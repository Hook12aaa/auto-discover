#!/usr/bin/env python3

import torch
import torch.nn as nn
import torch.nn.functional as F
import json
import time
import math
import os
import random

PRIMES = [5, 7, 11, 13, 17, 19, 23, 29, 31]
PRIME_TO_IDX = {p: i for i, p in enumerate(PRIMES)}
SEED = 42
MAX_EPOCHS = 10000
MAX_WALL_CLOCK_SECONDS = 7200
MAX_COMPUTE_FLOPS = 1e15
MAX_OUTPUT = 31
K = 32
TRAIN_FRACTION = 0.5
EVAL_INTERVAL = 100
ACCURACY_THRESHOLD = 0.99
DEVICE = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')


def generate_data():
    train_data, test_data = [], []
    rng = random.Random(SEED)
    for p in PRIMES:
        pairs = [(a, b, p, (a + b) % p) for a in range(p) for b in range(p)]
        rng.shuffle(pairs)
        split = int(len(pairs) * TRAIN_FRACTION)
        train_data.extend(pairs[:split])
        test_data.extend(pairs[split:])
    return train_data, test_data


def to_tensors(data, device):
    inputs = torch.tensor([[a, b, p] for a, b, p, _ in data], dtype=torch.long, device=device)
    targets = torch.tensor([t for _, _, _, t in data], dtype=torch.long, device=device)
    prime_indices = torch.tensor([PRIME_TO_IDX[p] for _, _, p, _ in data], dtype=torch.long, device=device)
    return inputs, targets, prime_indices


class TorusRotationCompositor(nn.Module):
    def __init__(self):
        super().__init__()
        self.omega = nn.Parameter(torch.linspace(0, 2 * math.pi, K + 1)[:K].clone())
        self.phi = nn.Parameter(torch.zeros(K))
        self.prime_embed = nn.Embedding(len(PRIMES), K)
        self.tau = nn.Parameter(torch.tensor(1.0))

        self.register_buffer('candidates', torch.arange(MAX_OUTPUT))
        masks = torch.zeros(len(PRIMES), MAX_OUTPUT)
        for i, p in enumerate(PRIMES):
            masks[i, :p] = 1.0
        self.register_buffer('prime_masks', masks)

    def forward(self, inputs, prime_indices):
        a = inputs[:, 0].float()
        b = inputs[:, 1].float()

        theta_a = a.unsqueeze(1) * self.omega.unsqueeze(0) + self.phi.unsqueeze(0)
        cos_a, sin_a = torch.cos(theta_a), torch.sin(theta_a)

        theta_b = b.unsqueeze(1) * self.omega.unsqueeze(0) + self.phi.unsqueeze(0)
        cos_b, sin_b = torch.cos(theta_b), torch.sin(theta_b)

        cos_composed = cos_a * cos_b - sin_a * sin_b
        sin_composed = cos_a * sin_b + sin_a * cos_b

        w = self.prime_embed(prime_indices)

        theta_c = self.candidates.float().unsqueeze(1) * self.omega.unsqueeze(0) + self.phi.unsqueeze(0)
        cos_c, sin_c = torch.cos(theta_c), torch.sin(theta_c)

        cos_diff = (cos_composed.unsqueeze(1) * cos_c.unsqueeze(0) +
                    sin_composed.unsqueeze(1) * sin_c.unsqueeze(0))

        scores = (w.unsqueeze(1) * cos_diff).sum(dim=2)
        scores = scores / self.tau

        masks = self.prime_masks[prime_indices]
        scores = scores.masked_fill(masks == 0, -1e9)

        return scores


def derive_learning_rate(model, inputs, targets, prime_indices):
    saved_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.zero_grad()
    loss = F.cross_entropy(model(inputs, prime_indices), targets)
    loss.backward()

    grad_norm_sq = sum(p.grad.norm().item() ** 2 for p in model.parameters() if p.grad is not None)
    initial_loss = loss.item()

    lr_theory = 0.01 * initial_loss / (grad_norm_sq + 1e-12)
    lr_theory = max(1e-5, min(lr_theory, 1e-1))

    candidates = sorted(set([
        max(1e-5, lr_theory * 0.1),
        max(1e-5, lr_theory * 0.3),
        lr_theory,
        min(1e-1, lr_theory * 3.0),
        min(1e-1, lr_theory * 10.0),
    ]))

    best_lr = lr_theory
    best_final_loss = float('inf')
    search_results = {}

    for lr_test in candidates:
        model.load_state_dict({k: v.clone() for k, v in saved_state.items()})
        opt = torch.optim.AdamW(model.parameters(), lr=lr_test, weight_decay=0.0)

        losses = []
        for _ in range(100):
            opt.zero_grad()
            l = F.cross_entropy(model(inputs, prime_indices), targets)
            l.backward()
            opt.step()
            losses.append(l.item())

        final = losses[-1]
        stable = all(l < initial_loss * 3 for l in losses)
        decreasing = final < initial_loss * 0.95

        search_results[lr_test] = {
            'final_loss': final,
            'stable': stable,
            'decreasing': decreasing,
        }

        if stable and decreasing and final < best_final_loss:
            best_final_loss = final
            best_lr = lr_test

    model.load_state_dict(saved_state)
    return best_lr, initial_loss, grad_norm_sq ** 0.5, lr_theory, search_results


def evaluate_model(model, inputs, targets, prime_indices, data):
    model.eval()
    with torch.no_grad():
        preds = model(inputs, prime_indices).argmax(dim=-1)
        correct = preds == targets
        acc = correct.float().mean().item()
        per_prime = {}
        for i, (_, _, p, _) in enumerate(data):
            if p not in per_prime:
                per_prime[p] = [0, 0]
            per_prime[p][1] += 1
            if correct[i].item():
                per_prime[p][0] += 1
        per_prime_acc = {p: c[0] / c[1] for p, c in sorted(per_prime.items())}
    model.train()
    return acc, per_prime_acc


def main():
    torch.manual_seed(SEED)
    train_data, test_data = generate_data()
    train_in, train_tgt, train_pidx = to_tensors(train_data, DEVICE)
    test_in, test_tgt, test_pidx = to_tensors(test_data, DEVICE)

    model = TorusRotationCompositor().to(DEVICE)
    num_params = sum(p.numel() for p in model.parameters())
    print(f"Train: {len(train_data)} | Test: {len(test_data)} | Params: {num_params} | Device: {DEVICE}")

    lr, initial_loss, grad_norm, lr_theory, search_results = derive_learning_rate(
        model, train_in, train_tgt, train_pidx
    )

    wd = math.log(2) / (MAX_EPOCHS * lr)
    flops_per_step = 6 * num_params * len(train_data)

    print(f"LR theory: {lr_theory:.6f} | LR selected: {lr:.6f} | WD: {wd:.6f}")
    print(f"Initial loss: {initial_loss:.4f} | Grad norm: {grad_norm:.4f}")
    for k, v in sorted(search_results.items()):
        print(f"  LR={k:.6f}: loss={v['final_loss']:.4f} stable={v['stable']} dec={v['decreasing']}")

    torch.manual_seed(SEED)
    model = TorusRotationCompositor().to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)

    total_flops = 0
    total_samples = 0
    grad_norms = []
    threshold_flops = None
    threshold_samples = None
    history = []

    start = time.time()
    final_epoch = 0

    for epoch in range(1, MAX_EPOCHS + 1):
        elapsed = time.time() - start
        if elapsed > MAX_WALL_CLOCK_SECONDS:
            print(f"Wall clock limit at epoch {epoch}")
            break
        if total_flops + flops_per_step > MAX_COMPUTE_FLOPS:
            print(f"FLOP limit at epoch {epoch}")
            break

        optimizer.zero_grad()
        logits = model(train_in, train_pidx)
        loss = F.cross_entropy(logits, train_tgt)
        loss.backward()

        gn = sum(p.grad.norm().item() ** 2 for p in model.parameters() if p.grad is not None) ** 0.5
        grad_norms.append(gn)

        optimizer.step()
        total_flops += flops_per_step
        total_samples += len(train_data)
        final_epoch = epoch

        if epoch % EVAL_INTERVAL == 0 or epoch == 1:
            test_acc, pp_acc = evaluate_model(model, test_in, test_tgt, test_pidx, test_data)
            train_acc = (logits.detach().argmax(-1) == train_tgt).float().mean().item()

            history.append({
                'epoch': epoch,
                'loss': loss.item(),
                'train_acc': train_acc,
                'test_acc': test_acc,
                'grad_norm': gn,
                'flops': total_flops,
                'samples': total_samples,
            })

            if test_acc >= ACCURACY_THRESHOLD and threshold_flops is None:
                threshold_flops = total_flops
                threshold_samples = total_samples
                print(f"  99% threshold at epoch {epoch}, test_acc={test_acc:.4f}")

            if epoch % 500 == 0:
                print(f"  E{epoch}: loss={loss.item():.4f} train={train_acc:.4f} test={test_acc:.4f} gnorm={gn:.4f}")

    elapsed = time.time() - start
    final_acc, final_pp = evaluate_model(model, test_in, test_tgt, test_pidx, test_data)
    mean_gn = sum(grad_norms) / len(grad_norms)

    metrics = {
        'test_accuracy_modular_addition': final_acc,
        'compute_to_threshold_ratio': threshold_flops / MAX_COMPUTE_FLOPS if threshold_flops is not None else None,
        'samples_to_threshold_accuracy': threshold_samples,
        'gradient_health_mean_norm': mean_gn,
        'param_efficiency_params_per_accuracy_point': num_params / (final_acc * 100) if final_acc > 0 else None,
    }

    worktree = '.auto-discover/worktrees/03d7c5957a78'

    training_record = {
        'training_history': history,
    }
    with open(os.path.join(worktree, 'training_metrics.json'), 'w') as f:
        json.dump(training_record, f, indent=2)

    final_record = {
        'architecture_name': 'torus_rotation_compositor',
        'metrics': metrics,
        'per_prime_accuracy': {str(k): v for k, v in final_pp.items()},
        'training_budget_used': {
            'epochs': final_epoch,
            'flops': total_flops,
            'wall_clock_seconds': elapsed,
            'samples_seen': total_samples,
        },
        'architecture': {
            'num_circles': K,
            'embedding_dim': 2 * K,
            'params': num_params,
            'layers': ['frequency_circular_embed', 'rotation_compose', 'prime_harmonic_gate', 'geodesic_classify'],
        },
        'hyperparameters': {
            'lr': lr,
            'weight_decay': wd,
            'optimizer': 'AdamW',
            'batch_size': len(train_data),
            'train_fraction': TRAIN_FRACTION,
            'seed': SEED,
        },
        'training_history': history,
    }
    with open(os.path.join(worktree, 'final_metrics.json'), 'w') as f:
        json.dump(final_record, f, indent=2)

    print(f"\n=== TORUS ROTATION COMPOSITOR RESULTS ===")
    print(f"Test accuracy: {final_acc:.4f}")
    print(f"Per-prime: {final_pp}")
    print(f"Mean grad norm: {mean_gn:.6f}")
    print(f"Params: {num_params} | Epochs: {final_epoch} | FLOPs: {total_flops:.2e} | Time: {elapsed:.1f}s")
    if threshold_flops is not None:
        print(f"99% threshold: {threshold_flops:.2e} FLOPs, {threshold_samples} samples")
    else:
        print(f"99% threshold: NOT reached")

    unstable_late = sum(1 for gn in grad_norms[-300:] if gn > 50)
    if final_acc < 0.1:
        print("VERDICT: DONE_WITH_CONCERNS")
        print("CONCERN: Very low accuracy suggests architecture may not be learning")
    elif unstable_late >= 3:
        print("VERDICT: DONE_WITH_CONCERNS")
        print("CONCERN: Gradient instability detected in final epochs")
    else:
        print("VERDICT: DONE")


if __name__ == '__main__':
    main()
