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
MAX_EPOCHS = 10000
EVAL_EVERY = 100
THRESHOLD_ACC = 0.99

DEVICE = torch.device("cpu")
DTYPE = torch.float64

OUT_DIR = "/Users/hook/Documents/coding/python/Personal_AI  Projects/auto_archicture_discovery/.auto-discover/worktrees/4eeea287a957"

SEEDS = [42, 137, 256, 512, 1024]
VARIANCE_TOLERANCE = 0.15


def generate_data(seed):
    train_a, train_b, train_target, train_prime_idx = [], [], [], []
    test_a, test_b, test_target, test_prime_idx = [], [], [], []

    for p in PRIMES:
        pairs = [(a, b, (a + b) % p) for a in range(p) for b in range(p)]
        rng = random.Random(seed)
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
    def __init__(self, seed):
        super().__init__()
        torch.manual_seed(seed)
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


def evaluate_model(model, data):
    a, b, t, pidx = data
    with torch.no_grad():
        logits = model(a, b, pidx)
        preds = logits.argmax(dim=1)
        correct = (preds == t).float().mean().item()
    return correct


def gradient_probe_lr(model, train_data, seed):
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


def train_with_seed(seed):
    print(f"\n{'='*60}")
    print(f"TRAINING WITH SEED {seed}")
    print(f"{'='*60}")

    torch.manual_seed(seed)
    random.seed(seed)

    train_data, test_data = generate_data(seed)
    print(f"Train samples: {len(train_data[0])}, Test samples: {len(test_data[0])}")

    model = HarmonicPhaseCorrelatorV2(seed).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Parameters: {n_params}")

    lr, initial_loss = gradient_probe_lr(model, train_data, seed)
    weight_decay = math.log(2) / (MAX_EPOCHS * lr)
    print(f"LR: {lr:.6e}, WD: {weight_decay:.6e}, Initial loss: {initial_loss:.4f}")

    torch.manual_seed(seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    a_tr, b_tr, t_tr, p_tr = train_data
    threshold_epoch = None
    start_time = time.time()

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(a_tr, b_tr, p_tr)
        loss = F.cross_entropy(logits, t_tr)
        loss.backward()
        optimizer.step()

        if epoch % EVAL_EVERY == 0 or epoch == 1:
            model.eval()
            train_acc = evaluate_model(model, train_data)
            test_acc = evaluate_model(model, test_data)
            elapsed = time.time() - start_time
            print(f"  Epoch {epoch:5d} | loss {loss.item():.4f} | train {train_acc:.4f} | test {test_acc:.4f} | {elapsed:.1f}s")

            if test_acc >= THRESHOLD_ACC and threshold_epoch is None:
                threshold_epoch = epoch
                print(f"  *** 99% test accuracy at epoch {epoch} ***")

            if train_acc >= 0.9999 and test_acc >= 0.9999:
                print(f"  Perfect accuracy at epoch {epoch}, stopping.")
                break

        if time.time() - start_time > 60 * 60:
            print("  Wall clock limit (60min) reached.")
            break

    model.eval()
    final_test_acc = evaluate_model(model, test_data)
    final_train_acc = evaluate_model(model, train_data)
    total_time = time.time() - start_time

    print(f"  Final: test={final_test_acc:.6f} train={final_train_acc:.6f} time={total_time:.1f}s")

    return {
        "test_accuracy": final_test_acc,
        "train_accuracy": final_train_acc,
        "epochs_to_99pct": threshold_epoch,
        "total_epochs": epoch,
        "wall_seconds": round(total_time, 2),
        "learning_rate": lr,
    }


def main():
    print("REPRODUCIBILITY GATE — harmonic_phase_correlator_v2")
    print(f"Seeds: {SEEDS}")
    print(f"Variance tolerance: {VARIANCE_TOLERANCE}")

    seed_results = {}
    for seed in SEEDS:
        result = train_with_seed(seed)
        seed_results[str(seed)] = result

    accuracies = [seed_results[str(s)]["test_accuracy"] for s in SEEDS]
    mean_acc = sum(accuracies) / len(accuracies)
    variance = sum((a - mean_acc) ** 2 for a in accuracies) / len(accuracies)

    all_accept = all(a >= THRESHOLD_ACC for a in accuracies)

    if all_accept and variance <= VARIANCE_TOLERANCE:
        verdict = "REPRODUCIBILITY_PASSED"
    else:
        verdict = "REPRODUCIBILITY_FAILED"

    results = {
        "seed_results": {str(s): {"test_accuracy": seed_results[str(s)]["test_accuracy"],
                                   "epochs_to_99pct": seed_results[str(s)]["epochs_to_99pct"]}
                         for s in SEEDS},
        "mean_accuracy": mean_acc,
        "variance": variance,
        "variance_tolerance": VARIANCE_TOLERANCE,
        "all_seeds_accept": all_accept,
        "overall_verdict": verdict,
    }

    with open(f"{OUT_DIR}/reproducibility_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"REPRODUCIBILITY RESULTS")
    print(f"{'='*60}")
    for s in SEEDS:
        r = seed_results[str(s)]
        print(f"  Seed {s:>4}: test_acc={r['test_accuracy']:.6f}  epochs_to_99%={r['epochs_to_99pct']}")
    print(f"  Mean accuracy: {mean_acc:.6f}")
    print(f"  Variance: {variance:.8f} (tolerance: {VARIANCE_TOLERANCE})")
    print(f"  All seeds ACCEPT: {all_accept}")
    print(f"\n  VERDICT: {verdict}")


if __name__ == "__main__":
    main()
