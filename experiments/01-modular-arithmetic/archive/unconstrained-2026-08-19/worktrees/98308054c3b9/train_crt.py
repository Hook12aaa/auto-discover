import torch
import torch.nn as nn
import torch.nn.functional as F
import json
import time
import random
import math

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
SEED = 42
PRIMES = [5, 7, 11, 13, 17, 19, 23, 29, 31]
PRIME_TO_CHANNEL = {p: i for i, p in enumerate(PRIMES)}
NUM_CHANNELS = len(PRIMES)
EMBED_DIM = 18
CHANNEL_DIM = 2
MAX_EPOCHS = 10000
EVAL_EVERY = 100
WORKTREE = "/Users/hook/Documents/coding/python/Personal_AI  Projects/auto_archicture_discovery/.auto-discover/worktrees/98308054c3b9"

torch.manual_seed(SEED)
random.seed(SEED)


def generate_grouped_data():
    train_groups = {}
    test_groups = {}

    for p in PRIMES:
        pairs = [(a, b) for a in range(p) for b in range(p)]
        rng = random.Random(SEED)
        rng.shuffle(pairs)
        split = len(pairs) // 2
        train_pairs = pairs[:split]
        test_pairs = pairs[split:]

        train_a = torch.tensor([x[0] for x in train_pairs], device=DEVICE)
        train_b = torch.tensor([x[1] for x in train_pairs], device=DEVICE)
        train_t = torch.tensor([(x[0] + x[1]) % p for x in train_pairs], device=DEVICE)
        train_groups[p] = (train_a, train_b, train_t)

        test_a = torch.tensor([x[0] for x in test_pairs], device=DEVICE)
        test_b = torch.tensor([x[1] for x in test_pairs], device=DEVICE)
        test_t = torch.tensor([(x[0] + x[1]) % p for x in test_pairs], device=DEVICE)
        test_groups[p] = (test_a, test_b, test_t)

    return train_groups, test_groups


class CRTChannelDecomposer(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(31, EMBED_DIM)
        self.Q_raw = nn.Parameter(torch.randn(EMBED_DIM, EMBED_DIM))

        self.w_fold = nn.ParameterList([nn.Parameter(torch.randn(CHANNEL_DIM)) for _ in range(NUM_CHANNELS)])
        self.bias_fold = nn.ParameterList([nn.Parameter(torch.zeros(1)) for _ in range(NUM_CHANNELS)])
        self.scale_fold = nn.ParameterList([nn.Parameter(torch.ones(1)) for _ in range(NUM_CHANNELS)])

        self.readout_W = nn.ParameterList([nn.Parameter(torch.randn(p, CHANNEL_DIM) * 0.1) for p in PRIMES])
        self.readout_b = nn.ParameterList([nn.Parameter(torch.zeros(p)) for p in PRIMES])

    def _get_orthogonal_Q(self):
        Q, _ = torch.linalg.qr(self.Q_raw.cpu())
        return Q.to(self.Q_raw.device)

    def forward_channel(self, a_idx, b_idx, channel_idx):
        Q = self._get_orthogonal_Q()
        embed_a = self.embedding(a_idx)
        embed_b = self.embedding(b_idx)

        i = channel_idx
        P_i = Q[:, 2 * i : 2 * i + 2].T

        ch_a = (embed_a @ P_i.T)
        ch_b = (embed_b @ P_i.T)

        s_i = ch_a + ch_b

        gate_val = (s_i * self.w_fold[i]).sum(dim=-1) + self.bias_fold[i]
        folded = s_i - self.scale_fold[i] * F.relu(gate_val).unsqueeze(-1)

        logits = folded @ self.readout_W[i].T + self.readout_b[i]
        return logits

    def count_params(self):
        return sum(p.numel() for p in self.parameters())


def compute_loss_and_acc_grouped(model, groups):
    total_loss = torch.tensor(0.0, device=DEVICE)
    total_correct = 0
    total_samples = 0

    for p in PRIMES:
        a, b, t = groups[p]
        channel_idx = PRIME_TO_CHANNEL[p]
        logits = model.forward_channel(a, b, channel_idx)
        loss = F.cross_entropy(logits, t, reduction='sum')
        total_loss = total_loss + loss
        total_correct += (logits.argmax(dim=-1) == t).sum().item()
        total_samples += len(a)

    return total_loss / total_samples, total_correct / total_samples


def gradient_probe(model, train_groups):
    model.zero_grad()
    sub_groups = {}
    for p in PRIMES:
        a, b, t = train_groups[p]
        n = min(8, len(a))
        sub_groups[p] = (a[:n], b[:n], t[:n])

    loss, _ = compute_loss_and_acc_grouped(model, sub_groups)
    loss.backward()

    grad_norms = []
    for param in model.parameters():
        if param.grad is not None:
            grad_norms.append(param.grad.norm().item())
    median_grad = sorted(grad_norms)[len(grad_norms) // 2]
    lr = min(0.1, 1.0 / (median_grad + 1e-8))
    lr = max(1e-4, lr)
    return lr


def per_prime_accuracy(model, groups):
    results = {}
    for p in PRIMES:
        a, b, t = groups[p]
        channel_idx = PRIME_TO_CHANNEL[p]
        with torch.no_grad():
            logits = model.forward_channel(a, b, channel_idx)
        acc = (logits.argmax(dim=-1) == t).float().mean().item()
        results[str(p)] = round(acc, 6)
    return results


def train():
    train_groups, test_groups = generate_grouped_data()
    train_count = sum(len(v[0]) for v in train_groups.values())
    test_count = sum(len(v[0]) for v in test_groups.values())
    print(f"Train samples: {train_count}, Test samples: {test_count}")

    model = CRTChannelDecomposer().to(DEVICE)
    num_params = model.count_params()
    print(f"Model parameters: {num_params}")

    lr = gradient_probe(model, train_groups)
    print(f"Initial LR from gradient probe: {lr:.6f}")
    weight_decay = math.log(2) / (MAX_EPOCHS * lr)
    print(f"Weight decay: {weight_decay:.8f}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    training_metrics = []
    best_test_acc = 0.0
    start_time = time.time()

    for epoch in range(1, MAX_EPOCHS + 1):
        elapsed = (time.time() - start_time) / 60
        if elapsed > 120:
            print(f"Wall clock limit reached at epoch {epoch}")
            break

        model.train()
        optimizer.zero_grad()
        train_loss, train_acc = compute_loss_and_acc_grouped(model, train_groups)
        train_loss.backward()
        optimizer.step()

        if epoch % EVAL_EVERY == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                test_loss, test_acc = compute_loss_and_acc_grouped(model, test_groups)

            grad_norms = []
            for param in model.parameters():
                if param.grad is not None:
                    grad_norms.append(param.grad.norm().item())
            mean_grad_norm = sum(grad_norms) / len(grad_norms) if grad_norms else 0.0

            record = {
                "epoch": epoch,
                "train_loss": round(train_loss.item(), 6),
                "train_accuracy": round(train_acc, 6),
                "test_loss": round(test_loss.item(), 6),
                "test_accuracy": round(test_acc, 6),
                "gradient_mean_norm": round(mean_grad_norm, 6),
                "wall_clock_minutes": round(elapsed, 2),
            }
            training_metrics.append(record)
            best_test_acc = max(best_test_acc, test_acc)

            print(
                f"Epoch {epoch:5d} | train_loss={train_loss.item():.4f} train_acc={train_acc:.4f} | "
                f"test_loss={test_loss.item():.4f} test_acc={test_acc:.4f} | grad_norm={mean_grad_norm:.4f} | {elapsed:.1f}m"
            )

    total_time = (time.time() - start_time) / 60
    model.eval()
    with torch.no_grad():
        final_test_loss, final_test_acc = compute_loss_and_acc_grouped(model, test_groups)
        final_train_loss, final_train_acc = compute_loss_and_acc_grouped(model, train_groups)
        pp_acc = per_prime_accuracy(model, test_groups)

    grad_norms = []
    for param in model.parameters():
        if param.grad is not None:
            grad_norms.append(param.grad.norm().item())
    final_mean_grad = sum(grad_norms) / len(grad_norms) if grad_norms else 0.0

    threshold_epoch = None
    for rec in training_metrics:
        if rec["test_accuracy"] >= 0.90:
            threshold_epoch = rec["epoch"]
            break

    compute_ratio = threshold_epoch / MAX_EPOCHS if threshold_epoch else None
    samples_to_threshold = threshold_epoch * train_count if threshold_epoch else None
    param_efficiency = num_params / (final_test_acc * 100) if final_test_acc > 0 else None

    final_metrics = {
        "experiment_hash": "98308054c3b9",
        "genome_spec": "crt_channel_decomposer",
        "seed": SEED,
        "total_parameters": num_params,
        "epochs_trained": epoch,
        "wall_clock_minutes": round(total_time, 2),
        "test_accuracy_modular_addition": round(final_test_acc, 6),
        "train_accuracy": round(final_train_acc, 6),
        "train_loss": round(final_train_loss.item(), 6),
        "test_loss": round(final_test_loss.item(), 6),
        "compute_to_threshold_ratio": round(compute_ratio, 6) if compute_ratio else None,
        "samples_to_threshold_accuracy": samples_to_threshold,
        "gradient_health_mean_norm": round(final_mean_grad, 6),
        "param_efficiency_params_per_accuracy_point": round(param_efficiency, 4) if param_efficiency else None,
        "per_prime_test_accuracy": pp_acc,
        "learning_rate": lr,
        "weight_decay": weight_decay,
        "device": str(DEVICE),
    }

    with open(f"{WORKTREE}/training_metrics.json", "w") as f:
        json.dump(training_metrics, f, indent=2)

    with open(f"{WORKTREE}/final_metrics.json", "w") as f:
        json.dump(final_metrics, f, indent=2)

    print(f"\nFinal test accuracy: {final_test_acc:.6f}")
    print(f"Per-prime accuracy: {pp_acc}")
    print(f"Parameters: {num_params}")
    print(f"Training time: {total_time:.2f} minutes")

    concerns = []
    if final_test_acc < 0.15:
        concerns.append(f"Test accuracy {final_test_acc:.4f} is near random baseline")
    if final_mean_grad < 1e-7:
        concerns.append("Gradient norms near zero — possible vanishing gradients")
    if final_train_acc > 0.99 and final_test_acc < 0.5:
        concerns.append("Large train/test gap — overfitting")

    if concerns:
        print(f"\nConcerns: {'; '.join(concerns)}")
        print("VERDICT: DONE_WITH_CONCERNS")
    else:
        print("VERDICT: DONE")


if __name__ == "__main__":
    train()
