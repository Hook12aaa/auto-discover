# Research Notes

What I'd like to capture here is how I researched this, because building something like this never works perfectly the first time. By sharing the methodology and the experience, I'm hoping someone willing to build something similar can learn how to improve on it.

---

## Starting with a grounded target

The project started as a linear pipeline. One genome spec, one training run, one verdict. Pre-register a hypothesis, train a baseline, propose an architecture, run it through gates, declare confirmed or refuted.

Rather than trying to find entirely new architectures with no target, I wanted to ground it in reality. If I didn't know what I was aiming for, I wouldn't have a goal I could actually measure against. So I based the first hypothesis on a mathematical paper: cyclic-group attention for modular arithmetic. Something adjacent enough to the norm that I suspected Claude would often default to known approaches rather than deriving anything new. That suspicion turned out to be the whole point.

## Failing in the right direction

The first couple of failures hit because we kept trying to do traditional methodology. The candidate temporarily grokked on 3 of 9 primes, hit 99% accuracy, then collapsed. The standard transformer without any inductive bias actually did better: 57.5% versus 22.1%. The architecture found the answer, then lost it.

What mattered was not that it failed but how it failed. A model that reaches 99% accuracy and stays there has what I started calling *grounded convergence*: the representation is structurally sound. A model that reaches 99% then drops to 12% has *consensus convergence*: it found an attractor without structural backing. Both look identical in a loss curve. You only see the difference in the accuracy trajectory over continued optimization.

The convergence script at the time measured loss plateaus and accuracy thresholds. It was a grokking detector. It could tell you whether a known phenomenon occurred. It could not tell you whether the model's convergence was backed by stable structure or by something that would evaporate.

## The thermometer problem

That first fix was only the surface. The deeper problem took three rounds of failure to see, and each round was the same structural failure at a different level.

First, the convergence check was a grokking detector. I fixed it with search-level convergence: spec-class exhaustion and Pareto front stability.

Then, the `allowed_ops` in the hypothesis named the answer. `modular_distance_attention` was already in the search space before any exploration ran. The "discovery" was selecting from a rigged menu. I fixed it with a content gate that rejects architecture-pattern terminology in op names.

Then, the entire hypothesis was a grokking experiment. The success criteria said "grokking delay." The metrics included `grokking_delay_ratio`. The training budget was 5000 epochs, borrowed from the grokking literature. Claude composed the baseline as a standard grokking recipe because that's what its training data says to do for modular arithmetic. Nobody questioned whether "grokking" was the right frame.

The analogy that finally made it click: we built a thermometer to detect whether it was light outside. Temperature correlates with daylight, loosely, sometimes. But it's the wrong instrument. It measures the wrong thing. And when it fails, the failure looks like "the measurement is inconclusive" rather than "the instrument is wrong."

| Round | What was retrieved | What should have been derived |
|---|---|---|
| 1 | Loss-plateau convergence (from grokking papers) | Search-space exhaustion |
| 2 | `modular_distance_attention` (from literature) | Abstract op names |
| 3 | The entire experimental setup (weight decay, epochs, criteria) | Training setup from data/architecture characteristics |

The pattern: Claude retrieves the frame from its training data before the anti-retrieval gates can fire. The gates guarded the back door (architecture search) but not the front door (hypothesis content) or the side door (baseline composition).

## Fixing retrieval at every level

The fix is one principle applied uniformly across the pipeline: derive, don't retrieve. Every composed artifact traces to a derivation from the problem structure, not recall from training data.

In pre-register, a content gate rejects phenomenon-named metrics. `grokking_delay_ratio` fails; `compute_to_threshold_ratio` passes. A compute-normalized budget is required because epoch-only budgets import a frame assumption.

In establish-baseline, a derivation gate requires hyperparameters to trace to first principles. Learning rate from gradient scale analysis, regularization from parameter-to-sample ratio. Not "weight decay 1.0 because that's what the papers use."

In evaluate, an operational classification gate records trajectory shapes, not phenomenon names. `accuracy_trajectory: spike_then_drop` instead of `convergence_type: consensus_collapsed`. The shape is the data. The name is the story. Record the shape.

The methodology has four principles:

- **Restate before you act.** Restate the problem in two different ways before composing anything.
- **Derive, don't retrieve.** Every composed artifact traces to a derivation, not recall.
- **Name the analogy.** When adapting a method, state which related problem it comes from.
- **Look back.** After every result, ask what it tells you about the frame, not just the model.

## Competing perspectives

When the first experiment failed, I spawned three independent agents, each blind to the others, to compete on what to try next.

The Contrarian argued the inductive bias philosophy was fundamentally wrong. Pre-built structure creates a local attractor that traps the network.

The Dynamics Engineer argued the architecture was right but the training dynamics destabilized it. Weight decay destroys the circular parameters. The learnable temperature oscillates.

The Mathematician, working from first principles rather than ML, argued the circular embedding operates in the spatial domain, but the solution lives in the frequency domain. These are dual, related by DFT but computationally opposite.

All three were right about different things. None would have reached the synthesis alone.

| Perspective | Key insight | Blind spot |
|---|---|---|
| Contrarian | Pre-built structure blocks the phase transition | Throws out geometric bias entirely |
| Dynamics | The representation works but optimization destroys it | Doesn't question whether circular is the correct representation |
| Mathematician | The solution is Fourier, not circular | Proposes fixed frequencies that might need to be learned |

The synthesis: the circular embedding is in the wrong domain. It encodes spatial position on a circle. But models that solve modular arithmetic learn Fourier modes. The fix isn't to remove the bias or stabilize it, it's to change the representation entirely. Deliberately blinding perspectives and forcing competition prevents consensus convergence at the thinking level, not just the training level.

## The constrained run

The first full run with anti-retrieval gates, evolutionary search, and compute-normalized budgets. 8 specs across 7 classes, 3 rounds.

The winner was a strict bottleneck pipeline: `standard_linear, l2_normalize, cyclic_projection, modular_distance_scoring`. 13K params, 98.27% test accuracy versus the baseline's 42.44% at 405K params. All end gates passed. The composition strategy was the discovery, not the ops.

But the run also broke things. The converge skill's front diversity condition created a deadlock where one class dominated everything but convergence couldn't fire because the front only had one class. A fixed 5000-epoch budget wasted 80-98% of compute when most specs peaked in under 1000 epochs. Two specs with identical ops but different composition graphs were flagged as "too similar" because divergence measured the wrong thing.

Each of these got fixed: front diversity became a diagnostic instead of a gate, adaptive early stopping replaced fixed budgets, composition-topology fingerprints replaced ops-overlap ratios.

The deeper lesson was that the search space was still framed. With only 6 allowed_ops all designed around the cyclic thesis, the search could only discover composition strategies within a rigged vocabulary. It answered "what's the best way to compose cyclic ops" rather than "what's the best architecture for modular arithmetic."

## Going unconstrained

I stripped hypothesis.yaml to the minimum. No allowed_ops, no hybrid_ratio_range, no num_heads_range. Just the task (modular addition mod p for primes 5-31), the compute budget, and max_parameters.

3 rounds, 6 spec classes, 9 variants. The research subagents worked from six analogy domains: signal processing, geometric, and information-theoretic in round 1; dynamical systems, algebraic, and combinatorial in round 2. Each restated the problem differently and proposed architectures from first principles.

Most of round 1 scored low or failed isolation. Round 2 refined the geometric approach to 99.94% accuracy and introduced a signal-processing approach. Round 3 produced the winner.

**harmonic_phase_correlator_v2.** 100% test accuracy across all 9 primes. 160 parameters. 100 epochs from random init. From the signal processing framing: "what if addition in Z/pZ is a convolution?"

The architecture is 5 ops in a sequential pipeline:

- **prime_modulator**: a learned frequency table, 9 primes x 16 channels (144 params). The only learned component.
- **harmonic_projector**: projects integers onto a harmonic basis (0 params).
- **phase_adder**: complex multiplication that hardwires the group homomorphism (0 params). This is the convolution theorem: addition in Z/pZ is pointwise multiplication of Fourier characters.
- **amplitude_weighter**: per-channel scaling (16 params). Learns which frequency channels matter.
- **correlation_classifier**: inverse projection readout (0 params).

The architecture IS the convolution theorem on finite cyclic groups, implemented as a neural network with only two learned components.

Remember the competing perspectives? The Mathematician said the solution lives in the frequency domain. The unconstrained search, working from a signal-processing restatement of the problem, independently arrived at the same conclusion and built it as an architecture.

| Run | Constraint | Winner | Accuracy | Params |
|---|---|---|---|---|
| Linear pipeline | Pre-written code | cyclic attention | 22% | n/a |
| Constrained | 6 allowed_ops | strict-bottleneck-pipeline | 98.27% | 13,011 |
| Unconstrained | Task + compute only | harmonic_phase_correlator | 100% | 160 |

Each run removed a constraint and found something the previous run couldn't. The frame is the constraint. Remove the frame, and the harness finds the mathematical structure of the problem, not a variant of a known architecture, but the actual theorem that governs the task.

## Testing on a different domain

Different domain, same harness. The hypothesis: find a message-passing neural network that can distinguish all pairs of non-isomorphic graphs that the 1-Weisfeiler-Leman test can distinguish, using fewer parameters and less compute than a standard GCN with mean aggregation.

No allowed_ops. No references. Just the task and the compute budget.

4 rounds, 13 specs across 8 classes. The search explored symmetric polynomials, moment-based aggregation, multiband parallel fusion, cumulant generating functions, Boltzmann energy models, structural probes, multi-probe fingerprinting, and guild-partitioned aggregation. Four specs failed isolation. The rest trained.

Most plateaued at chance level (0.51 on binary classification). Two classes broke through to 100%: structural probes and guild-partitioned aggregation.

The winner was **niche_partitioned_aggregator** at 20,745 params, 100% accuracy on all WL-distinguishable graph pairs. A slimmer variant hit 16,769 params at the same accuracy. The key insight: partition the embedding dimension into 3 "guilds," each computing a different aggregation statistic (sum over dims 0-9, max over dims 10-19, std over dims 20-31), then mix across guilds with a learned linear layer. Related to but distinct from the known GIN architecture, which uses pure sum aggregation. The harness discovered that you need multiple aggregation statistics operating on different subspaces of the embedding.

A second architecture, yoneda_faithful_functor_net, also scored 100% (56,673 params) via a completely different approach: 6D structural probes with injective sum aggregation. Two independent classes reaching 100% through different mechanisms is exactly what the convergence check is designed to look for.

The search converged cleanly. No post-run fixes needed. The methodology transferred to a completely different domain.

## What I learned

Retrieval is the deepest failure mode. Not hallucination, not process drift. Claude retrieving a known experimental setup is more dangerous than Claude inventing one, because the retrieved setup looks competent and passes surface-level review.

The thermometer problem is recursive. Every time you fix retrieval at one level, it's still happening at the level below. Fixing the convergence check revealed the allowed_ops bias. Fixing the allowed_ops revealed the hypothesis bias. Fixing the hypothesis revealed the baseline composition bias. Each level was the same pattern: assuming the frame instead of deriving it.

The frame is the constraint. Three runs on modular arithmetic proved this: pre-written code produced 22% accuracy, constrained ops produced 98.27%, unconstrained produced 100% with 80x fewer parameters. The ceiling was never the harness, it was the vocabulary the harness was allowed to use.

Adversarial validation after every "success" is non-negotiable. The first confirmed discovery was real results with a rigged process. Without five adversarial agents, each blind to the others, the rigging would not have been caught.

Competing perspectives prevent consensus at the thinking level. Three agents with different framings produced a synthesis none could reach alone. The unconstrained search later validated the Mathematician's frequency-domain thesis.

Process design beats gates. Gates catch integrity violations. But process drift is an assumption problem, and you solve it by designing the process so the assumption has no room.

## The methodology question (v0.3)

After the unconstrained run and the graph experiment, I thought the pipeline was in good shape. Two domains, two confirmed discoveries. But something kept bothering me.

I looked at how auto_model_trainer worked — the project that came before this one. It used contract-first skills: typed inputs, typed outputs, a verdict. No teaching. The skill says what to check and what to emit. Claude figures out how to do it in the target project's language.

auto-discover wasn't doing that. It was teaching methodology. Polya's heuristics, domain catalogs, analysis checklists. The skills said "here's how to think about this problem" instead of "here's the contract you need to satisfy." That's a form of retrieval too — not retrieving an architecture, but retrieving a methodology from the skill text and applying it pattern-match style.

So v0.3 replaced the methodology-teaching skills with contract-first ones. Each skill became a typed contract pointing at colocated reference docs. analyze-problem got a domain registry. explore got a component catalog. propose-spec got a genome schema.

It was cleaner. But the catalogs were still prescriptive. The domain registry listed what domains exist. The component catalog listed what components to try. The search could still only find what I'd thought to put in the tables. I'd moved from prescribing methodology to prescribing content, and the constraint was the same.

I tested v0.3 on modular arithmetic again. 17,311 parameters. Failed reproducibility on a secondary metric. The catalog approach was strictly worse than the unconstrained v0.1 run.

## Stripping the catalogs (v0.3 raw session)

To prove the catalogs were the bottleneck, I ran a raw research session outside the formal pipeline. No catalogs, no domain registry, no component vocabulary. Just "here's the problem, probe it with scripts, web-search what you find, build something."

It found a 124-parameter architecture. Better than v0.3's 17k. The formal pipeline with its catalogs was actively getting in the way.

That was the moment the project's philosophy crystallised: prescribe how to research, not what to find. The search space should emerge from the problem, not from tables I wrote in advance.

## Research-driven discovery (v0.4)

v0.4 deleted three skills (analyze-problem, explore, propose-spec) and their eight reference docs. Replaced them with a single `research` skill that prescribes process:

1. **Probe** the problem with short scripts (≤50 lines). Look at the data, the baseline's failures, the mathematical structure.
2. **Web-search** based on what the probes find. Not "search for modular arithmetic architectures" but "the probes found circulant structure — search for that."
3. **Prototype** candidate architectures (≤100 lines, ≤500 epochs). Test the idea before committing to a full training run.
4. **Learn** from the prototype results. What worked, what didn't, why.
5. **Diverge** — try something the previous rounds didn't try.

Four hard gates: every genome spec traces to a logged finding, no catalog or registry references, no architecture-pattern terminology in spec names, structural_basis must cite specific probe or prototype IDs.

I ran v0.4 on modular arithmetic. Four rounds:

| Round | Accuracy | Params | What happened |
|---|---|---|---|
| R1 | 45.51% | — | Per-prime sine bilinear. Failed — approach too fragmented |
| R2 | 95.73% | 29k | Frequency products work, but p=5 bottleneck |
| R3 | 100% | 2,335 | Cross-prime sharing fixes p=5 |
| R4 | 100% | 0 | Pure algebra — no learning needed |

Each round learned from the previous round's failure. R1 failed, R2 diagnosed why. R2 had a bottleneck on p=5, R3 fixed it. R3 worked but had 2,335 parameters. R4 asked "can we go smaller?" and found the theoretical floor: a zero-parameter DFT of the addition table. The architecture isn't a neural network. It's the theorem implemented directly.

The orchestrator ended at 25% context through 4 rounds plus all end gates. Subagent dispatch with worktree isolation held throughout. Compare that to v0.1 which crashed at 100% context in a single linear run.

## The full version table

| Version | What I prescribed | What it found | Params | Accuracy |
|---|---|---|---|---|
| v0.1 linear | Written code | cyclic attention | n/a | 22% |
| v0.1 constrained | 6 allowed ops | strict bottleneck pipeline | 13,011 | 98.27% |
| v0.1 unconstrained | Task + compute only | harmonic_phase_correlator | 160 | 100% |
| v0.1 graph domain | Task + compute only | niche_partitioned_aggregator | 16,769 | 100% |
| v0.3 catalogs | Domain registry + component catalog | catalog-derived architecture | 17,311 | REFUTED |
| v0.3 raw session | Nothing (no pipeline) | probe-derived architecture | 124 | 100% |
| v0.4 research pipeline | How to research | pure algebraic DFT | 0 | 100% |

The trend is clear. Every version that prescribed less found something better. The catalogs (v0.3) were strictly worse than prescribing nothing (v0.3 raw). The research pipeline (v0.4) — which prescribes process but not content — found the theoretical optimum.

## What I'm still figuring out

Modular arithmetic has an exact analytical solution. Claude's training data covers the relevant group theory. I can't fully separate discovery from recall on this problem. The probes "discovered" the circulant structure, but Claude already knew what to probe for. The anti-retrieval discipline is softer in v0.4 than in v0.1 — Polya's method forced reframing, while the research skill just says "probe the problem."

The next step is a domain where the answer isn't in the training data and a zero-parameter shortcut doesn't exist. Something where the model genuinely has to combine ideas in a way that hasn't been written down. That's where this either proves itself or doesn't.

## What I wish I could do better

The search is still wave-based in some stages. True concurrent tree search, where each spec streams independently and new specs spawn as results land, would be more efficient and produce better coverage.

Compute budget estimation is a guess. The hypothesis requires `max_compute_flops`, but estimating the right FLOP budget for an unknown architecture on an unknown task is itself a problem. A scaling-law pilot (accuracy vs compute doublings) would be the principled approach.

Three experiments across two domains is the start of evidence, not a benchmark. The harness needs a proper benchmark suite across different mathematical domains to make the claims rigorous rather than anecdotal. And the real test — a domain where the answer isn't in the training data — hasn't been run yet.
