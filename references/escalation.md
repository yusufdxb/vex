# Escalation Playbook

## Escalation Ladder

```
Tier 1: ollama:small   (your configured small model)
Tier 2: ollama:medium  (your configured medium model)
Tier 3: ollama:large   (your configured large model)
Tier 4: claude:full    (current Claude session)
```

Max retries per tier: 2 (Tier 1–3), then escalate
Total escalation budget: 3 tiers before forcing Claude

## Failure Detection

After every Ollama output, check:

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

### Tier 1 → 2 failure
- Log: what prompt was sent, what the failure was
- Do NOT just re-run the same prompt
- Add to next prompt: "Previous attempt failed with: [error]. Avoid this approach."
- Increase context: provide more of the surrounding code

### Tier 2 → 3 failure
- Switch to your configured large model
- Add explicit constraints: "Output ONLY the modified function. No prose. No explanation."
- If debugging: add the full error traceback to prompt

### Tier 3 → 4 failure (→ Claude)
- Don't pass the Ollama output to Claude — start fresh
- Run `git checkout -- .` if any partial changes were made
- Give Claude the original task + any diagnostic info from failed attempts

## Post-Corruption Recovery

If any patch breaks the build:
```bash
git diff --stat              # see what changed
git checkout -- .            # revert all unstaged changes
git stash                    # if changes were staged
# Run your project's build command to verify clean state
```

Never proceed with a broken build state. Always verify clean before retrying.
