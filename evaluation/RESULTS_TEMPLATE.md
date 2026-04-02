# Vex Evaluation Results

> **Status:** [DRAFT / PRELIMINARY / FINAL]
> **Period:** [start date] to [end date]
> **Tasks logged:** [N]
> **Evaluator:** [name]
> **Codebase(s):** [repos used]
> **Languages:** [languages encountered]
> **Model versions:** Haiku 4.5, Sonnet 4.5, Opus 4.6

## Important disclaimers

- This is a single-user observational evaluation, not a controlled experiment
- Quality scores are subjective ratings by the evaluator using a fixed rubric
- Cost savings are calculated against an Opus-only baseline, which overstates savings compared to manual model selection
- Results apply to this specific user, codebase, and task mix — do not generalize
- [Add any additional caveats specific to your evaluation]

## Summary

[2-3 sentences: what happened, what the headline numbers are, what surprised you]

## Cost metrics

| Metric | Value |
|---|---|
| Total tasks | |
| Total tokens consumed | |
| Estimated actual cost | $ |
| Estimated Opus-only baseline cost | $ |
| Estimated savings vs. Opus baseline | % |

### Cost by tier

| Tier | Tasks | Tokens | Est. cost | % of total cost |
|---|---|---|---|---|
| Haiku | | | $ | % |
| Sonnet | | | $ | % |
| Opus | | | $ | % |
| **Total** | | | **$** | **100%** |

### Cost by task class

| Task class | N | Avg tokens | Avg cost | Avg Opus baseline cost | Savings |
|---|---|---|---|---|---|
| TRIVIAL | | | | | |
| MECHANICAL | | | | | |
| SINGLE_FILE | | | | | |
| MULTI_FILE | | | | | |
| REFACTOR | | | | | |
| DEBUGGING | | | | | |
| RESEARCH | | | | | |
| INFRASTRUCTURE | | | | | |
| ARCHITECTURAL | | | | | |

## Quality metrics

### Overall

| Metric | Value |
|---|---|
| Mean quality score | /5 |
| Median quality score | /5 |
| Pass rate (score >= 3) | % |
| Tasks requiring rework | % |

### Quality by tier

| Tier | N | Mean score | Pass rate | Rework rate |
|---|---|---|---|---|
| Haiku | | /5 | % | % |
| Sonnet | | /5 | % | % |
| Opus | | /5 | % | % |

### Quality by task class

| Task class | N | Mean score | Pass rate | Notes |
|---|---|---|---|---|
| TRIVIAL | | | | |
| MECHANICAL | | | | |
| SINGLE_FILE | | | | |
| MULTI_FILE | | | | |
| REFACTOR | | | | |
| DEBUGGING | | | | |
| RESEARCH | | | | |
| INFRASTRUCTURE | | | | |
| ARCHITECTURAL | | | | |

## Routing accuracy

| Metric | Value |
|---|---|
| Classification accuracy | % (N tasks where class was correct) |
| Escalation rate | % |
| Escalation success rate | % (of escalated tasks that eventually succeeded) |
| Misroute rate | % (tasks where a different tier was clearly better) |

### Escalation details

| From | To | Count | Success after escalation |
|---|---|---|---|
| Haiku | Sonnet | | / |
| Haiku | Opus | | / |
| Sonnet | Opus | | / |

## Bootstrap estimate comparison

How did actual success rates compare to the bootstrap estimates in `references/adaptive-routing.md`?

| Task class | Bootstrap (Haiku) | Actual (Haiku) | Bootstrap (Sonnet) | Actual (Sonnet) |
|---|---|---|---|---|
| TRIVIAL | 92% | % (n=) | 97% | % (n=) |
| MECHANICAL | 82% | % (n=) | 94% | % (n=) |
| SINGLE_FILE | 55% | % (n=) | 90% | % (n=) |
| MULTI_FILE | 20% | % (n=) | 82% | % (n=) |
| REFACTOR | 10% | % (n=) | 72% | % (n=) |
| DEBUGGING | 25% | % (n=) | 80% | % (n=) |

## Where routing helped

[List task classes or specific scenarios where routing clearly saved cost without quality loss]

## Where routing failed or didn't help

[List task classes or scenarios where routing caused problems, unnecessary escalations, or no meaningful savings]

## Observations

[Qualitative notes: surprises, patterns, things the routing system gets wrong systematically]

## Recommendations

[Based on these results, what should change in the routing tables, thresholds, or approach?]

## Raw data

Full evaluation log: `evaluation/data/eval_log.jsonl`
Weekly notes: `evaluation/data/weekly_notes.md`
Environment: `evaluation/data/environment.md`

---

*This evaluation used the methodology described in `evaluation/METHODOLOGY.md` with quality scoring from `evaluation/SCORING_RUBRIC.md`.*
