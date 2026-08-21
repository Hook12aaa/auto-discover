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
SEED = 42
MAX_EPOCHS = 10000
MAX_WALL_CLOCK_SECONDS = 7200
MAX_COMPUTE_FLOPS = 1e15
VOCAB_SIZE = 32
D_MODEL = 128
N_HEADS = 4
N_LAYERS = 2
D_FF = 512
MAX_OUTPUT = 31
SEQ_LEN = 3
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
    return inputs, targets


class Baseline(nn.Module):
    def __init__(self):
        super().__init__()
        self.tok_emb = nn.Embedding(VOCAB_SIZE, D_MODEL)
        self.pos_emb = nn.Embedding(SEQ_LEN, D_MODEL)
        layer = nn.TransformerEncoderLayer(
            d_model=D_MODEL, nhead=N_HEADS, dim_feedforward=D_FF,
            batch_first=True, dropout=0.0, norm_first=True
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=N_LAYERS)
        self.head = nn.Linear(D_MODEL, MAX_OUTPUT)

    def forward(self, x):
        pos = torch.arange(SEQ_LEN, device=x.device).unsqueeze(0)
        h = self.tok_emb(x) + self.pos_emb(pos)
        h = self.encoder(h)
        return self.head(h.mean(dim=1))


def derive_learning_rate(model, inputs, targets):
    saved_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.zero_grad()
    loss = F.cross_entropy(model(inputs), targets)
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
            l = F.cross_entropy(model(inputs), targets)
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


def evaluate_model(model, inputs, targets, data):
    model.eval()
    with torch.no_grad():
        preds = model(inputs).argmax(dim=-1)
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
    train_in, train_tgt = to_tensors(train_data, DEVICE)
    test_in, test_tgt = to_tensors(test_data, DEVICE)

    model = Baseline().to(DEVICE)
    num_params = sum(p.numel() for p in model.parameters())
    print(f"Train: {len(train_data)} | Test: {len(test_data)} | Params: {num_params} | Device: {DEVICE}")

    lr, initial_loss, grad_norm, lr_theory, search_results = derive_learning_rate(
        model, train_in, train_tgt
    )

    wd = math.log(2) / (MAX_EPOCHS * lr)

    ratio = num_params / len(train_data)
    flops_per_step = 6 * num_params * SEQ_LEN * len(train_data)

    print(f"LR theory: {lr_theory:.6f} | LR selected: {lr:.6f} | WD: {wd:.6f}")
    print(f"Initial loss: {initial_loss:.4f} | Grad norm: {grad_norm:.4f} | Param/sample: {ratio:.1f}")
    for k, v in sorted(search_results.items()):
        fl = v['final_loss']
        st = v['stable']
        dc = v['decreasing']
        print(f"  LR={k:.6f}: loss={fl:.4f} stable={st} dec={dc}")

    derivation = {
        'learning_rate': {
            'value': lr,
            'derivation_method': 'loss_gradient_probe_with_validation',
            'input_measurement': {
                'initial_loss': initial_loss,
                'full_batch_gradient_norm': grad_norm,
                'theoretical_lr': lr_theory,
                'formula': '0.01 * L / ||grad||^2 — targets 1% loss reduction per step in quadratic approximation',
                'validation': 'Tested 5 candidates (0.1x to 10x theory) for 100 steps each; selected lowest final loss among stable, decreasing runs',
                'search_results': {str(k): v for k, v in search_results.items()},
            },
        },
        'weight_decay': {
            'value': wd,
            'derivation_method': 'budget_based_decay_targeting',
            'input_measurement': {
                'max_epochs': MAX_EPOCHS,
                'learning_rate': lr,
                'target_shrinkage': 0.5,
                'formula': 'ln(2) / (max_epochs * lr) — targets 50% weight magnitude shrinkage over training budget without learning signal',
            },
        },
        'optimizer': {
            'value': 'AdamW',
            'derivation_method': 'default_adaptive',
            'input_measurement': {
                'rationale': 'AdamW provides per-parameter adaptive learning rates; decoupled weight decay avoids coupling regularization to gradient magnitude',
            },
        },
        'batch_size': {
            'value': len(train_data),
            'derivation_method': 'dataset_size_analysis',
            'input_measurement': {
                'train_set_size': len(train_data),
                'rationale': 'Full batch gives exact gradient; dataset fits in memory',
            },
        },
        'dropout': {
            'value': 0.0,
            'derivation_method': 'regularization_strategy',
            'input_measurement': {
                'param_to_sample_ratio': ratio,
                'rationale': 'With full-batch training, dropout adds noise to an already exact gradient; weight decay is the appropriate regularization for this regime',
            },
        },
        'architecture': {
            'd_model': D_MODEL,
            'n_heads': N_HEADS,
            'd_ff': D_FF,
            'n_layers': N_LAYERS,
            'num_params': num_params,
            'norm_first': True,
            'derivation': {
                'd_model': f'{D_MODEL} gives {num_params} params within max_parameters=500000',
                'n_heads': f'd_model/{D_MODEL // N_HEADS}={N_HEADS}, {D_MODEL // N_HEADS} dims per head',
                'd_ff': f'4*d_model={D_FF}',
                'n_layers': 'Per null_hypothesis declaration',
                'norm_first': 'Pre-LN for gradient stability with deep residual paths',
                'pooling': 'Mean over 3 positions — all inputs (a, b, p) contribute equally to the answer',
            },
        },
        'train_fraction': {
            'value': TRAIN_FRACTION,
            'derivation_method': 'residue_coverage_analysis',
            'input_measurement': {
                'primes': PRIMES,
                'min_residue_appearances': f'At 50%, each residue appears ~p/2 times: min {min(PRIMES) // 2} for p={min(PRIMES)}',
            },
        },
    }

    torch.manual_seed(SEED)
    model = Baseline().to(DEVICE)
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
        logits = model(train_in)
        loss = F.cross_entropy(logits, train_tgt)
        loss.backward()

        gn = sum(p.grad.norm().item() ** 2 for p in model.parameters() if p.grad is not None) ** 0.5
        grad_norms.append(gn)

        optimizer.step()
        total_flops += flops_per_step
        total_samples += len(train_data)
        final_epoch = epoch

        if epoch % EVAL_INTERVAL == 0 or epoch == 1:
            test_acc, pp_acc = evaluate_model(model, test_in, test_tgt, test_data)
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
                print(f"  E{epoch}: loss={loss.item():.4f} train={train_acc:.4f} test={test_acc:.4f} gnorm={gn:.2f}")

    elapsed = time.time() - start
    final_acc, final_pp = evaluate_model(model, test_in, test_tgt, test_data)
    mean_gn = sum(grad_norms) / len(grad_norms)

    metrics = {
        'test_accuracy_modular_addition': final_acc,
        'compute_to_threshold_ratio': threshold_flops / MAX_COMPUTE_FLOPS if threshold_flops is not None else None,
        'samples_to_threshold_accuracy': threshold_samples,
        'gradient_health_mean_norm': mean_gn,
        'param_efficiency_params_per_accuracy_point': num_params / (final_acc * 100) if final_acc > 0 else None,
    }

    record = {
        'null_hypothesis': 'A standard 2-layer transformer with softmax scoring trained on the same data with the same compute budget.',
        'metrics': metrics,
        'per_prime_accuracy': {str(k): v for k, v in final_pp.items()},
        'training_budget_used': {
            'epochs': final_epoch,
            'flops': total_flops,
            'wall_clock_seconds': elapsed,
            'samples_seen': total_samples,
        },
        'architecture': {
            'd_model': D_MODEL,
            'n_heads': N_HEADS,
            'n_layers': N_LAYERS,
            'd_ff': D_FF,
            'params': num_params,
            'norm_first': True,
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

    with open('.auto-discover/baselines/baseline_metrics.json', 'w') as f:
        json.dump(record, f, indent=2)
    with open('.auto-discover/baselines/derivation.json', 'w') as f:
        json.dump(derivation, f, indent=2)

    print(f"\n=== BASELINE RESULTS ===")
    print(f"Test accuracy: {final_acc:.4f}")
    print(f"Per-prime: {final_pp}")
    print(f"Mean grad norm: {mean_gn:.4f}")
    print(f"Params: {num_params} | Epochs: {final_epoch} | FLOPs: {total_flops:.2e} | Time: {elapsed:.1f}s")
    if threshold_flops is not None:
        print(f"99% threshold: {threshold_flops:.2e} FLOPs, {threshold_samples} samples")
    else:
        print(f"99% threshold: NOT reached")
    print("VERDICT: BASELINE_LOCKED")


if __name__ == '__main__':
    main()
