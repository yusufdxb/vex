---
name: smart-routing
description: Intelligent LLM routing system — minimizes Claude API cost while maximizing reliability. ALWAYS triggers when: any coding task begins, user mentions usage/cost/tokens/Ollama/local models, task involves file edits, refactors, debugging, or build system changes. Routes tasks across Claude (plan+verify) and Ollama (local execution) using confidence scoring, impact analysis, risk scoring, and adaptive learning.
user-invocable: true
---

# Smart Routing — Intelligent LLM Orchestration

## User Configuration

Set these values to match your local setup before using this skill.

```
OLLAMA_SMALL:    <your small model, e.g. llama3.2, qwen2.5:7b>
OLLAMA_MEDIUM:   <your medium model, e.g. qwen2.5:14b, mistral>
OLLAMA_LARGE:    <your large model, e.g. qwen2.5:32b, llama3.1:70b, deepseek-coder-v2:16b>
OLLAMA_ENDPOINT: http://localhost:11434
CLOUD_MODEL:     claude-sonnet-4-5  (or your preferred Claude model)
```

Replace references to `ollama:small`, `ollama:medium`, and `ollama:large` throughout this skill with the model IDs you configure above.

---

## Role Architecture

```
Claude  = PLANNER + ARCHITECT + VERIFIER  (never brute executor)
Ollama  = LOCAL EXECUTOR  (deterministic, isolated, low-risk tasks)
```

Claude always owns the plan. Ollama handles tasks requiring minimal reasoning.
Never route a task requiring cross-file understanding to a local model without a Claude-written plan.

---

## Step 1 — Classify the Task (with Confidence Score)

Assign ONE class and a confidence score 0.0–1.0:

| Class | Signals |
|---|---|
| `TRIVIAL` | Rename, typo fix, add comment, 1–5 lines, no logic |
| `MECHANICAL` | Docstrings, formatting, boilerplate, repetitive transforms |
| `SINGLE_FILE` | Logic change in one file, function-level |
| `MULTI_FILE` | Changes span 2–10 files, wiring a new feature |
| `REFACTOR` | Structural change, module rename/extract, cross-package |
| `ARCHITECTURAL` | New subsystem, major API redesign, replace X with Y |
| `DEBUGGING` | Error output present, "why is", "fix crash", segfault |
| `RESEARCH` | "explain", "how does", "document", "understand" |
| `INFRASTRUCTURE` | Build configs, Dockerfiles, CI/CD pipelines, deploy scripts |

**Confidence scoring signals:**

| Signal | Effect |
|---|---|
| Single file, clear scope | +0.2 |
| Error message provided | +0.2 |
| User specified exact function | +0.15 |
| Multiple files involved | -0.1 |
| Ambiguous user request | -0.2 |
| Mixed languages in repo | -0.1 |
| No test coverage | -0.05 |
| Deep dependency chains | -0.15 |

**Confidence rule:** If `confidence < 0.65` → skip all local model tiers, route directly to `claude:plan`.
A low-confidence task given to a weak model will produce confidently wrong output.

---

## Step 2 — Repository Impact Analysis

Before routing, estimate how many files are affected if this change goes wrong.
Use grep + git to approximate — no full call graph required.

```bash
# Count files that import/reference the symbol being changed
grep -r "SymbolName" --include="*.py" --include="*.cpp" --include="*.ts" --include="*.js" --include="*.go" --include="*.rs" -l | wc -l

# Check downstream dependencies (adapt to your build system)
# For npm:   grep -r '"SymbolName"' package.json
# For pip:   grep -r "SymbolName" requirements.txt setup.py pyproject.toml
# For cargo: grep -r "SymbolName" Cargo.toml

# See if symbol is part of a public API
grep -r "SymbolName" --include="*.h" --include="*.hpp" --include="*.d.ts" -l | wc -l
```

**Impact score thresholds:**

| Downstream files | Impact |
|---|---|
| 0–1 | LOW |
| 2–5 | MEDIUM |
| 6–15 | HIGH |
| 16+ | CRITICAL |

**Adjust routing:** Impact score escalates route tier. A LOW-risk SINGLE_FILE task with HIGH impact routes like a MULTI_FILE task.

---

## Step 3 — Risk Scoring

Scan the task for risk signals. Sum the scores.

**+3 each (CRITICAL):**
- Build system configs (Makefile, CMakeLists.txt, build.gradle, etc.)
- CI/CD config (`.github/workflows`, `.gitlab-ci.yml`, Jenkinsfile)
- Docker or docker-compose files
- Infrastructure-as-code (Terraform, Pulumi, CloudFormation)
- Database migrations or schema changes
- Security-sensitive code (auth, crypto, permissions)
- Hardware interface or driver code

**+2 each (HIGH):**
- More than 5 files touched
- Test files modified
- Main entry points (`main.*`, `index.*`, `app.*`)
- Dependency manifests (`requirements.txt`, `package.json`, `Cargo.toml`, `go.mod`)
- Cross-package imports added or removed
- Public API surface changed

**+1 each (MEDIUM):**
- 2–5 files touched
- New feature wired into existing code
- Module-level interface changes

```
0     = LOW
1–2   = MEDIUM
3–5   = HIGH
>=6   = CRITICAL
```

---

## Step 4 — Context Size Estimation

Count lines across all files needed x 15 for token estimate. Add 500 overhead, 200 per file.

```
ollama:small   → safe <= 4K tokens
ollama:medium  → safe <= 8K tokens
ollama:large   → safe <= 16K tokens
Claude         → safe <= 180K tokens
```

Adjust these limits based on the actual context window of your configured models.

---

## Step 5 — Route

Five inputs → one route:

```
classify(task)  → CLASS + CONFIDENCE
impact(repo)    → IMPACT
score(task)     → RISK
estimate(task)  → CTX
stats(CLASS)    → MODEL_SUCCESS_RATES  (from routing log)
```

**Pre-routing overrides (check first):**
- `confidence < 0.65` → force `claude:plan`
- `IMPACT = CRITICAL` → force `claude:full`
- `RISK = CRITICAL` → force `claude:full`

**Routing table (after overrides pass):**

| Class | Risk | Context | Route |
|---|---|---|---|
| TRIVIAL | ANY | <4K | `ollama:small` |
| MECHANICAL | LOW | <8K | `ollama:medium` |
| MECHANICAL | LOW | <16K | `ollama:large` |
| MECHANICAL | MEDIUM+ | ANY | `claude:plan` |
| SINGLE_FILE | LOW | <8K | `ollama:medium` |
| SINGLE_FILE | MEDIUM | <16K | `ollama:large` |
| SINGLE_FILE | HIGH+ | ANY | `claude:plan` |
| MULTI_FILE | LOW | <16K | `ollama:large` |
| MULTI_FILE | MEDIUM+ | ANY | `claude:full` |
| REFACTOR | LOW–MED | <16K | `claude:plan` |
| REFACTOR | HIGH+ | ANY | `claude:full` |
| ARCHITECTURAL | ANY | ANY | `claude:full` |
| DEBUGGING | LOW | <16K | `ollama:large` → escalate |
| DEBUGGING | MEDIUM+ | ANY | `claude:full` |
| RESEARCH | ANY | ANY | `claude:full` |
| INFRASTRUCTURE | ANY | ANY | `claude:full` |

**Adaptive override:** If routing log shows model success rate for this CLASS < 40%, skip that tier.
See `references/adaptive-routing.md` for how to read the log.

---

## Step 6 — Execute the Route

### Route: `ollama:*` (local model)

```
mcp__ollama__ollama_query(
  model = "<OLLAMA_SMALL|OLLAMA_MEDIUM|OLLAMA_LARGE>",
  prompt = "[full task + code context]"
)
```

Do NOT use Ollama for tasks that require writing files — it generates text only.
If your setup supports Ollama tool-use or agentic execution, you can extend this route.

### Route: `claude:plan`

**Step A — Claude produces a structured plan (minimal tokens):**
```
Files to touch: [list]
Operations:
  - [file]: [what to do, one sentence each]
Acceptance criteria: [how to verify success]
Context needed: [only the signatures/APIs needed]
```

**Step B — Claude does minimal targeted reads:**
- Grep for function signatures, not full file reads
- Read only the hunks that will be modified (offset+limit)

**Step C — Claude executes the plan using Read/Edit/Bash tools.**

**Step D — Claude verifies after execution:**
- Run project-specific build/test commands
- Scan diff: `git diff --stat`

### Route: `claude:full`

Stay in Claude. Execute using Read/Edit/Bash tools directly.
Apply all token optimization rules (Step 7) throughout.

---

## Step 7 — Token Optimization (Always Active)

See full techniques in `references/token-ops.md`. Summary rules:

- **Grep before Read** — locate exact lines first, then read offset+limit only
- **Parallel tool calls** — every set of independent reads/greps in a single message
- **Diff-based context** — `git diff HEAD -- file` instead of re-reading
- **Signature-only reads** — grep for `def |class |void |fn ` when you need the API, not the body
- **No prose summaries** — the diff is the summary; don't restate what you just did
- **Context pruning** — list files you will actually touch before starting; don't read extras

---

## Step 8 — Failure Detection and Escalation

See full playbook in `references/escalation.md`. Summary:

**Failure signals:** non-zero exit, `error:` / `SyntaxError` / `fatal:` in output, empty diff, diff > 500 lines, "I'm not sure" / "I cannot"

**Escalation ladder (2 retries per tier, 3 tiers max before Claude):**
```
ollama:small → ollama:medium → ollama:large → claude:full
```

On each escalation: pass failure context forward, don't repeat the same prompt, `git checkout -- .` if build is broken.

**After every task:** log the outcome to `references/routing_log.jsonl` (see Step 9).

---

## Step 9 — Adaptive Learning

See full spec in `references/adaptive-routing.md`. Summary:

After every routed task, append one line to `references/routing_log.jsonl`:
```json
{"date":"2026-03-29","class":"DEBUGGING","model":"ollama:large","success":false,"tokens":3200,"escalated_to":"claude:full"}
```

Before routing a new task, check if a routing log entry exists for the same CLASS:
```bash
grep '"class":"DEBUGGING"' references/routing_log.jsonl | python3 -c "
import sys, json
rows = [json.loads(l) for l in sys.stdin]
for model in ['ollama:small','ollama:medium','ollama:large']:
    total = sum(1 for r in rows if r['model']==model)
    wins  = sum(1 for r in rows if r['model']==model and r['success'])
    if total >= 3:
        print(f'{model}: {wins}/{total} = {wins/total:.0%}')
"
```

**Routing adjustment rule:** If a model shows < 40% success rate for this CLASS with >= 3 data points, skip it.

---

## When Invoked as `/smart-routing`

Output a routing audit for the current task:

```
ROUTING AUDIT
-------------
Task class:    [CLASS] (confidence: [N])
Impact score:  [LOW/MEDIUM/HIGH/CRITICAL] ([N] downstream files)
Risk score:    [N] → [LOW/MEDIUM/HIGH/CRITICAL]
Context est.:  [~N tokens]
Historical:    [model success rates for this class, if logged]
Assigned route: [route]

Overrides triggered:
  [list any pre-routing overrides, or "none"]

Offload opportunities:
  Local models: [tasks safe for Ollama]

Token waste found:
  [list wasteful patterns with leaner alternatives]

Recommended execution plan:
  1. [step]
  2. [step]
```

---

## Environment Reference

**Local models (Ollama):**
Configure in User Configuration section above. Example setup:

| Tier | Example Model | Best for |
|---|---|---|
| `ollama:small` | qwen2.5-coder:7b | Trivial/Mechanical |
| `ollama:medium` | qwen2.5-coder:14b | Single-file code |
| `ollama:large` | deepseek-coder-v2:16b | Complex code, debug |

**Verify Ollama is running:** `curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin)['models']]"`

**Dependencies:**
- [Ollama](https://ollama.ai) — local model runtime
- Claude Code CLI or API access
- `git` — for impact analysis and diff-based context
- `grep` — for symbol reference counting
