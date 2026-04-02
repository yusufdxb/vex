# Escalation Playbook

## Cloud Mode Escalation Ladder

```
Tier 1: Haiku   (fast, cheap — trivial tasks)
Tier 2: Sonnet  (balanced — standard dev work)
Tier 3: Opus    (full power — takes over completely)
```

Max retries per tier: 2 (Tier 1–2), then escalate
Total escalation budget: 2 tiers before Opus takes over

## Hybrid Mode Escalation Ladder

```
Tier 1: ollama:small   (your configured small model)
Tier 2: ollama:medium  (your configured medium model)
Tier 3: ollama:large   (your configured large model)
Tier 4: claude:full    (current Claude session)
```

Max retries per tier: 2 (Tier 1–3), then escalate
Total escalation budget: 3 tiers before forcing Claude

## Failure Detection

After every model output, check:

```python
FAIL_SIGNALS = [
    "error:", "Error:", "ERROR:",
    "SyntaxError", "IndentationError",
    "undefined reference", "undeclared identifier",
    "fatal:", "FAILED", "exception",
    "Traceback (most recent call last)",
    "I'm not sure", "I cannot", "I don't have enough context",
    "I apologize",
]

def detect_failure(output: str, exit_code: int) -> bool:
    if exit_code != 0:
        return True
    if not output.strip():
        return True  # empty output = likely failure
    for sig in FAIL_SIGNALS:
        if sig in output:
            return True
    return False

def detect_corrupt_patch(diff: str) -> bool:
    lines = diff.count('\n')
    if lines > 500:
        return True  # suspiciously large, verify manually
    if not diff.strip():
        return True  # no-op patch
    return False
```

## Per-Tier Recovery Protocol

### Cloud Mode

#### Haiku → Sonnet failure
- Log: what task was sent, what the failure was
- Don't just retry — Sonnet can reason about *why* Haiku failed
- Provide the Haiku output as context: "Previous attempt produced: [error]"
- Sonnet has more reasoning capacity — it may take a different approach entirely

#### Sonnet → Opus failure
- Opus takes over completely — don't pass Sonnet's partial work
- Run `git stash && git checkout -- .` if any partial changes were made (see Post-Corruption Recovery for safety notes)
- Opus reads the failure output, diagnoses root cause, executes directly
- Classify as ARCHITECTURAL or escalated DEBUGGING

### Hybrid Mode

#### Tier 1 → 2 failure
- Log: what prompt was sent, what the failure was
- Do NOT just re-run the same prompt
- Add to next prompt: "Previous attempt failed with: [error]. Avoid this approach."
- Increase context: provide more of the surrounding code

#### Tier 2 → 3 failure
- Switch to your configured large model
- Add explicit constraints: "Output ONLY the modified function. No prose. No explanation."
- If debugging: add the full error traceback to prompt

#### Tier 3 → Claude failure
- Don't pass the Ollama output to Claude — start fresh
- Run `git stash && git checkout -- .` if any partial changes were made (see Post-Corruption Recovery for safety notes)
- Give Claude the original task + any diagnostic info from failed attempts

## Post-Corruption Recovery

> **Warning:** `git checkout -- .` discards **all** unstaged changes in the working tree, not just changes from the failed task. If you have other uncommitted work, it will be lost. Consider using `git stash` first, or limit the revert to specific files with `git checkout -- <file>`.

If any patch breaks the build:
```bash
git diff --stat              # see what changed
git stash                    # save all changes (staged + unstaged) before reverting
git checkout -- .            # revert all unstaged changes
# Run your project's build command to verify clean state
# If the build is clean, selectively restore non-task changes:
# git stash pop
```

Never proceed with a broken build state. Always verify clean before retrying.
