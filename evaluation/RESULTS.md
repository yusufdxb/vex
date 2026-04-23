# Vex Evaluation Results

> **Status:** PRELIMINARY
> **Period:** 2026-04-07 to 2026-04-23
> **Tasks logged:** 60
> **Evaluator:** Yusuf Guenena
> **Codebase(s):** come-here, helix, odin, vex, go2-phoenix, BlackBoxRS, GO2-seeing-eye-dog
> **Languages:** Python, C++, YAML, Markdown, Bash, CMake
> **Model versions:** Haiku 4.5, Sonnet 4.6, Opus 4.7

## Important disclaimers

- This is a single-user observational evaluation, not a controlled experiment
- Quality scores are subjective ratings by the evaluator using a fixed rubric
- Cost savings are calculated against an Opus-only baseline, which overstates savings compared to manual model selection
- Results apply to this specific user, codebase, and task mix — do not generalize
- All 60 tasks were actually run on Opus (Claude Code default). The "Vex-routed" and "manual-pick" costs are reconstructed baselines, not observed
- Token counts are estimated (line count * 15 + overhead), not exact API values
- Tasks were back-filled from git history, not logged in real-time — quality scores and manual picks are retrospective judgments

## Summary

In this evaluation of 60 tasks over 8 days across 7 codebases, Vex routing would have saved an estimated 44% vs. the Opus-only baseline ($12.03 vs. $21.50). Vex also narrowly beats the evaluator's manual model selection by 6.1% ($0.78), suggesting the router adds marginal value beyond what the user would do anyway. The main quality risk is that Vex over-routes LOW-risk SINGLE_FILE tasks to Haiku — 16 tasks that the evaluator would have sent to Sonnet.

## Cost metrics

| Metric | Value |
|---|---|
| Total tasks | 60 |
| Total tokens consumed | 603,500 |
| Estimated actual cost (all Opus) | $21.50 |
| Estimated Vex-routed cost | $12.03 |
| Estimated manual-pick cost | $12.81 |
| Savings vs. Opus baseline | 44% |
| Savings vs. manual pick | 6.1% |

### Cost by tier (Vex-routed)

| Tier | Tasks | % of tasks | Tokens | Est. cost |
|---|---|---|---|---|
| Haiku | 25 | 42% | 173,000 | $0.83 |
| Sonnet | 15 | 25% | 138,500 | $2.49 |
| Opus | 20 | 33% | 292,000 | $8.71 |
| **Total** | **60** | **100%** | **603,500** | **$12.03** |

### Cost by task class

| Task class | N | Avg tokens | Opus cost | Vex cost | Savings |
|---|---|---|---|---|---|
| TRIVIAL | 7 | 3,429 | $1.07 | $0.12 | 89% |
| MECHANICAL | 5 | 7,200 | $1.61 | $0.17 | 89% |
| SINGLE_FILE | 25 | 8,300 | $9.27 | $2.59 | 72% |
| MULTI_FILE | 6 | 16,500 | $4.42 | $3.75 | 15% |
| DEBUGGING | 7 | 11,429 | $3.57 | $2.38 | 33% |
| RESEARCH | 6 | 10,833 | $2.90 | $2.90 | 0% |
| REFACTOR | 2 | 23,500 | $2.10 | $1.30 | 38% |
| INFRASTRUCTURE | 1 | 8,000 | $0.36 | $0.07 | 81% |
| ARCHITECTURAL | 1 | 37,000 | $1.66 | $1.66 | 0% |

## Quality metrics

### Overall

| Metric | Value |
|---|---|
| Mean quality score | 4.85/5 |
| Median quality score | 5/5 |
| Pass rate (score >= 3) | 100% |
| Tasks requiring rework | 5% (3/60) |

### Quality by task class

| Task class | N | Mean score | Rework | Notes |
|---|---|---|---|---|
| TRIVIAL | 7 | 5.00 | 0% | |
| MECHANICAL | 5 | 5.00 | 0% | |
| SINGLE_FILE | 25 | 4.92 | 4% | 1 task needed cosmetic rework |
| MULTI_FILE | 6 | 4.67 | 17% | 1 task needed functional rework (CI follow-ups) |
| DEBUGGING | 7 | 4.43 | 0% | Lowest mean — hardware debugging is hard |
| RESEARCH | 6 | 5.00 | 0% | |
| REFACTOR | 2 | 4.50 | 0% | Insufficient data |
| INFRASTRUCTURE | 1 | 5.00 | 0% | Insufficient data |
| ARCHITECTURAL | 1 | 5.00 | 0% | Insufficient data |

## Routing accuracy

| Metric | Value |
|---|---|
| Classification accuracy | 100% (60/60) |
| Escalation rate | 0% (no escalations — all ran on Opus) |
| Matched manual pick | 33% (20/60) |
| Vex downgrade risk | 27% (16/60 tasks where Vex picks weaker than manual) |

### Routing agreement

| Comparison | Haiku | Sonnet | Opus |
|---|---|---|---|
| **Manual pick** | 11 (18%) | 29 (48%) | 20 (33%) |
| **Vex routing** | 25 (42%) | 15 (25%) | 20 (33%) |

Vex routes 14 more tasks to Haiku and 14 fewer to Sonnet than the evaluator would. Agreement on Opus routing is perfect — both the evaluator and Vex agree on which tasks need full power.

### Downgrade analysis

16 tasks where Vex picks a weaker tier than the evaluator's manual pick:

- **14 of 16** are SINGLE_FILE/LOW routed to Haiku instead of Sonnet. These include implementing ROS nodes, writing test suites, and creating protocol stubs — tasks where Haiku's literal execution style may produce incorrect output.
- **2 of 16** are SINGLE_FILE/MEDIUM routed to Sonnet instead of Opus. Both involve wiring ROS nodes with external services (LLM, hardware) where the evaluator wanted Opus for correctness.

## Measured tier success rates (45 cloud + 60 hybrid calls)

Measured 2026-04-23 using `evaluation/scripts/measure_routing.py` — 15 coding prompts spanning all 9 task classes, sent to each tier via `claude -p` (cloud) and `ollama run` (hybrid).

### Cloud mode (15 prompts × 3 tiers = 45 calls)

| Tier | Success rate | Cost (15 prompts) |
|---|---|---|
| Haiku 4.5 | 15/15 (100%) | $0.065 |
| Sonnet 4.6 | 15/15 (100%) | $0.146 |
| Opus 4.7 | 15/15 (100%) | $0.836 |

Haiku is **13x cheaper** than Opus for identical results on these prompts.

### Hybrid mode (15 prompts × 4 tiers = 60 calls)

| Tier | Model | Success rate | Cost |
|---|---|---|---|
| ollama:small | qwen2.5-coder:latest (7b) | 15/15 (100%) | $0 (local) |
| ollama:medium | qwen2.5-coder:14b | 15/15 (100%) | $0 (local) |
| ollama:large | deepseek-coder-v2:16b | 15/15 (100%) | $0 (local) |
| Haiku (baseline) | claude-haiku-4-5 | 15/15 (100%) | $0.076 |

All three Ollama models match Haiku on these prompts at zero API cost.

### Per-class success (cloud tiers)

| Class | Haiku | Sonnet | Opus |
|---|---|---|---|
| TRIVIAL | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| MECHANICAL | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| SINGLE_FILE | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| DEBUGGING | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| MULTI_FILE | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |
| REFACTOR | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |
| RESEARCH | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |
| ARCHITECTURAL | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |
| INFRASTRUCTURE | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |

### Simulated escalation

| Metric | Value |
|---|---|
| Direct success (first tier) | 15/15 (100%) |
| Escalation needed | 0/15 (0%) |
| All tiers failed | 0/15 (0%) |

### Caveat

These prompts are self-contained, short-context coding tasks. All models handled them successfully, which means the prompts are **too easy to differentiate tiers**. Real routing failures occur on ambiguous, multi-step, context-heavy tasks that require tool use and cross-file reasoning — those cannot be simulated with `claude -p` (no tool access). The cost data (13x cheaper for identical results) is the stronger finding. Success rate differentiation requires real in-session routing data.

## Where routing helped

- **TRIVIAL tasks** (7 tasks, 89% savings): Haiku handles renames, one-line fixes, and doc updates trivially. No quality risk.
- **MECHANICAL tasks** (5 tasks, 89% savings): Config generation, lint fixes, CI boilerplate — Haiku sufficient.
- **INFRASTRUCTURE** (1 task, 81% savings): CI pipeline work routes to Sonnet, which handles YAML/workflow files well.

## Where routing failed or didn't help

- **RESEARCH tasks** (6 tasks, 0% savings): All route to Opus, which is correct — spec and design work needs full reasoning. No savings possible here.
- **SINGLE_FILE/LOW** (16 tasks over-routed to Haiku): The routing table sends LOW-risk single-file tasks to Haiku, but many of these are non-trivial implementations (ROS nodes, protocol patterns, test suites). Haiku is too literal for tasks requiring design judgment. **Recommendation: route SINGLE_FILE/LOW to Sonnet.**

## Observations

1. **Opus agreement is the bright spot.** Both the evaluator and Vex agree on which tasks need Opus. The router's value is not in escalating to Opus — it's in knowing when NOT to use Opus.

2. **The real competition is Haiku vs. Sonnet**, not Sonnet vs. Opus. The evaluator almost never picks Haiku for SINGLE_FILE (0 manual picks), but Vex routes 14 SINGLE_FILE tasks there. This is the largest disagreement.

3. **Quality is high across the board** (4.85/5 mean), but this evaluation ran everything on Opus. The real test is whether Haiku/Sonnet maintain this quality on their routed tasks. This cannot be answered from reconstructed baselines.

4. **DEBUGGING is the hardest class** (4.43/5 mean even on Opus). Routing DEBUGGING/LOW to Sonnet is correct — Sonnet handles straightforward debug tasks — but DEBUGGING/MEDIUM+ should stay on Opus.

5. **Task mix is SINGLE_FILE-heavy** (42%). This matches typical development work but means SINGLE_FILE routing accuracy disproportionately affects overall savings.

## Recommendations

1. **SINGLE_FILE/LOW now routes to Sonnet** (changed in this evaluation). The previous Haiku routing was the largest quality risk. This reduces estimated savings from 44% to ~38% but eliminates 14 downgrade cases.

2. **Hybrid mode is viable for TRIVIAL and MECHANICAL tasks.** All three Ollama models (7b, 14b, 16b) scored 100% on these classes at zero API cost. For users with a local GPU, offloading TRIVIAL/MECHANICAL to `ollama:small` is a free win.

3. **Harder prompts needed.** The current measurement prompts are too easy — all tiers score 100%. Real tier differentiation requires multi-file, tool-using, context-heavy tasks that can only be measured through in-session routing with `quick_log.sh`.

4. **Collect real routing data.** This evaluation is partly reconstructed (cost/quality from git history) and partly measured (tier success rates from `measure_routing.py`). The next step is real in-session routing with actual Haiku/Sonnet task outcomes.

## Raw data

Full evaluation log: `evaluation/data/eval_log.jsonl` (gitignored — 60 entries)
Routing measurement: `evaluation/data/routing_results.jsonl` (45 cloud calls)
Hybrid measurement: `evaluation/data/routing_results_hybrid.jsonl` (60 hybrid calls)
Environment: `evaluation/data/environment.md`

---

*This evaluation used the methodology described in `evaluation/METHODOLOGY.md` with quality scoring from `evaluation/SCORING_RUBRIC.md`.*
