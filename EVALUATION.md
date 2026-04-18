# Evaluation Plan

> **Status: Evaluation not started.** The evaluation framework is ready but no data has been collected. Zero tasks have been logged. This document describes how to evaluate Vex, not results that have been collected.

## Evaluation framework

The `evaluation/` directory contains everything needed to run a credible single-user evaluation:

```
evaluation/
├── METHODOLOGY.md           # Study design, metrics, threats to validity
├── SCORING_RUBRIC.md         # 1-5 quality scoring rubric with criteria
├── EXPERIMENT_PROTOCOL.md    # Daily workflow for logging tasks
├── RESULTS_TEMPLATE.md       # Template for publishing findings
├── scripts/
│   ├── analyze.py            # Summary statistics from eval log
│   └── log_task.sh           # Interactive helper to log entries
├── examples/
│   └── sample_eval_log.jsonl # Example entries (SAMPLE DATA, not real)
└── data/
    ├── eval_log.jsonl        # Your real evaluation log (gitignored)
    ├── weekly_notes.md       # Weekly observations (gitignored)
    └── environment.md        # Your setup details (gitignored)
```

## Quick start

1. Read `evaluation/EXPERIMENT_PROTOCOL.md` for the daily workflow
2. Read `evaluation/SCORING_RUBRIC.md` to understand scoring criteria
3. Start logging tasks to `evaluation/data/eval_log.jsonl`
4. Run `python3 evaluation/scripts/analyze.py evaluation/data/eval_log.jsonl` weekly
5. After 50+ tasks, fill in `evaluation/RESULTS_TEMPLATE.md`

## What needs to be measured

### 1. Cost reduction

**Question:** Does routing to cheaper tiers actually reduce total spend?

**Method:**
- Log every task during the evaluation period with token counts
- Compare actual cost against an Opus-only baseline
- Track cost by tier and by task class

**Metrics:**
- Total tokens consumed (by tier)
- Total estimated cost (using published API pricing)
- Savings percentage vs. Opus-only baseline

**Caveat:** The Opus-only baseline overstates savings. A fairer comparison is against manual model selection — the evaluation log captures this via the `manual_pick` field.

### 2. Quality preservation

**Question:** Do tasks routed to cheaper tiers produce equivalent results?

**Method:**
- Score every task output 1-5 using the rubric in `evaluation/SCORING_RUBRIC.md`
- Track rework frequency and severity
- Compare quality scores across tiers

**Metrics:**
- Success rate per tier per task class
- Mean quality score by tier
- Rework rate and severity distribution

### 3. Routing accuracy

**Question:** Does the classification system correctly assess task complexity?

**Method:**
- After each task, mark whether the classification was correct
- Track escalation rates and outcomes
- Compare routed model vs. manual pick

**Metrics:**
- Classification accuracy vs. human judgment
- Escalation rate and escalation success rate
- Routing agreement with manual model selection

### 4. Output compression savings

**Question:** How much output-token cost do the `/vex terse` and `/vex caveman` modes (Step 10) actually save?

**Method:**
- Run `evaluation/scripts/measure_compression.py`, which feeds each prompt in `evaluation/compression_prompts.jsonl` through the Anthropic API in normal, terse, and caveman modes
- The script simulates each mode via a system-prompt instruction and records input/output tokens per call
- Results are written to `evaluation/data/compression_results.jsonl` (gitignored) with a summary table printed to stdout

**Metrics:**
- Average and total output tokens per mode
- Estimated total cost per mode (using the pricing table inside the script — verify against current Anthropic pricing before quoting)
- Savings percentage vs. normal, overall and per task class

**Caveats:**
- Measures prompt-simulated compliance via the API, NOT whether Claude Code reliably honors the slash commands in a real session. A separate in-session audit is needed for that.
- Output-token savings only. Tool-call arguments, file writes via Edit/Write, and code produced by the skill are unaffected.
- Variance is high for small prompt sets. Use `--runs N` with N >= 3 before reporting a number.

**Usage:**
```
export ANTHROPIC_API_KEY=...
python3 evaluation/scripts/measure_compression.py --runs 3
```

### 5. Escalation effectiveness

**Question:** When a lower tier fails and escalates, does the next tier recover?

**Method:**
- Log the full escalation chain for every task
- Track whether escalated tasks ultimately succeed

**Metrics:**
- Escalation success rate
- Cost of failed attempts before successful escalation
- Task classes most likely to require escalation

## What would make this credible

- 50+ logged routing decisions across diverse task types
- Minimum 5 entries per task class before reporting class-specific metrics
- Measured cost comparison against Opus-only baseline
- Quality scores assigned using the rubric, not gut feeling
- Threats to validity section completed honestly
- All data published alongside claims (JSONL log available)
- Independent replication by someone other than the author

## What data is real vs. sample

- `evaluation/examples/sample_eval_log.jsonl` — **SAMPLE DATA**, fabricated to show the log format
- `evaluation/data/eval_log.jsonl` — **REAL DATA**, your actual evaluation entries (gitignored)
- `examples/routing_log_example.jsonl` — **SAMPLE DATA**, fabricated routing log entries

**Nothing in this repository constitutes measured evidence.** All results must come from your own logged evaluation.

## What is still missing (as of 2026-04-03)

Before findings can be published, all of the following must exist:

- [x] `evaluation/data/pre_registration.md` — frozen thresholds, primary metric, exclusion and falsification criteria
- [x] `evaluation/data/environment.md` — machine specs, Claude Code version, model versions, typical codebases and languages
- [ ] 50+ entries in `evaluation/data/eval_log.jsonl` (currently: 0)
- [ ] At least 5 entries per task class for any class-specific claims
- [ ] Minimum 2 weeks of regular usage (currently: 0 days)
- [ ] Weekly notes in `evaluation/data/weekly_notes.md` (currently: blank template)
- [ ] At least one run of `evaluation/scripts/analyze.py` against real data

Until these are met, the repo should not contain a findings section, and no public claims about cost savings, quality, or routing accuracy are supported.
