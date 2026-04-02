# Task Quality Scoring Rubric

## Quick reference

| Score | Label | Meaning |
|---|---|---|
| 5 | Excellent | Correct, complete, clean — no changes needed |
| 4 | Good | Correct and complete with minor style issues — would accept as-is |
| 3 | Acceptable | Works but has noticeable issues — minor rework needed |
| 2 | Poor | Partially works or has significant issues — substantial rework needed |
| 1 | Failed | Wrong, broken, or unusable — must redo from scratch |

## Detailed criteria

### Score 5 — Excellent

- Code compiles/runs without errors
- All requirements of the task are addressed
- Edge cases handled appropriately
- Code style matches the project
- No unnecessary changes or additions
- Tests pass (if applicable)

### Score 4 — Good

- Code compiles/runs without errors
- All requirements addressed
- Minor style inconsistencies (naming, formatting)
- Slightly verbose or could be cleaner
- You'd accept it in a code review without requesting changes

### Score 3 — Acceptable

- Code compiles/runs
- Core requirement met but with gaps
- Missing an edge case that matters
- Needs a small manual fix (1-5 lines)
- Acceptable but you'd request changes in review

### Score 2 — Poor

- Code has functional issues
- Partially addresses the task
- Significant logic errors or missing functionality
- Needs substantial rework (5-20 lines of changes)
- Would not accept in code review

### Score 1 — Failed

- Code doesn't compile/run
- Wrong approach entirely
- Breaks existing functionality
- Must be redone from scratch
- Output is empty, garbled, or irrelevant

## Pass/fail threshold

- **Pass:** Score >= 3 (task is usable, even if imperfect)
- **Fail:** Score <= 2 (task requires significant intervention)

## Rework severity

When rework is needed, classify it:

| Severity | Description | Examples |
|---|---|---|
| 1 — Cosmetic | Style, naming, whitespace | Rename a variable, fix indentation |
| 2 — Functional | Logic fix or missing piece | Add a null check, fix off-by-one |
| 3 — Redo | Fundamental approach wrong | Wrong algorithm, wrong file, broken architecture |

## Scoring guidelines

- Score the **output**, not the **effort**. A task that required 3 escalations but produced a score-5 result is still score 5.
- Score relative to what you asked for, not what you wish you'd asked for.
- Score immediately after the task completes, before you start fixing things.
- If a task was abandoned (you gave up and did it yourself), score it 1.
- If a task required escalation, score the **final output** from the last model that handled it.

## Task class expectations

Different task classes have different quality bars. A score of 3 means different things for different classes:

| Class | Score 3 means... |
|---|---|
| TRIVIAL | Should almost never happen — if it does, routing is wrong |
| MECHANICAL | Acceptable — boilerplate with a small fix needed |
| SINGLE_FILE | Normal — function works but needs a tweak |
| MULTI_FILE | Normal — most files correct, one needs adjustment |
| REFACTOR | Concerning — refactors need to be clean |
| DEBUGGING | Normal — root cause found but fix is incomplete |
| RESEARCH | Normal — explanation is correct but misses nuance |
| INFRASTRUCTURE | Concerning — config files must be exact |
| ARCHITECTURAL | Concerning — design decisions shouldn't be "acceptable" |
