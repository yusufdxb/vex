# Experiment Protocol

> How to run the evaluation day-to-day.

## Setup (once)

1. Ensure `evaluation/data/` directory exists
2. Create your evaluation log file: `evaluation/data/eval_log.jsonl`
3. Review `SCORING_RUBRIC.md` so scoring criteria are fresh
4. Note your start date and commit to logging every task for at least 2 weeks
5. Record your environment in `evaluation/data/environment.md`:
   - Machine specs
   - Claude Code version
   - Model versions available
   - Typical codebase(s) you work on
   - Languages used

## Daily workflow

### For each coding task

**Before the task:**

1. Write down what you're about to do (one sentence)
2. Note which task class you think it is
3. Note which model you would have picked manually (this is your "manual baseline")

**During the task:**

4. Let Vex route normally
5. Note the routed model and any escalations
6. Note approximate wall-clock time

**After the task (immediately):**

7. Score the output using `SCORING_RUBRIC.md` (1-5)
8. Note if rework was needed and severity (0=none, 1=cosmetic, 2=functional, 3=redo)
9. Log the entry (see format below)

### Logging a task

Append one line to `evaluation/data/eval_log.jsonl`:

```json
{
  "id": "001",
  "date": "2026-04-02",
  "task_summary": "Fix null check in user validation",
  "task_class": "SINGLE_FILE",
  "task_class_correct": true,
  "confidence": 0.85,
  "risk": "MEDIUM",
  "impact": "LOW",
  "routed_model": "sonnet",
  "manual_pick": "sonnet",
  "escalation_chain": [],
  "tokens_in": 1200,
  "tokens_out": 800,
  "tokens_total": 2000,
  "token_source": "estimated",
  "quality_score": 4,
  "task_success": true,
  "rework_needed": false,
  "rework_severity": 0,
  "wall_clock_seconds": 45,
  "codebase": "my-project",
  "languages": ["python"],
  "notes": ""
}
```

Or use the helper script:

```bash
./evaluation/scripts/log_task.sh
```

### End of day

- Quick scan of today's entries — anything surprising?
- No analysis needed daily. Save analysis for weekly.

## Weekly review (15 minutes)

Run the analysis script:

```bash
python3 evaluation/scripts/analyze.py evaluation/data/eval_log.jsonl
```

Review:
1. Tasks logged this week
2. Distribution across task classes
3. Success rate by tier
4. Cost comparison vs. Opus baseline
5. Any task classes with < 3 entries (need more data)
6. Any surprising escalations or failures

Update `evaluation/data/weekly_notes.md` with a brief paragraph.

## Field definitions

| Field | Type | Description |
|---|---|---|
| `id` | string | Sequential task ID ("001", "002", ...) |
| `date` | string | ISO date |
| `task_summary` | string | One-line description of the task |
| `task_class` | string | Vex classification: TRIVIAL, MECHANICAL, SINGLE_FILE, MULTI_FILE, REFACTOR, ARCHITECTURAL, DEBUGGING, RESEARCH, INFRASTRUCTURE |
| `task_class_correct` | bool | Post-hoc: was the classification right? |
| `confidence` | float | Vex confidence score (0.0-1.0) |
| `risk` | string | LOW, MEDIUM, HIGH, CRITICAL |
| `impact` | string | LOW, MEDIUM, HIGH, CRITICAL |
| `routed_model` | string | Model that handled the task (final model if escalated) |
| `manual_pick` | string | What model you would have chosen without routing |
| `escalation_chain` | array | List of models tried before success, e.g. `["haiku", "sonnet"]` |
| `tokens_in` | int | Input tokens consumed (all attempts) |
| `tokens_out` | int | Output tokens consumed (all attempts) |
| `tokens_total` | int | Total tokens (in + out, all attempts including escalations) |
| `token_source` | string | "exact" (from API) or "estimated" |
| `quality_score` | int | 1-5 per rubric |
| `task_success` | bool | Did the task complete without manual intervention? |
| `rework_needed` | bool | Did output require manual correction? |
| `rework_severity` | int | 0=none, 1=cosmetic, 2=functional, 3=redo |
| `wall_clock_seconds` | int | Approximate time from start to done |
| `codebase` | string | Which project/repo this task was in |
| `languages` | array | Languages involved |
| `notes` | string | Anything notable — failure reasons, surprises |

## What counts as a task

Log a task if:
- You gave Claude Code a coding instruction
- The instruction could plausibly have been routed by Vex
- The task took more than a trivial interaction (not "what does this function do?")

Do NOT log:
- Conversational back-and-forth
- Tasks where you manually overrode routing
- Tasks outside of coding (email, research not related to code)

## Handling edge cases

**Task abandoned mid-way:** Log it with `task_success: false`, `quality_score: 1`, note "abandoned"

**Multiple escalations:** Log the full chain: `"escalation_chain": ["haiku", "sonnet"]` means haiku failed, sonnet failed, final model (opus) succeeded.

**You forgot to log immediately:** Log it anyway with a note "logged retroactively" — imperfect data is better than missing data.

**Routing was clearly wrong:** Log it, mark `task_class_correct: false`, note what the correct class should have been.

**Vex wasn't active:** Don't log it. Only log tasks where Vex routing was in effect.
