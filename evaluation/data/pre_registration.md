# Pre-Registration — Vex Evaluation

> Frozen before the first logged task. Do not modify during the evaluation period.
> If any threshold is changed, the evaluation restarts from zero.

**Date frozen:** 2026-04-03
**Evaluator:** Yusuf Guenena
**Routing mode:** cloud
**Model versions:** Haiku 4.5, Sonnet 4.5 (claude-sonnet-4-5), Opus 4.7 (claude-opus-4-7)

## Frozen routing thresholds

### Confidence

- Confidence < 0.65 -> route directly to tier:3 (Opus), skip lower tiers

### Impact score thresholds

| Downstream files | Impact |
|---|---|
| 0-1 | LOW |
| 2-5 | MEDIUM |
| 6-15 | HIGH |
| 16+ | CRITICAL |

### Risk score thresholds

| Score | Risk |
|---|---|
| 0 | LOW |
| 1-2 | MEDIUM |
| 3-5 | HIGH |
| >=6 | CRITICAL |

### Adaptive routing thresholds

- Minimum 3 data points before overriding default routing
- Success rate < 40% for model+class -> skip that tier
- Success rate > 80% for model+class -> prefer that tier at slightly higher risk

### Cloud routing table (frozen)

| | Low risk | Med risk | High+ risk |
|---|---|---|---|
| TRIVIAL | Haiku | Haiku | Haiku |
| MECHANICAL | Haiku | Haiku | Sonnet |
| SINGLE_FILE | Haiku | Sonnet | Sonnet |
| MULTI_FILE | Sonnet | Opus | Opus |
| REFACTOR | Sonnet | Sonnet | Opus |
| ARCHITECTURAL | Opus | Opus | Opus |
| DEBUGGING | Sonnet | Opus | Opus |

### Hard overrides (always tier:3)

- Confidence < 0.65
- Impact or risk = CRITICAL
- ARCHITECTURAL or RESEARCH tasks

## Primary metric

**Cost savings vs. Opus-only baseline** (percentage), reported alongside quality pass rate.

This is the headline number. It will be reported as: "In this evaluation of N tasks over M days, routing reduced estimated cost by X% compared to an Opus-only baseline."

## Secondary metrics

- Mean quality score (1-5 rubric)
- Pass rate (score >= 3)
- Rework rate
- Classification accuracy (% of tasks where assigned class was correct)
- Routing agreement with manual pick

## Exclusion criteria

A task is loggable if:
- It was a coding instruction given to Claude Code
- Vex routing was active during the task
- The task was non-trivial (not "what does this function do?")

A task is NOT loggable if:
- Routing was manually overridden before execution
- The task was conversational, not coding
- The task was outside of code (email, research unrelated to code)

## Falsification criteria

The evaluation concludes that routing **does not deliver sufficient value** if ANY of:
- Mean quality score drops below 3.5/5
- Rework rate exceeds 25%
- Cost savings vs. Opus baseline are under 15%
- Classification accuracy is below 70%
- The evaluator overrides the router on more than 15% of tasks

If routing only beats the Opus-only baseline but does not beat manual model selection (measured via manual_pick field), the conclusion is that the router adds complexity without value beyond what the user would do anyway.

## Minimum evidence thresholds

| Level | Tasks | Claim strength |
|---|---|---|
| Anecdotal | < 20 | "Here's what happened" only |
| Preliminary | 20-49 | "Early signal suggests..." with heavy caveats |
| Credible | 50-99 | Per-class rates reportable; cost comparison meaningful |
| Strong | 100+ | Patterns across task classes reliable |

Per-class minimum: 5 entries before reporting class-specific metrics.
Minimum duration: 2 weeks of regular usage.
