import torch
import torch.nn as nn
import torch.nn.functional as F
import json
import time
import random
import math

PRIMES = [5, 7, 11, 13, 17, 19, 23, 29, 31]
PRIME_TO_IDX = {p: i for i, p in enumerate(PRIMES)}
SEED = 42
MAX_EPOCHS = 10000
MAX_WALL_MINUTES = 120
DEVICE = torch.device("mps")
WORKTREE = "/Users/hook/Documents/coding/python/Personal_AI  Projects/auto_archicture_discovery/.auto-discover/worktrees/09810afd22c2"


class CayleyAlgebraCompositor(nn.Module):
    def __init__(self):
        super().__init__()
        self.element_state_embed = nn.Embedding(31, 2)
        self.action_orbit_embed = nn.Embedding(31, 2)
        self.readout_heads = nn.ModuleDict()
        for p in PRIMES:
            self.readout_heads[str(p)] = nn.Linear(2, p)

    def forward(self, a, b, p_idx):
        s_a = self.element_state_embed(a)
        g_b = self.action_orbit_embed(b)
        z = s_a * g_b
        all_logits = []
        for i, p in enumerate(PRIMES):
            logits_p = self.readout_heads[str(p)](z)
            all_logits.append((i, p, logits_p))
        return all_logits, z

    def forward_single_prime(self, a, b, prime):
        s_a = self.element_state_embed(a)
        g_b = self.action_orbit_embed(b)
        z = s_a * g_b
        return self.readout_heads[str(prime)](z)


def build_dataset():
    rng = random.Random(SEED)
    train_data = []
    test_data = []

    for p in PRIMES:
        pairs = [(a, b) for a in range(p) for b in range(p)]
        rng.shuffle(pairs)
        split = len(pairs) // 2
        train_pairs = pairs[:split]
        test_pairs = pairs[split:]

        for a, b in train_pairs:
            target = (a + b) % p
            train_data.append((a, b, p, target))
        for a, b in test_pairs:
            target = (a + b) % p
            test_data.append((a, b, p, target))

    return train_data, test_data


def data_to_tensors(data, device):
    a_list = [d[0] for d in data]
    b_list = [d[1] for d in data]
    p_list = [d[2] for d in data]
    t_list = [d[3] for d in data]
    return (
        torch.tensor(a_list, dtype=torch.long, device=device),
        torch.tensor(b_list, dtype=torch.long, device=device),
        torch.tensor(p_list, dtype=torch.long, device=device),
        torch.tensor(t_list, dtype=torch.long, device=device),
    )


def compute_loss(model, a, b, primes, targets):
    total_loss = torch.tensor(0.0, device=a.device)
    count = 0
    for p in PRIMES:
        mask = primes == p
        if not mask.any():
            continue
        a_p = a[mask]
        b_p = b[mask]
        t_p = targets[mask]
        logits = model.forward_single_prime(a_p, b_p, p)
        loss = F.cross_entropy(logits, t_p, reduction='sum')
        total_loss = total_loss + loss
        count += mask.sum().item()
    return total_loss / count


def compute_accuracy(model, a, b, primes, targets):
    correct = 0
    total = 0
    per_prime = {}
    with torch.no_grad():
        for p in PRIMES:
            mask = primes == p
            if not mask.any():
                per_prime[str(p)] = 0.0
                continue
            a_p = a[mask]
            b_p = b[mask]
            t_p = targets[mask]
            logits = model.forward_single_prime(a_p, b_p, p)
            preds = logits.argmax(dim=-1)
            c = (preds == t_p).sum().item()
            n = t_p.shape[0]
            correct += c
            total += n
            per_prime[str(p)] = c / n
    return correct / total if total > 0 else 0.0, per_prime


def gradient_probe_lr(model, a, b, primes, targets):
    model.zero_grad()
    loss = compute_loss(model, a, b, primes, targets)
    loss.backward()
    grad_norm_sq = 0.0
    for param in model.parameters():
        if param.grad is not None:
            grad_norm_sq += param.grad.data.pow(2).sum().item()
    grad_norm = math.sqrt(grad_norm_sq)
    lr = 0.01 * loss.item() / (grad_norm ** 2) if grad_norm > 0 else 1e-3
    lr = max(min(lr, 1.0), 1e-5)
    model.zero_grad()
    return lr, loss.item(), grad_norm


def main():
    torch.manual_seed(SEED)
    random.seed(SEED)

    train_data, test_data = build_dataset()
    print(f"Train samples: {len(train_data)}, Test samples: {len(test_data)}")

    a_train, b_train, p_train, t_train = data_to_tensors(train_data, DEVICE)
    a_test, b_test, p_test, t_test = data_to_tensors(test_data, DEVICE)

    model = CayleyAlgebraCompositor().to(DEVICE)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params}")

    lr, initial_loss, initial_grad_norm = gradient_probe_lr(model, a_train, b_train, p_train, t_train)
    print(f"Gradient probe: lr={lr:.6f}, initial_loss={initial_loss:.4f}, grad_norm={initial_grad_norm:.4f}")

    weight_decay = math.log(2) / (MAX_EPOCHS * lr)
    print(f"Weight decay: {weight_decay:.8f}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    history = []
    best_test_acc = 0.0
    threshold_epoch = None
    start_time = time.time()

    for epoch in range(1, MAX_EPOCHS + 1):
        elapsed_minutes = (time.time() - start_time) / 60.0
        if elapsed_minutes > MAX_WALL_MINUTES:
            print(f"Wall clock limit reached at epoch {epoch}")
            break

        model.train()
        optimizer.zero_grad()
        loss = compute_loss(model, a_train, b_train, p_train, t_train)
        loss.backward()
        optimizer.step()

        if epoch % 100 == 0 or epoch == 1:
            model.eval()
            train_loss = loss.item()
            train_acc, train_per_prime = compute_accuracy(model, a_train, b_train, p_train, t_train)
            test_acc, test_per_prime = compute_accuracy(model, a_test, b_test, p_test, t_test)
            test_loss = compute_loss(model, a_test, b_test, p_test, t_test).item()

            grad_norm = 0.0
            for param in model.parameters():
                if param.grad is not None:
                    grad_norm += param.grad.data.pow(2).sum().item()
            grad_norm = math.sqrt(grad_norm)

            record = {
                "epoch": epoch,
                "train_loss": train_loss,
                "test_loss": test_loss,
                "train_accuracy": train_acc,
                "test_accuracy": test_acc,
                "train_per_prime": train_per_prime,
                "test_per_prime": test_per_prime,
                "grad_norm": grad_norm,
                "elapsed_minutes": elapsed_minutes,
            }
            history.append(record)

            if test_acc > best_test_acc:
                best_test_acc = test_acc

            if test_acc >= 0.99 and threshold_epoch is None:
                threshold_epoch = epoch
                print(f"  >> 99% test accuracy reached at epoch {epoch}")

            if epoch % 500 == 0 or epoch == 1:
                print(f"Epoch {epoch}: train_loss={train_loss:.4f} test_loss={test_loss:.4f} "
                      f"train_acc={train_acc:.4f} test_acc={test_acc:.4f} grad_norm={grad_norm:.4f}")

            if train_acc >= 0.9999 and test_acc >= 0.9999:
                print(f"Perfect accuracy reached at epoch {epoch}, stopping early.")
                break

    elapsed_total = (time.time() - start_time) / 60.0
    model.eval()
    final_test_acc, final_per_prime = compute_accuracy(model, a_test, b_test, p_test, t_test)
    final_train_acc, _ = compute_accuracy(model, a_train, b_train, p_train, t_train)
    final_test_loss = compute_loss(model, a_test, b_test, p_test, t_test).item()
    final_train_loss = compute_loss(model, a_train, b_train, p_train, t_train).item()

    final_grad_norms = []
    for param in model.parameters():
        if param.grad is not None:
            final_grad_norms.append(param.grad.data.norm().item())
    mean_grad_norm = sum(final_grad_norms) / len(final_grad_norms) if final_grad_norms else 0.0

    param_efficiency = total_params / max(final_test_acc * 100, 1e-6)

    compute_ratio = None
    if threshold_epoch is not None:
        compute_ratio = threshold_epoch / MAX_EPOCHS

    samples_to_threshold = None
    if threshold_epoch is not None:
        samples_to_threshold = threshold_epoch * len(train_data)

    final_metrics = {
        "experiment_hash": "09810afd22c2",
        "spec_name": "cayley_algebra_compositor",
        "seed": SEED,
        "total_params": total_params,
        "epochs_trained": history[-1]["epoch"] if history else 0,
        "wall_clock_minutes": elapsed_total,
        "pre_registered_metrics": {
            "test_accuracy_modular_addition": final_test_acc,
            "compute_to_threshold_ratio": compute_ratio,
            "samples_to_threshold_accuracy": samples_to_threshold,
            "gradient_health_mean_norm": mean_grad_norm,
            "param_efficiency_params_per_accuracy_point": param_efficiency,
        },
        "additional_metrics": {
            "train_accuracy": final_train_acc,
            "train_loss": final_train_loss,
            "test_loss": final_test_loss,
            "initial_loss": initial_loss,
            "initial_grad_norm": initial_grad_norm,
            "learning_rate": lr,
            "weight_decay": weight_decay,
            "threshold_epoch": threshold_epoch,
            "best_test_accuracy": best_test_acc,
            "per_prime_test_accuracy": final_per_prime,
        },
        "budget": {
            "max_epochs": MAX_EPOCHS,
            "max_wall_clock_minutes": MAX_WALL_MINUTES,
            "epochs_used_fraction": (history[-1]["epoch"] if history else 0) / MAX_EPOCHS,
            "wall_clock_used_fraction": elapsed_total / MAX_WALL_MINUTES,
        },
    }

    with open(f"{WORKTREE}/training_metrics.json", "w") as f:
        json.dump(history, f, indent=2)

    with open(f"{WORKTREE}/final_metrics.json", "w") as f:
        json.dump(final_metrics, f, indent=2)

    print(f"\n=== FINAL RESULTS ===")
    print(f"Test accuracy: {final_test_acc:.6f}")
    print(f"Train accuracy: {final_train_acc:.6f}")
    print(f"Total params: {total_params}")
    print(f"Epochs trained: {history[-1]['epoch'] if history else 0}")
    print(f"Wall clock: {elapsed_total:.2f} minutes")
    print(f"Threshold epoch (99%): {threshold_epoch}")
    print(f"Per-prime test accuracy: {final_per_prime}")

    concerns = []
    if final_test_acc < 0.5:
        concerns.append(f"Low test accuracy: {final_test_acc:.4f}")
    if any(v < 0.1 for v in final_per_prime.values()):
        failing_primes = [p for p, v in final_per_prime.items() if v < 0.1]
        concerns.append(f"Near-zero accuracy on primes: {failing_primes}")

    if concerns:
        print(f"\nConcerns: {concerns}")
        print("VERDICT: DONE_WITH_CONCERNS")
    else:
        print("VERDICT: DONE")


if __name__ == "__main__":
    main()
