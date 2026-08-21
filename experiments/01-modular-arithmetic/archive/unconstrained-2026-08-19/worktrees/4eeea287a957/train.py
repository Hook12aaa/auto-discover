import torch
import torch.nn as nn
import torch.nn.functional as F
import json
import time
import random
import math

PRIMES = [5, 7, 11, 13, 17, 19, 23, 29, 31]
PRIME_TO_IDX = {p: i for i, p in enumerate(PRIMES)}
MAX_P = max(PRIMES)
K = 16
SEED = 42
MAX_EPOCHS = 10000
EVAL_EVERY = 100
THRESHOLD_ACC = 0.99

DEVICE = torch.device("cpu")
DTYPE = torch.float64

OUT_DIR = "/Users/hook/Documents/coding/python/Personal_AI  Projects/auto_archicture_discovery/.auto-discover/worktrees/4eeea287a957"


def generate_data():
    train_a, train_b, train_target, train_prime_idx = [], [], [], []
    test_a, test_b, test_target, test_prime_idx = [], [], [], []

    for p in PRIMES:
        pairs = [(a, b, (a + b) % p) for a in range(p) for b in range(p)]
        rng = random.Random(42)
        rng.shuffle(pairs)
        split = len(pairs) // 2
        train_pairs = pairs[:split]
        test_pairs = pairs[split:]
        pidx = PRIME_TO_IDX[p]

        for a, b, t in train_pairs:
            train_a.append(a)
            train_b.append(b)
            train_target.append(t)
            train_prime_idx.append(pidx)

        for a, b, t in test_pairs:
            test_a.append(a)
            test_b.append(b)
            test_target.append(t)
            test_prime_idx.append(pidx)

    def to_tensor(*arrs):
        return tuple(torch.tensor(a, dtype=torch.long, device=DEVICE) for a in arrs)

    tr_a, tr_b, tr_t, tr_p = to_tensor(train_a, train_b, train_target, train_prime_idx)
    te_a, te_b, te_t, te_p = to_tensor(test_a, test_b, test_target, test_prime_idx)
    return (tr_a, tr_b, tr_t, tr_p), (te_a, te_b, te_t, te_p)


class HarmonicPhaseCorrelatorV2(nn.Module):
    def __init__(self):
        super().__init__()
        torch.manual_seed(SEED)
        self.freqs = nn.Parameter(torch.rand(len(PRIMES), K, dtype=DTYPE))
        self.amplitude_weights = nn.Parameter(torch.ones(K, dtype=DTYPE))

    def forward(self, a, b, prime_idx):
        freqs = self.freqs[prime_idx]

        a_f = a.to(DTYPE).unsqueeze(1)
        b_f = b.to(DTYPE).unsqueeze(1)

        two_pi = 2.0 * math.pi
        phase_a = two_pi * a_f * freqs
        phase_b = two_pi * b_f * freqs

        re_a = torch.cos(phase_a)
        im_a = torch.sin(phase_a)
        re_b = torch.cos(phase_b)
        im_b = torch.sin(phase_b)

        combined_re = re_a * re_b - im_a * im_b
        combined_im = re_a * im_b + im_a * re_b

        w = self.amplitude_weights.unsqueeze(0)
        combined_re = combined_re * w
        combined_im = combined_im * w

        candidates = torch.arange(MAX_P, dtype=DTYPE, device=freqs.device)
        freqs_expanded = freqs.unsqueeze(1)
        candidates_expanded = candidates.unsqueeze(0).unsqueeze(2)
        phase_c = two_pi * candidates_expanded * freqs_expanded

        cos_c = torch.cos(phase_c)
        sin_c = torch.sin(phase_c)

        scores = (combined_re.unsqueeze(1) * cos_c + combined_im.unsqueeze(1) * sin_c).sum(dim=2)

        primes_tensor = torch.tensor(PRIMES, device=scores.device, dtype=torch.long)
        prime_values = primes_tensor[prime_idx]
        mask = candidates.unsqueeze(0).long() >= prime_values.unsqueeze(1)
        scores = scores.masked_fill(mask, float('-inf'))

        return scores


def count_params(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def compute_grad_norm(model):
    total = 0.0
    for p in model.parameters():
        if p.grad is not None:
            total += p.grad.norm().item() ** 2
    return math.sqrt(total)


def evaluate_model(model, data):
    a, b, t, pidx = data
    with torch.no_grad():
        logits = model(a, b, pidx)
        preds = logits.argmax(dim=1)
        correct = (preds == t).float().mean().item()

    per_prime = {}
    for p in PRIMES:
        mask = pidx == PRIME_TO_IDX[p]
        if mask.any():
            p_preds = logits[mask].argmax(dim=1)
            p_correct = (p_preds == t[mask]).float().mean().item()
            per_prime[str(p)] = p_correct
    return correct, per_prime


def gradient_probe_lr(model, train_data):
    a, b, t, pidx = train_data

    candidates = [1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 5e-1]
    best_lr = 1e-3
    best_final_loss = float('inf')

    for lr_cand in candidates:
        probe_model = HarmonicPhaseCorrelatorV2.__new__(HarmonicPhaseCorrelatorV2)
        nn.Module.__init__(probe_model)
        probe_model.freqs = nn.Parameter(model.freqs.data.clone())
        probe_model.amplitude_weights = nn.Parameter(model.amplitude_weights.data.clone())
        opt = torch.optim.AdamW(probe_model.parameters(), lr=lr_cand, weight_decay=0.0)
        for _ in range(100):
            opt.zero_grad()
            logits = probe_model(a, b, pidx)
            loss = F.cross_entropy(logits, t)
            loss.backward()
            opt.step()
        final_loss = loss.item()
        if final_loss < best_final_loss:
            best_final_loss = final_loss
            best_lr = lr_cand

    model.zero_grad()
    logits = model(a, b, pidx)
    initial_loss = F.cross_entropy(logits, t).item()

    return best_lr, initial_loss


def main():
    torch.manual_seed(SEED)
    random.seed(SEED)

    print("Generating data...")
    train_data, test_data = generate_data()
    print(f"Train samples: {len(train_data[0])}, Test samples: {len(test_data[0])}")

    model = HarmonicPhaseCorrelatorV2().to(DEVICE)
    n_params = count_params(model)
    print(f"Total parameters: {n_params}")
    print(f"Frequency init: random uniform [0, 1] (NOT k/p)")
    print(f"Freq sample [prime=5]: {model.freqs.data[0, :4].tolist()}")

    print("Running gradient probe for learning rate...")
    lr, initial_loss = gradient_probe_lr(model, train_data)
    weight_decay = math.log(2) / (MAX_EPOCHS * lr)
    print(f"Selected LR: {lr:.6e}, Weight decay: {weight_decay:.6e}, Initial loss: {initial_loss:.4f}")

    torch.manual_seed(SEED)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    a_tr, b_tr, t_tr, p_tr = train_data
    history = []
    threshold_epoch = None
    threshold_wall = None
    start_time = time.time()

    init_test_acc, init_test_per_prime = evaluate_model(model, test_data)
    init_train_acc, _ = evaluate_model(model, train_data)
    print(f"Epoch     0 | loss {initial_loss:.4f} | train_acc {init_train_acc:.4f} | test_acc {init_test_acc:.4f}")

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(a_tr, b_tr, p_tr)
        loss = F.cross_entropy(logits, t_tr)
        loss.backward()
        grad_norm = compute_grad_norm(model)
        optimizer.step()

        if epoch % EVAL_EVERY == 0 or epoch == 1:
            model.eval()
            train_acc, train_per_prime = evaluate_model(model, train_data)
            test_acc, test_per_prime = evaluate_model(model, test_data)
            elapsed = time.time() - start_time

            record = {
                "epoch": epoch,
                "train_loss": loss.item(),
                "train_accuracy": train_acc,
                "test_accuracy": test_acc,
                "gradient_norm": grad_norm,
                "wall_clock_seconds": elapsed,
                "train_per_prime": train_per_prime,
                "test_per_prime": test_per_prime,
            }
            history.append(record)
            print(f"Epoch {epoch:5d} | loss {loss.item():.4f} | train_acc {train_acc:.4f} | test_acc {test_acc:.4f} | grad {grad_norm:.4e} | {elapsed:.1f}s")

            if test_acc >= THRESHOLD_ACC and threshold_epoch is None:
                threshold_epoch = epoch
                threshold_wall = elapsed
                print(f"*** 99% test accuracy reached at epoch {epoch} ({elapsed:.1f}s) ***")

            if train_acc >= 0.9999 and test_acc >= 0.9999:
                print(f"Perfect accuracy reached at epoch {epoch}, stopping early.")
                break

        wall_elapsed = time.time() - start_time
        if wall_elapsed > 120 * 60:
            print("Wall clock limit reached.")
            break

    total_time = time.time() - start_time
    model.eval()
    final_test_acc, final_per_prime = evaluate_model(model, test_data)
    final_train_acc, _ = evaluate_model(model, train_data)

    optimizer.zero_grad()
    logits = model(a_tr, b_tr, p_tr)
    final_loss = F.cross_entropy(logits, t_tr)
    final_loss.backward()
    final_grad_norms = []
    for p in model.parameters():
        if p.grad is not None:
            final_grad_norms.append(p.grad.norm().item())
    mean_grad_norm = sum(final_grad_norms) / len(final_grad_norms) if final_grad_norms else 0.0

    total_train_samples = len(a_tr)
    compute_to_threshold = None
    samples_to_threshold = None
    if threshold_epoch is not None:
        compute_to_threshold = total_train_samples * n_params * 6 * threshold_epoch
        samples_to_threshold = total_train_samples * threshold_epoch

    param_efficiency = n_params / (final_test_acc * 100) if final_test_acc > 0 else float('inf')

    final_metrics = {
        "experiment_hash": "4eeea287a957",
        "architecture_name": "harmonic_phase_correlator_v2",
        "refinement_of": "2ddafd9fcd03",
        "refinement_type": "random_init_to_test_learning",
        "seed": SEED,
        "total_parameters": n_params,
        "learning_rate": lr,
        "weight_decay": weight_decay,
        "epochs_trained": history[-1]["epoch"] if history else 0,
        "wall_clock_seconds": total_time,
        "pre_registered_metrics": {
            "test_accuracy_modular_addition": final_test_acc,
            "compute_to_threshold_ratio": compute_to_threshold,
            "samples_to_threshold_accuracy": samples_to_threshold,
            "gradient_health_mean_norm": mean_grad_norm,
            "param_efficiency_params_per_accuracy_point": param_efficiency,
        },
        "threshold_epoch": threshold_epoch,
        "threshold_wall_seconds": threshold_wall,
        "final_train_accuracy": final_train_acc,
        "final_train_loss": final_loss.item(),
        "per_prime_test_accuracy": final_per_prime,
        "initial_loss": initial_loss,
        "initial_test_accuracy": init_test_acc,
        "frequency_init": "random_uniform_0_to_1",
        "training_budget_used": {
            "epochs": history[-1]["epoch"] if history else 0,
            "max_epochs": MAX_EPOCHS,
            "wall_clock_minutes": total_time / 60,
            "epochs_used_fraction": (history[-1]["epoch"] if history else 0) / MAX_EPOCHS,
        },
    }

    with open(f"{OUT_DIR}/training_metrics.json", "w") as f:
        json.dump(history, f, indent=2)

    with open(f"{OUT_DIR}/final_metrics.json", "w") as f:
        json.dump(final_metrics, f, indent=2)

    print(f"\n=== FINAL RESULTS ===")
    print(f"Test accuracy: {final_test_acc:.6f}")
    print(f"Train accuracy: {final_train_acc:.6f}")
    print(f"Total params: {n_params}")
    print(f"Epochs trained: {history[-1]['epoch'] if history else 0}")
    print(f"Wall clock: {total_time / 60:.2f} minutes")
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
