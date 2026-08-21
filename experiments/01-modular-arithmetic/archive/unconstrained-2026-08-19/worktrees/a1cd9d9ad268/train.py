import torch
import torch.nn as nn
import torch.optim as optim
import json
import time
import random
import math

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
SEED = 42
PRIMES = [5, 7, 11, 13, 17, 19, 23, 29, 31]
PRIME_TO_IDX = {p: i for i, p in enumerate(PRIMES)}
MAX_EPOCHS = 10000
EVAL_EVERY = 100


def set_seed(seed):
    torch.manual_seed(seed)
    random.seed(seed)


def build_dataset(primes, seed):
    rng = random.Random(seed)
    train_inputs, train_targets = [], []
    test_inputs, test_targets = [], []
    train_per_prime, test_per_prime = {}, {}

    for p in primes:
        pidx = PRIME_TO_IDX[p]
        pairs = [(a, b, pidx, (a + b) % p) for a in range(p) for b in range(p)]
        rng.shuffle(pairs)
        split = len(pairs) // 2
        train_split = pairs[:split]
        test_split = pairs[split:]

        train_per_prime[p] = len(train_split)
        test_per_prime[p] = len(test_split)

        for a, b, pi, t in train_split:
            train_inputs.append((a, b, pi))
            train_targets.append(t)
        for a, b, pi, t in test_split:
            test_inputs.append((a, b, pi))
            test_targets.append(t)

    train_a = torch.tensor([x[0] for x in train_inputs], dtype=torch.long, device=DEVICE)
    train_b = torch.tensor([x[1] for x in train_inputs], dtype=torch.long, device=DEVICE)
    train_p = torch.tensor([x[2] for x in train_inputs], dtype=torch.long, device=DEVICE)
    train_t = torch.tensor(train_targets, dtype=torch.long, device=DEVICE)

    test_a = torch.tensor([x[0] for x in test_inputs], dtype=torch.long, device=DEVICE)
    test_b = torch.tensor([x[1] for x in test_inputs], dtype=torch.long, device=DEVICE)
    test_p = torch.tensor([x[2] for x in test_inputs], dtype=torch.long, device=DEVICE)
    test_t = torch.tensor(test_targets, dtype=torch.long, device=DEVICE)

    return (train_a, train_b, train_p, train_t,
            test_a, test_b, test_p, test_t,
            train_per_prime, test_per_prime)


class PoincareFoldCompositor(nn.Module):
    def __init__(self, max_val=31, dim=32, n_primes=9, n_classes=31):
        super().__init__()
        self.E_a = nn.Embedding(max_val, dim)
        self.E_b = nn.Embedding(max_val, dim)
        self.E_p = nn.Embedding(n_primes, dim)

        self.w_detect = nn.Parameter(torch.randn(dim))
        self.b_detect = nn.Parameter(torch.zeros(1))

        self.W_out = nn.Linear(dim, n_classes)

    def forward(self, a, b, p_idx):
        e_a = self.E_a(a)
        e_b = self.E_b(b)
        beta = self.E_p(p_idx)

        s_free = e_a + e_b
        crossing = torch.sum(self.w_detect * (s_free - beta), dim=-1, keepdim=True) + self.b_detect
        gate = torch.sigmoid(crossing)
        s_folded = s_free - gate * beta

        logits = self.W_out(s_folded)
        return logits


def count_params(model):
    return sum(p.numel() for p in model.parameters())


def derive_lr(model, train_a, train_b, train_p, train_t, base_lr=0.01, n_candidates=5, validation_steps=100):
    logits = model(train_a, train_b, train_p)
    initial_loss = nn.functional.cross_entropy(logits, train_t).item()

    model.zero_grad()
    loss = nn.functional.cross_entropy(model(train_a, train_b, train_p), train_t)
    loss.backward()

    grad_norm_sq = sum((p.grad ** 2).sum().item() for p in model.parameters() if p.grad is not None)
    grad_norm = math.sqrt(grad_norm_sq)

    proposed_lr = base_lr * initial_loss / (grad_norm ** 2)

    candidates = [proposed_lr * (2 ** i) for i in range(-2, n_candidates - 2)]
    best_lr = proposed_lr
    best_final_loss = float('inf')

    for clr in candidates:
        test_model = PoincareFoldCompositor().to(DEVICE)
        test_model.load_state_dict(model.state_dict())
        test_opt = optim.AdamW(test_model.parameters(), lr=clr, weight_decay=0.0)

        for _ in range(validation_steps):
            test_opt.zero_grad()
            out = test_model(train_a, train_b, train_p)
            l = nn.functional.cross_entropy(out, train_t)
            l.backward()
            test_opt.step()

        final_l = nn.functional.cross_entropy(test_model(train_a, train_b, train_p), train_t).item()
        if final_l < best_final_loss:
            best_final_loss = final_l
            best_lr = clr

    return best_lr, initial_loss, grad_norm


def evaluate_per_prime(model, test_a, test_b, test_p, test_t, primes):
    model.eval()
    with torch.no_grad():
        logits = model(test_a, test_b, test_p)
        preds = logits.argmax(dim=-1)

    results = {}
    for p in primes:
        pidx = PRIME_TO_IDX[p]
        mask = test_p == pidx
        correct = (preds[mask] == test_t[mask]).sum().item()
        total = mask.sum().item()
        results[str(p)] = correct / total if total > 0 else 0.0

    overall = (preds == test_t).sum().item() / len(test_t)
    return overall, results


def train():
    set_seed(SEED)

    (train_a, train_b, train_p, train_t,
     test_a, test_b, test_p, test_t,
     train_per_prime, test_per_prime) = build_dataset(PRIMES, SEED)

    print(f"Train samples: {len(train_t)}, Test samples: {len(test_t)}")
    print(f"Device: {DEVICE}")

    model = PoincareFoldCompositor().to(DEVICE)
    n_params = count_params(model)
    print(f"Parameters: {n_params}")

    lr, initial_loss, grad_norm = derive_lr(model, train_a, train_b, train_p, train_t)
    print(f"Initial loss: {initial_loss:.4f}, Grad norm: {grad_norm:.4f}, Derived LR: {lr:.6f}")

    set_seed(SEED)
    model = PoincareFoldCompositor().to(DEVICE)

    weight_decay = math.log(2) / (MAX_EPOCHS * lr)
    print(f"Weight decay: {weight_decay:.6f}")

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    history = []
    threshold_epoch = None
    start_time = time.time()

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(train_a, train_b, train_p)
        loss = nn.functional.cross_entropy(logits, train_t)
        loss.backward()

        grad_norms = []
        for p in model.parameters():
            if p.grad is not None:
                grad_norms.append(p.grad.norm().item())

        optimizer.step()

        if epoch % EVAL_EVERY == 0 or epoch == 1:
            test_acc, per_prime_acc = evaluate_per_prime(model, test_a, test_b, test_p, test_t, PRIMES)
            train_acc_val = (logits.argmax(dim=-1) == train_t).float().mean().item()

            entry = {
                "epoch": epoch,
                "train_loss": loss.item(),
                "train_accuracy": train_acc_val,
                "test_accuracy": test_acc,
                "per_prime_test_accuracy": per_prime_acc,
                "gradient_mean_norm": sum(grad_norms) / len(grad_norms) if grad_norms else 0.0,
                "wall_clock_seconds": time.time() - start_time,
            }
            history.append(entry)

            if test_acc >= 0.99 and threshold_epoch is None:
                threshold_epoch = epoch
                print(f"  *** 99% test accuracy reached at epoch {epoch} ***")

            if epoch % 500 == 0 or epoch == 1:
                print(f"Epoch {epoch}: loss={loss.item():.4f}, train_acc={train_acc_val:.4f}, test_acc={test_acc:.4f}")

        elapsed = time.time() - start_time
        if elapsed > 120 * 60:
            print(f"Wall clock limit reached at epoch {epoch}")
            break

    total_time = time.time() - start_time
    final_test_acc, final_per_prime = evaluate_per_prime(model, test_a, test_b, test_p, test_t, PRIMES)
    final_train_logits = model(train_a, train_b, train_p)
    final_train_loss = nn.functional.cross_entropy(final_train_logits, train_t).item()
    final_train_acc = (final_train_logits.argmax(dim=-1) == train_t).float().mean().item()

    grad_norms_final = []
    for p in model.parameters():
        if p.grad is not None:
            grad_norms_final.append(p.grad.norm().item())
    mean_grad_norm = sum(grad_norms_final) / len(grad_norms_final) if grad_norms_final else 0.0

    compute_ratio = threshold_epoch / MAX_EPOCHS if threshold_epoch else 1.0
    samples_to_threshold = threshold_epoch * len(train_t) if threshold_epoch else MAX_EPOCHS * len(train_t)
    param_efficiency = n_params / (final_test_acc * 100) if final_test_acc > 0 else float('inf')

    final_metrics = {
        "experiment_hash": "a1cd9d9ad268",
        "genome_spec": "poincare_fold_compositor",
        "seed": SEED,
        "test_accuracy_modular_addition": final_test_acc,
        "train_accuracy": final_train_acc,
        "train_loss": final_train_loss,
        "compute_to_threshold_ratio": compute_ratio,
        "samples_to_threshold_accuracy": samples_to_threshold,
        "gradient_health_mean_norm": mean_grad_norm,
        "param_efficiency_params_per_accuracy_point": param_efficiency,
        "per_prime_test_accuracy": final_per_prime,
        "total_parameters": n_params,
        "epochs_trained": epoch,
        "threshold_epoch": threshold_epoch,
        "wall_clock_seconds": total_time,
        "learning_rate": lr,
        "weight_decay": weight_decay,
        "device": str(DEVICE),
        "budget_used": {
            "epochs": epoch,
            "wall_clock_minutes": total_time / 60,
        },
    }

    worktree = "/Users/hook/Documents/coding/python/Personal_AI  Projects/auto_archicture_discovery/.auto-discover/worktrees/a1cd9d9ad268"

    with open(f"{worktree}/training_metrics.json", "w") as f:
        json.dump(history, f, indent=2)

    with open(f"{worktree}/final_metrics.json", "w") as f:
        json.dump(final_metrics, f, indent=2)

    print(f"\nFinal Results:")
    print(f"  Test accuracy: {final_test_acc:.4f}")
    print(f"  Train accuracy: {final_train_acc:.4f}")
    print(f"  Epochs: {epoch}")
    print(f"  Wall clock: {total_time:.1f}s")
    print(f"  Threshold epoch (99%): {threshold_epoch}")
    print(f"  Parameters: {n_params}")
    print(f"  Per-prime accuracy: {final_per_prime}")

    if final_test_acc >= 0.99:
        print("\nVERDICT: DONE")
    elif final_test_acc >= 0.50:
        print("\nVERDICT: DONE_WITH_CONCERNS")
        print(f"  Concern: test accuracy {final_test_acc:.4f} below 99% threshold")
    else:
        print("\nVERDICT: DONE_WITH_CONCERNS")
        print(f"  Concern: test accuracy {final_test_acc:.4f} significantly below target")


if __name__ == "__main__":
    train()
