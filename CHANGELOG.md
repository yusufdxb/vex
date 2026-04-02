# Changelog

## v1.3.0 — 2026-04-02

### Evaluation framework

- Added `evaluation/` directory with complete evaluation workflow
- `METHODOLOGY.md`: study design, metrics definitions, threats to validity, minimum evidence thresholds, acceptable vs. invalid claims
- `SCORING_RUBRIC.md`: 1-5 quality scoring rubric with detailed criteria, pass/fail thresholds, rework severity classification
- `EXPERIMENT_PROTOCOL.md`: daily workflow for logging tasks, field definitions, edge case handling
- `RESULTS_TEMPLATE.md`: structured template for publishing findings with required disclaimers
- `scripts/analyze.py`: summary statistics from evaluation log (cost, quality, routing accuracy, per-class breakdown, data quality warnings)
- `scripts/log_task.sh`: interactive helper for appending JSONL log entries
- `examples/sample_eval_log.jsonl`: sample entries showing the evaluation log format (clearly labeled as non-real data)
- Rewrote `EVALUATION.md` to reference the new framework
- Updated README repo structure and evidence section
- Added evaluation data files to `.gitignore`

## v1.2.0 — 2026-04-02

### Public credibility pass

- Rewrote README: removed unsupported claims (40–70% savings, fabricated latency/cost numbers), added explicit experimental status, limitations section, and honest evidence assessment
- Added EVALUATION.md with evaluation plan and benchmark template (no results yet)
- Added examples/routing_log_example.jsonl with sample log entries
- Labeled bootstrap success rates as author estimates, not measured data
- Added safety warnings around `git checkout -- .` in escalation docs — now recommends `git stash` first
- Replaced marketing tone with technical documentation throughout

## v1.1.0 — 2026-03-31

### Dual-mode routing

- Added **Cloud mode**: Opus (mastermind) → Sonnet (workhorse) → Haiku (grunt) routing
- Added **Hybrid mode**: Claude + Ollama local models (original behavior)
- User Configuration block now supports `ROUTING_MODE: cloud | hybrid`
- Separate routing tables, escalation ladders, and bootstrap success rates for each mode
- Adaptive learning log now includes `mode` field
- Professional repo structure: LICENSE, CLAUDE.md, CODE_OF_CONDUCT.md, .gitignore, .gitattributes

## v1.0.0 — 2026-03-31

### Initial release

- 9-step routing system: classify, impact analysis, risk scoring, context estimation, route, execute, token optimization, escalation, adaptive learning
- Configurable Ollama model tiers (small/medium/large) — no hardcoded model names
- Confidence-based routing with automatic Claude escalation below 0.65
- Impact analysis via grep/git for blast radius estimation
- Generalized risk scoring for any tech stack
- 3-tier escalation ladder with 2 retries per tier
- Adaptive learning via routing_log.jsonl with automatic threshold adjustment
- Token optimization reference guide
- `/vex` command for manual routing audits (originally named `/smart-routing`)
