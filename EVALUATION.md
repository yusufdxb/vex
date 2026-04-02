# Evaluation Plan

> **Status: No results yet.** This document describes how Vex should be evaluated, not results that have been collected.

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

### 4. Escalation effectiveness

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
