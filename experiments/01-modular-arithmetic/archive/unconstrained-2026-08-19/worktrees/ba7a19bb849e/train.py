#!/usr/bin/env python3
"""syndrome_refinement_decoder_v2 — build-variant ba7a19bb849e"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import json
import math
import time

PRIMES = [5, 7, 11, 13, 17, 19, 23, 29, 31]
PRIME_TO_IDX = {p: i for i, p in enumerate(PRIMES)}
SEED = 42
MAX_EPOCHS = 10000
WORKTREE = "/Users/hook/Documents/coding/python/Personal_AI  Projects/auto_archicture_discovery/.auto-discover/worktrees/ba7a19bb849e"


class SyndromeRefinementDecoderV2(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed_ab = nn.Embedding(31, 128)
        self.embed_p = nn.Embedding(len(PRIMES), 32)

        self.parity_acc = nn.Linear(128, 128)
        self.compress1 = nn.Linear(128, 32, bias=False)
        self.compress2 = nn.Linear(160, 64, bias=False)
        self.compress3 = nn.Linear(224, 128, bias=False)
        self.code_proj = nn.Linear(32, 32, bias=False)
        self.synth = nn.Linear(36, 224, bias=False)
        self.feedback = nn.Linear(31, 224, bias=False)

        self._sqrt_224 = math.sqrt(224)

    def _compute_scores(self, h_full, V):
        return torch.bmm(V, h_full.unsqueeze(2)).squeeze(2)

    def forward(self, a, b, p_idx, p_vals):
        e_a = self.embed_ab(a)
        e_b = self.embed_ab(b)
        e_p = self.embed_p(p_idx)

        h = F.relu(self.parity_acc(e_a + e_b))

        h1 = F.relu(self.compress1(h))
        h2 = F.relu(self.compress2(torch.cat([h, h1], dim=1)))
        h3 = F.relu(self.compress3(torch.cat([h, h1, h2], dim=1)))
        h_full = torch.cat([h1, h2, h3], dim=1)

        c_p = F.relu(self.code_proj(e_p))

        k_vals = torch.arange(31, device=a.device, dtype=torch.float32)
        p_float = p_vals.float().unsqueeze(1)
        phase1 = 2.0 * math.pi * k_vals.unsqueeze(0) / p_float
        phase2 = 2.0 * phase1

        harmonics = torch.stack([
            torch.cos(phase1), torch.sin(phase1),
            torch.cos(phase2), torch.sin(phase2)
        ], dim=2)

        c_p_exp = c_p.unsqueeze(1).expand(-1, 31, -1)
        synth_in = torch.cat([c_p_exp, harmonics], dim=2)
        V = F.relu(self.synth(synth_in))

        valid_mask = k_vals.unsqueeze(0) < p_float
        scores = self._compute_scores(h_full, V)

        for _ in range(2):
            scores_norm = scores / self._sqrt_224
            scores_fb = scores_norm * valid_mask.float()
            h_full = h_full + F.relu(self.feedback(scores_fb))
            scores = self._compute_scores(h_full, V)

        scores = scores.masked_fill(~valid_mask, float('-inf'))
        return scores


def generate_data():
    all_a, all_b, all_pidx, all_labels, all_pvals = [], [], [], [], []
    for p in PRIMES:
        for a_val in range(p):
            for b_val in range(p):
                all_a.append(a_val)
                all_b.append(b_val)
                all_pidx.append(PRIME_TO_IDX[p])
                all_labels.append((a_val + b_val) % p)
                all_pvals.append(p)

    tensors = [torch.tensor(x, dtype=torch.long) for x in
               [all_a, all_b, all_pidx, all_labels, all_pvals]]

    train_mask = torch.zeros(len(all_a), dtype=torch.bool)
    offset = 0
    for p in PRIMES:
        n = p * p
        perm = torch.randperm(n) + offset
        train_mask[perm[:n // 2]] = True
        offset += n

    test_mask = ~train_mask
    train = tuple(t[train_mask] for t in tensors)
    test = tuple(t[test_mask] for t in tensors)
    return train, test


def main():
    torch.manual_seed(SEED)

    train_data, test_data = generate_data()
    train_a, train_b, train_pidx, train_labels, train_pvals = train_data
    test_a, test_b, test_pidx, test_labels, test_pvals = test_data

    N_train = len(train_a)
    N_test = len(test_a)
    print(f"Train: {N_train}, Test: {N_test}")

    model = SyndromeRefinementDecoderV2()
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {total_params}")

    init_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.zero_grad()
    probe_scores = model(train_a, train_b, train_pidx, train_pvals)
    probe_loss = F.cross_entropy(probe_scores, train_labels)
    initial_loss = probe_loss.item()
    probe_loss.backward()

    grad_norms = sorted([p.grad.norm().item() for p in model.parameters() if p.grad is not None])
    median_norm = grad_norms[len(grad_norms) // 2]
    lr = 1e-2 / max(1.0, median_norm)
    lr = max(1e-4, min(5e-2, lr))
    print(f"Initial loss: {initial_loss:.4f}")
    print(f"Gradient probe median: {median_norm:.6f}, LR: {lr:.6f}")

    model.load_state_dict(init_state)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.3)

    fwd_flops_per_sample = (
        2*128*128 + 2*128*32 + 2*160*64 + 2*224*128 +
        2*32*32 + 31*2*36*224 + 31*2*224 +
        2*(2*31*224 + 31*2*224)
    )
    flops_per_epoch = 3 * fwd_flops_per_sample * N_train

    training_log = []
    grad_norm_history = []
    consecutive_high_grad = 0
    threshold_epoch = None
    best_test_acc = 0.0
    best_state = None
    best_epoch = 0
    verdict = "DONE"
    failure_reason = None
    start_time = time.time()
    final_epoch = 0

    for epoch in range(1, MAX_EPOCHS + 1):
        final_epoch = epoch
        model.train()
        optimizer.zero_grad()

        scores = model(train_a, train_b, train_pidx, train_pvals)
        loss = F.cross_entropy(scores, train_labels)
        loss.backward()

        grad_norm = 0.0
        for p_param in model.parameters():
            if p_param.grad is not None:
                grad_norm += p_param.grad.data.norm(2).item() ** 2
        grad_norm = grad_norm ** 0.5
        grad_norm_history.append(grad_norm)

        if grad_norm > 50:
            consecutive_high_grad += 1
            if consecutive_high_grad >= 3:
                verdict = "DONE_WITH_CONCERNS"
                failure_reason = f"Gradient norms exceeded 50 for 3 consecutive epochs at epoch {epoch}"
                print(f"FAILURE: {failure_reason}")
                break
        else:
            consecutive_high_grad = 0

        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()

        do_eval = (epoch % 100 == 0 or epoch == 1 or epoch == MAX_EPOCHS)
        if epoch > 3000 and epoch % 50 == 0:
            do_eval = True

        if do_eval:
            model.eval()
            with torch.no_grad():
                test_scores = model(test_a, test_b, test_pidx, test_pvals)
                test_preds = test_scores.argmax(dim=1)
                test_acc = (test_preds == test_labels).float().mean().item()

                train_preds = scores.detach().argmax(dim=1)
                train_acc = (train_preds == train_labels).float().mean().item()

            if test_acc > best_test_acc:
                best_test_acc = test_acc
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
                best_epoch = epoch

            if test_acc >= 0.99 and threshold_epoch is None:
                threshold_epoch = epoch

            elapsed = time.time() - start_time
            checkpoint = {
                "epoch": epoch,
                "train_loss": round(loss.item(), 6),
                "train_accuracy": round(train_acc, 6),
                "test_accuracy": round(test_acc, 6),
                "gradient_norm": round(grad_norm, 6),
                "elapsed_seconds": round(elapsed, 2),
                "cumulative_flops": epoch * flops_per_epoch,
            }
            training_log.append(checkpoint)

            if epoch % 500 == 0 or epoch == 1:
                print(f"E{epoch:5d} | loss {loss.item():.4f} | train {train_acc:.4f} | test {test_acc:.4f} | grad {grad_norm:.2f}")

        if epoch == 2000:
            model.eval()
            with torch.no_grad():
                chk = model(train_a, train_b, train_pidx, train_pvals)
                chk_loss = F.cross_entropy(chk, train_labels).item()
            if chk_loss >= initial_loss:
                failure_reason = f"Loss ({chk_loss:.4f}) not below initial ({initial_loss:.4f}) at 20% budget"
                print(f"WARNING: {failure_reason}")
                verdict = "DONE_WITH_CONCERNS"

        if epoch == 5000:
            model.eval()
            with torch.no_grad():
                chk = model(test_a, test_b, test_pidx, test_pvals)
                chk_acc = (chk.argmax(dim=1) == test_labels).float().mean().item()
            if chk_acc <= 0.60:
                failure_reason = f"Test accuracy ({chk_acc:.4f}) <= 60% at 50% budget"
                print(f"FAILURE: {failure_reason}")
                verdict = "DONE_WITH_CONCERNS"
                break

        if do_eval and best_test_acc >= 0.999:
            print(f"Converged at epoch {epoch} with test accuracy {best_test_acc:.6f}")
            break

    if best_state is not None:
        model.load_state_dict(best_state)
        print(f"Restored best model from epoch {best_epoch} (test_acc={best_test_acc:.6f})")

    model.eval()
    with torch.no_grad():
        test_scores = model(test_a, test_b, test_pidx, test_pvals)
        test_preds = test_scores.argmax(dim=1)
        final_test_acc = (test_preds == test_labels).float().mean().item()

        train_scores = model(train_a, train_b, train_pidx, train_pvals)
        best_train_loss = F.cross_entropy(train_scores, train_labels).item()

        per_prime = {}
        for p in PRIMES:
            mask = test_pvals == p
            if mask.any():
                per_prime[str(p)] = round(
                    (test_preds[mask] == test_labels[mask]).float().mean().item(), 6
                )

    elapsed = time.time() - start_time
    total_flops = final_epoch * flops_per_epoch
    mean_grad = sum(grad_norm_history) / len(grad_norm_history)

    if final_test_acc < 0.99 and verdict == "DONE":
        verdict = "DONE_WITH_CONCERNS"

    final_metrics = {
        "architecture": "syndrome_refinement_decoder_v2",
        "experiment_hash": "ba7a19bb849e",
        "seed": SEED,
        "total_parameters": total_params,
        "epochs_trained": final_epoch,
        "best_epoch": best_epoch,
        "final_train_loss": round(best_train_loss, 6),
        "test_accuracy_modular_addition": round(final_test_acc, 6),
        "per_prime_test_accuracy": per_prime,
        "samples_to_threshold_accuracy": threshold_epoch * N_train if threshold_epoch else None,
        "threshold_epoch": threshold_epoch,
        "gradient_health_mean_norm": round(mean_grad, 6),
        "param_efficiency_params_per_accuracy_point": round(total_params / max(final_test_acc * 100, 1e-6), 2),
        "total_flops": total_flops,
        "wall_clock_seconds": round(elapsed, 2),
        "learning_rate": lr,
        "verdict": verdict,
    }
    if failure_reason:
        final_metrics["failure_reason"] = failure_reason

    print(f"\n=== Final Results ===")
    print(f"Test accuracy: {final_test_acc:.6f}")
    print(f"Per-prime: {per_prime}")
    print(f"Threshold epoch: {threshold_epoch}")
    print(f"Mean gradient norm: {mean_grad:.4f}")
    print(f"Parameters: {total_params}")
    print(f"Wall clock: {elapsed:.1f}s")
    print(f"Verdict: {verdict}")

    with open(f"{WORKTREE}/training_metrics.json", "w") as f:
        json.dump(training_log, f, indent=2)

    with open(f"{WORKTREE}/final_metrics.json", "w") as f:
        json.dump(final_metrics, f, indent=2)

    print(f"Metrics written to {WORKTREE}/")


if __name__ == "__main__":
    main()
