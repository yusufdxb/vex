# Token Optimization Techniques

## The Token Budget Mindset

Every token you read into context costs money. Every token you generate costs more.
The goal: get the right answer using the minimum tokens needed to be correct.

## Technique 1 — Grep Before Read

**Wrong:**
```
Read("src/controller.py")  # 800 lines, 12K tokens
```

**Right:**
```
Grep("class Controller", "src/controller.py")  # returns 3 lines
Read("src/controller.py", offset=45, limit=60)  # read only the class
```

Savings: typically 80–95% of file read tokens.

## Technique 2 — Parallel Independent Reads

**Wrong (serialized):**
```
Read("include/foo.h")
# wait...
Read("include/bar.h")
# wait...
Read("src/main.cpp")
```

**Right (batched):**
```
[Read("include/foo.h"), Read("include/bar.h"), Read("src/main.cpp")]
```

Savings: same tokens, but faster. Never creates extra cost.

## Technique 3 — Diff-Based Context

When reviewing changes or understanding recent work:

```bash
git diff HEAD -- src/foo.py      # much smaller than full file
git log --oneline -10             # before reading any file
git diff HEAD~1 HEAD --stat       # understand scope before diving in
```

Savings: reviewing a 200-line file via diff costs ~200–500 tokens vs ~3000 for full read.

## Technique 4 — Signature-Only Reads

When you need to know an API but not its implementation:

```
Grep("^def |^class |^void |^fn |pub fn ", "src/module.py")
```

Returns all function/class signatures — enough to understand the interface.
Savings: skip reading 500+ lines of implementation.

## Technique 5 — Incremental Patching

Apply one logical change at a time, verify it compiles/tests pass, then continue.
Don't batch 10 changes into one call — if it fails, you lose all 10 and re-read everything.

Savings: avoids catastrophic re-read after corrupt large patches.

## Technique 6 — No Prose Summaries

After every code change, the default instinct is to write:
"I've updated the Controller class to use the new async API. The changes include..."

Delete this. The diff is the summary. The user can read it.
Savings: 100–400 tokens per response, multiplied across all responses in a session.

## Technique 7 — Context Pruning Before Long Tasks

Before starting any multi-file task, explicitly list what you need vs what you don't:

```
Files I MUST read:   [file A for its public API, file B for the function I'll modify]
Files I can SKIP:    [test files, unchanged modules, docs]
Info I can GET via GREP: [all function signatures, all includes/imports]
```

Don't read files "for context" you won't use.

## Technique 8 — Minimal Prompts for Local Models

When passing work to Ollama, be precise:
- Name the exact files relevant to the task
- State the exact operation (one sentence)
- State the acceptance criteria (how to know if it worked)
- Provide only the code context the model actually needs (interfaces, not implementations)

Verbose prompts don't improve quality for local models — they inflate context and reduce accuracy.

## Estimated Token Costs (reference)

| Operation | Tokens |
|---|---|
| Reading 100-line file | ~1500 |
| Reading 500-line file | ~7500 |
| Grep result (10 matches) | ~200 |
| `git diff` (10 changed lines) | ~300 |
| Prose summary paragraph | ~150–400 |
| Ollama call (no overhead on Claude) | 0 Claude tokens |
| Agent spawn overhead | ~3000–8000 |
