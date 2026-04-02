# Evaluation Methodology

> **Status: Framework only.** No results have been collected yet. Everything below describes how to collect credible evidence, not evidence itself.

## What this evaluation can and cannot show

### Can show (with sufficient data)

- Whether routing reduces token usage and estimated cost for **one user's workload**
- Whether lower-tier success rates match, exceed, or fall short of bootstrap estimates
- Whether escalation recovers failed tasks at an acceptable rate
- Which task classes benefit from routing and which do not
- Whether routing decisions correlate with task complexity as judged post-hoc

### Cannot show (regardless of data volume)

- That Vex saves money "in general" or "for most users"
- That routing is better than a skilled user manually choosing models
- That the quality metric captures everything that matters
- Anything about hybrid/Ollama mode unless hybrid tasks are logged
- Causal claims — only correlational observations from a single-user sample

## Pre-registration

Before starting data collection, freeze the following and do not change them during the evaluation period:

1. **Routing thresholds** — the confidence, risk, and impact cutoffs in SKILL.md
2. **Primary metric** — what you will report as the headline number (declare it now)
3. **Exclusion criteria** — what counts as a loggable task and what doesn't (define before, not after)
4. **Falsification criteria** — what result would cause you to conclude routing doesn't work?

Example falsification: "If quality score mean drops below 3.5, or rework rate exceeds 25%, or cost savings are under 15% vs. Opus baseline, routing is not delivering enough value to justify its complexity."

Write these in `evaluation/data/pre_registration.md` before your first logged task. If you adjust thresholds mid-evaluation, the evaluation restarts from zero.

## Study design

### Type

Observational, single-subject, within-subject comparison.

This is **not** a controlled experiment. There is no randomization, no blinding, and no control group running simultaneously. The baseline is reconstructed, not observed.

### Baseline construction

The cost baseline is: "What would this task have cost if routed to Opus every time?"

```
baseline_cost = sum(estimated_opus_tokens * opus_price_per_token for each task)
actual_cost   = sum(actual_tokens * actual_model_price_per_token for each task)
savings       = (baseline_cost - actual_cost) / baseline_cost
```

**Why Opus-only baseline:** It's the simplest to compute. However, **it is a straw man**. No reasonable user sends every trivial request to Opus. The real question is whether routing beats what a competent user would do manually — and that is a much harder bar.

**The `manual_pick` field exists for this reason.** Before each task, record what model you would have chosen yourself. This enables a second, stronger comparison: routing vs. manual selection. If routing only beats always-Opus but doesn't beat your own judgment, the router's value is questionable.

**Report both baselines.** The Opus baseline shows the upper bound of possible savings. The manual-pick comparison shows whether routing adds value beyond what you'd do anyway.

### Sample size targets

| Evidence level | Tasks logged | Claim strength |
|---|---|---|
| Anecdotal | < 20 | "Here's what happened" — no generalizable claims |
| Preliminary | 20-49 | "Early signal suggests..." with heavy caveats |
| Credible | 50-99 | Per-class success rates reportable; cost comparison meaningful |
| Strong | 100+ | Patterns across task classes; escalation rate reliable |

**Per-class minimums:** Do not report success rates for a task class with fewer than 5 entries. Do not draw conclusions from fewer than 10.

### Duration

Minimum 2 weeks of regular usage. Single-day evaluations are not credible because task mix varies by day.

## Metrics

### 1. Cost metrics

| Metric | Source | Unit |
|---|---|---|
| Tokens consumed (input + output) | API response or estimate | tokens |
| Estimated cost | tokens * published price | USD |
| Cost by tier | group by model | USD |
| Baseline cost (Opus-only) | task count * estimated Opus tokens * Opus price | USD |
| Savings rate | (baseline - actual) / baseline | percentage |

**Token estimation:** When exact API token counts aren't available, estimate: `(file_lines * 15) + 500 overhead + 200 per file`. Log whether the count is exact or estimated.

**Pricing (as of 2026-04):**

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|---|---|---|
| Haiku 4.5 | $0.80 | $4.00 |
| Sonnet 4.5 | $3.00 | $15.00 |
| Opus 4.6 | $15.00 | $75.00 |

Update these when prices change. The analysis script reads them from a config section.

### 2. Quality metrics

See `SCORING_RUBRIC.md` for the full rubric.

| Metric | How measured |
|---|---|
| Task success (binary) | Did the task complete without errors? |
| Quality score (1-5) | Post-hoc human rating |
| Rework needed (binary) | Did the output require manual correction? |
| Rework severity (1-3) | 1=cosmetic, 2=functional fix, 3=redo from scratch |

### 3. Routing metrics

| Metric | How measured |
|---|---|
| Classification accuracy | Post-hoc: was the assigned class correct? |
| Confidence calibration | Do 0.8-confidence tasks succeed ~80% of the time? |
| Escalation rate | % of tasks that required escalation |
| Escalation success rate | % of escalated tasks that succeeded after escalation |
| Misroute rate | % of tasks where a different tier would have been clearly better |

### 4. Latency metrics

| Metric | How measured |
|---|---|
| Time to completion | Wall clock from task start to done |
| Escalation overhead | Extra time spent on failed attempts before escalation |

Latency is secondary — log it when convenient, don't stress about precision.

## Threats to validity

### Internal validity

| Threat | Description | Mitigation |
|---|---|---|
| **Confirmation bias** | Scoring quality more leniently for routed tasks because you want it to work | Use the rubric strictly. Score before checking which tier handled it, if possible |
| **Selection bias** | Unconsciously giving routing "easy" tasks | Log ALL tasks during the evaluation period, not just ones that seem suitable |
| **Learning effect** | Getting better at writing prompts over the evaluation period | Acknowledged as unavoidable. Note if prompt style changes |
| **Rework invisibility** | Small manual fixes not logged as rework | Be strict: any manual edit to routed output counts as rework |
| **Survivorship bias** | Failed tasks abandoned and never logged | Log every task attempt, including failures and abandons |
| **Trivial task inflation** | If 70% of tasks are trivial, volume-weighted cost savings are large but meaningless — the savings on trivial tasks are real but tiny in absolute terms, and they obscure quality on hard tasks where model choice matters | Report savings broken down by task class. Report both volume-weighted and difficulty-weighted results |
| **Post-hoc threshold tuning** | Adjusting routing thresholds after seeing results is fitting to noise | Freeze thresholds before evaluation (see Pre-registration). If adjusted, restart the evaluation |
| **Prompt adaptation** | Re-phrasing prompts when you suspect wrong routing, turning one task into two | Count re-prompts as rework. Log the original prompt, not just the successful one |

### External validity

| Threat | Description | Mitigation |
|---|---|---|
| **Single user** | One person's task mix, codebase, and prompting style | Do not generalize beyond "for this user, on these tasks" |
| **Single codebase** | Results may not transfer to different languages/architectures | State the languages and repo characteristics |
| **Time period** | Model capabilities change; prices change | Pin the evaluation to specific model versions and dates |
| **Task distribution** | Your task mix may not represent typical development work | Report the distribution; let readers judge relevance |

### Construct validity

| Threat | Description | Mitigation |
|---|---|---|
| **Quality is subjective** | 1-5 scores depend on the rater | Use a concrete rubric with examples |
| **"Success" is binary but quality isn't** | A task that "works" may be mediocre | Score both success (binary) and quality (1-5) |
| **Token count != cost** | Input and output tokens have different prices | Track both separately where possible |
| **Opus baseline is artificial** | Nobody actually uses Opus for everything | Report savings against Opus baseline but note the limitation |

## What to report and what to avoid

### Acceptable claims (with 50+ tasks)

- "In my evaluation of N tasks over M days, routing reduced estimated cost by X% compared to an Opus-only baseline"
- "Lower-tier success rates for [class] were Y% (N=Z), compared to a bootstrap estimate of W%"
- "Escalation was triggered in X% of cases and succeeded Y% of the time"
- "The strongest cost savings were in [class] tasks; routing provided no benefit for [class] tasks"

### Claims that are NEVER valid from this evaluation

- "Vex saves X% for all users"
- "Routing is better than manual model selection"
- "Quality is equivalent across tiers" (would require blinded evaluation by multiple raters)
- "Vex is production-ready"
- Anything implying statistical significance from a single-user observational study

### Language to use

- "In this evaluation..." not "Vex achieves..."
- "For this user's workload..." not "In general..."
- "Preliminary findings suggest..." not "Results show..."
- "N tasks observed" not "N tasks tested"

### Language to avoid

- "Statistically significant" (inappropriate for this study design)
- "Proves" or "demonstrates" (too strong)
- "Consistently" (unless literally 100%)
- "Users can expect..." (no basis for generalization)
- "Benchmark" (implies rigor this design cannot provide)
- "No quality loss" (unmeasurable with unblinded single-rater design)
- "Optimal" (not tested against alternative routing strategies)

## The honest ceiling

The strongest claim a 2-week single-user evaluation can support:

> "In my specific usage over this period, the router's decisions seemed reasonable to me, quality scores stayed above [threshold], and my estimated API cost was [X]% lower than it would have been using Opus for everything."

That is it. Everything beyond this requires either more data, more users, or a different study design.

## Handling negative results

If routing degrades quality on complex tasks, this is the most important finding and must be the headline — not buried beneath cost savings on trivial tasks.

If you override the router more than ~15% of the time, the router is not working and the benefit comes from the overrides, not the routing.

If cost savings are only significant on trivial tasks, say so. Do not report aggregate savings that are driven entirely by the trivial task volume.

Never rationalize negative results away. "The router failed here because X" is fine for diagnosis but does not erase the failure from the record.
