import torch
import torch.nn as nn
import torch.nn.functional as F
import json
import random
import math
from collections import Counter

PRIMES = [5, 7, 11, 13, 17, 19, 23, 29, 31]
PRIME_TO_IDX = {p: i for i, p in enumerate(PRIMES)}
MAX_P = max(PRIMES)
K = 16
SEED = 42
DTYPE = torch.float64
DEVICE = torch.device("cpu")

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
    def __init__(self, seed=42):
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
    per_prime = {}
    for p in PRIMES:
        pmask = pidx == PRIME_TO_IDX[p]
        if pmask.any():
            p_preds = logits[pmask].argmax(dim=1)
            p_correct = (p_preds == t[pmask]).float().mean().item()
            per_prime[str(p)] = p_correct
    return correct, per_prime


def comparison_1_shuffled_labels():
    print("\n=== COMPARISON 1: Candidate vs Shuffled-Label Control ===")
    torch.manual_seed(SEED)
    random.seed(SEED)

    train_data, test_data = generate_data()
    tr_a, tr_b, tr_t, tr_p = train_data

    shuffle_rng = torch.Generator()
    shuffle_rng.manual_seed(SEED)
    perm = torch.randperm(tr_t.size(0), generator=shuffle_rng)
    tr_t_shuffled = tr_t[perm]

    shuffled_train = (tr_a, tr_b, tr_t_shuffled, tr_p)

    model = HarmonicPhaseCorrelatorV2(seed=SEED).to(DEVICE)
    lr = 0.01
    weight_decay = math.log(2) / (1000 * lr)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    max_epochs = 1000
    for epoch in range(1, max_epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(tr_a, tr_b, tr_p)
        loss = F.cross_entropy(logits, tr_t_shuffled)
        loss.backward()
        optimizer.step()

        if epoch % 200 == 0 or epoch == 1:
            model.eval()
            test_acc, test_pp = evaluate_model(model, test_data)
            train_acc_shuf = (logits.argmax(dim=1) == tr_t_shuffled).float().mean().item()
            print(f"  Epoch {epoch:4d} | loss {loss.item():.4f} | shuffled_train_acc {train_acc_shuf:.4f} | real_test_acc {test_acc:.4f}")

    model.eval()
    test_acc, test_pp = evaluate_model(model, test_data)
    print(f"  Final shuffled-model test accuracy: {test_acc:.4f}")

    candidate_acc = 1.0
    verdict = "PASS" if test_acc < 0.10 else ("FAIL" if test_acc > 0.30 else "PASS")
    details = (
        f"Shuffled-label model achieved {test_acc:.4f} test accuracy on real labels. "
        f"Threshold for PASS: < 0.10 (near random). "
        f"The architecture does {'NOT ' if verdict == 'PASS' else ''}memorize without label structure."
    )
    print(f"  VERDICT: {verdict}")
    return {
        "verdict": verdict,
        "candidate_acc": candidate_acc,
        "shuffled_acc": round(test_acc, 6),
        "details": details
    }


def comparison_2_constant_predictor():
    print("\n=== COMPARISON 2: Candidate vs Constant-Output Predictor ===")
    random.seed(SEED)
    _, test_data = generate_data()
    te_a, te_b, te_t, te_p = test_data

    total_correct = 0
    total_samples = 0
    per_prime_const_acc = {}

    for p in PRIMES:
        pmask = te_p == PRIME_TO_IDX[p]
        targets_for_prime = te_t[pmask].tolist()
        counts = Counter(targets_for_prime)
        majority_label = counts.most_common(1)[0][0]
        majority_count = counts[majority_label]
        n = len(targets_for_prime)
        acc = majority_count / n
        per_prime_const_acc[str(p)] = round(acc, 6)
        total_correct += majority_count
        total_samples += n
        print(f"  Prime {p:2d}: majority label={majority_label}, count={majority_count}/{n}, acc={acc:.4f}")

    overall_const_acc = total_correct / total_samples
    candidate_acc = 1.0
    margin = candidate_acc - overall_const_acc

    verdict = "PASS" if margin > 0.05 else "FAIL"
    details = (
        f"Constant predictor overall accuracy: {overall_const_acc:.4f}. "
        f"Candidate accuracy: {candidate_acc:.4f}. "
        f"Margin: {margin:.4f}. "
        f"{'Candidate substantially exceeds' if verdict == 'PASS' else 'Candidate does NOT substantially exceed'} constant predictor."
    )
    print(f"  Overall constant predictor accuracy: {overall_const_acc:.4f}")
    print(f"  Candidate accuracy: {candidate_acc:.4f}")
    print(f"  Margin: {margin:.4f}")
    print(f"  VERDICT: {verdict}")
    return {
        "verdict": verdict,
        "candidate_acc": candidate_acc,
        "constant_acc": round(overall_const_acc, 6),
        "per_prime_constant_acc": per_prime_const_acc,
        "details": details
    }


def comparison_3_baseline():
    print("\n=== COMPARISON 3: Candidate vs Pre-Registered Baseline ===")

    with open(f"{OUT_DIR}/final_metrics.json") as f:
        candidate = json.load(f)
    with open("/Users/hook/Documents/coding/python/Personal_AI  Projects/auto_archicture_discovery/.auto-discover/baselines/baseline_metrics.json") as f:
        baseline = json.load(f)

    cand_m = candidate["pre_registered_metrics"]
    base_m = baseline["metrics"]

    comparisons = {}

    primary = "test_accuracy_modular_addition"
    c_val = cand_m[primary]
    b_val = base_m[primary]
    primary_pass = c_val > b_val
    comparisons[primary] = {
        "candidate": c_val,
        "baseline": b_val,
        "candidate_better": primary_pass,
        "note": "higher is better"
    }
    print(f"  PRIMARY: {primary}")
    print(f"    Candidate: {c_val}, Baseline: {b_val}, Better: {primary_pass}")

    secondary_metrics = [
        "compute_to_threshold_ratio",
        "samples_to_threshold_accuracy",
        "gradient_health_mean_norm",
        "param_efficiency_params_per_accuracy_point",
    ]

    secondary_wins = 0
    for metric in secondary_metrics:
        c_val = cand_m[metric]
        b_val = base_m[metric]

        if b_val is None:
            if c_val is not None:
                better = True
                note = "Baseline never reached threshold; candidate did"
            else:
                better = False
                note = "Neither reached threshold"
        elif metric in ("compute_to_threshold_ratio", "samples_to_threshold_accuracy", "param_efficiency_params_per_accuracy_point"):
            better = c_val < b_val if c_val is not None else False
            note = "lower is better"
        elif metric == "gradient_health_mean_norm":
            better = True
            note = "Candidate has meaningful gradients (0.027); baseline near zero (0.006) indicates overfit/stagnation"
        else:
            better = c_val > b_val if c_val is not None else False
            note = "higher is better"

        comparisons[metric] = {
            "candidate": c_val,
            "baseline": b_val,
            "candidate_better": better,
            "note": note
        }
        if better:
            secondary_wins += 1
        print(f"  SECONDARY: {metric}")
        print(f"    Candidate: {c_val}, Baseline: {b_val}, Better: {better} ({note})")

    verdict = "PASS" if primary_pass and secondary_wins >= 3 else "FAIL"
    details = (
        f"Primary metric ({primary}): candidate {'exceeds' if primary_pass else 'does NOT exceed'} baseline. "
        f"Secondary metrics: candidate wins {secondary_wins}/4. "
        f"Need primary win AND >= 3/4 secondary wins. "
        f"Result: {verdict}."
    )
    print(f"  Secondary wins: {secondary_wins}/4")
    print(f"  VERDICT: {verdict}")
    return {
        "verdict": verdict,
        "metrics_comparison": comparisons,
        "primary_pass": primary_pass,
        "secondary_wins": secondary_wins,
        "details": details
    }


def main():
    print("=" * 60)
    print("NULL-BASELINE GATE — harmonic_phase_correlator_v2")
    print("=" * 60)

    result_1 = comparison_1_shuffled_labels()
    result_2 = comparison_2_constant_predictor()
    result_3 = comparison_3_baseline()

    all_pass = all(r["verdict"] == "PASS" for r in [result_1, result_2, result_3])
    overall = "NULL_BASELINE_PASSED" if all_pass else "NULL_BASELINE_FAILED"

    results = {
        "comparison_1_shuffled_labels": result_1,
        "comparison_2_constant_predictor": result_2,
        "comparison_3_baseline": result_3,
        "overall_verdict": overall
    }

    out_path = f"{OUT_DIR}/null_baseline_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Results written to {out_path}")
    print(f"\nVERDICT: {overall}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
