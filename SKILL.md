---
name: vex
description: Intelligent LLM routing system — minimizes cost while maximizing reliability. ALWAYS triggers when: any coding task begins, user mentions usage/cost/tokens/routing/models, task involves file edits, refactors, debugging, or build system changes. Routes tasks across model tiers using confidence scoring, impact analysis, risk scoring, and adaptive learning. Supports two modes — cloud-only (Opus/Sonnet/Haiku) and hybrid (Claude + Ollama local models).
user-invocable: true
---

# Vex — Intelligent LLM Orchestration

## User Configuration

Choose your routing mode and configure it below.

### Mode A — Cloud Only (no local models needed)

```
ROUTING_MODE:  cloud
TIER_1:        claude-haiku-4-5    # fast, cheap — trivial/mechanical tasks
TIER_2:        claude-sonnet-4-5   # balanced — single/multi-file, debugging
TIER_3:        claude-opus-4-6     # full power — architecture, refactors, research
```

### Mode B — Hybrid (Claude + Ollama)

```
ROUTING_MODE:    hybrid
OLLAMA_SMALL:    <your small model, e.g. llama3.2, qwen2.5:7b>
OLLAMA_MEDIUM:   <your medium model, e.g. qwen2.5:14b, mistral>
OLLAMA_LARGE:    <your large model, e.g. qwen2.5:32b, deepseek-coder-v2:16b>
OLLAMA_ENDPOINT: http://localhost:11434
CLOUD_MODEL:     claude-sonnet-4-5  (fallback/escalation target)
```

Throughout this skill, `tier:1`, `tier:2`, `tier:3` refer to your configured models — either Haiku/Sonnet/Opus or Ollama small/medium/large.

---

## Role Architecture

### Cloud Mode
```
Opus   = MASTERMIND  (architecture, complex reasoning, verification)
Sonnet = WORKHORSE   (multi-file edits, debugging, feature work)
Haiku  = GRUNT       (trivial, mechanical, boilerplate, renames)
```

### Hybrid Mode
```
Claude  = PLANNER + ARCHITECT + VERIFIER  (never brute executor)
Ollama  = LOCAL EXECUTOR  (deterministic, isolated, low-risk tasks)
```

In both modes: the highest-tier model owns the plan. Lower tiers execute.
Never route a task requiring cross-file understanding to a lower tier without a higher-tier plan.

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

**Confidence rule:** If `confidence < 0.65` → skip tier:1 and tier:2, route directly to `tier:3`.
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

### Cloud Mode Limits
```
Haiku  (tier:1)  → safe <= 32K tokens   (fast, 200K context window)
Sonnet (tier:2)  → safe <= 180K tokens  (balanced)
Opus   (tier:3)  → safe <= 680K tokens  (1M context window)
```

### Hybrid Mode Limits
```
ollama:small  (tier:1)  → safe <= 4K tokens
ollama:medium (tier:2)  → safe <= 8K tokens
ollama:large  (tier:3)  → safe <= 16K tokens
Claude        (tier:3+) → safe <= 180K tokens
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
- `confidence < 0.65` → force `tier:3`
- `IMPACT = CRITICAL` → force `tier:3`
- `RISK = CRITICAL` → force `tier:3`

### Cloud Mode Routing Table

| Class | Risk | Route |
|---|---|---|
| TRIVIAL | ANY | `haiku` |
| MECHANICAL | LOW–MED | `haiku` |
| MECHANICAL | HIGH+ | `sonnet` |
| SINGLE_FILE | LOW | `haiku` |
| SINGLE_FILE | MEDIUM | `sonnet` |
| SINGLE_FILE | HIGH+ | `sonnet` |
| MULTI_FILE | LOW | `sonnet` |
| MULTI_FILE | MEDIUM+ | `opus` |
| REFACTOR | LOW–MED | `sonnet` |
| REFACTOR | HIGH+ | `opus` |
| ARCHITECTURAL | ANY | `opus` |
| DEBUGGING | LOW | `sonnet` |
| DEBUGGING | MEDIUM+ | `opus` |
| RESEARCH | ANY | `opus` |
| INFRASTRUCTURE | ANY | `sonnet` (opus verifies) |

### Hybrid Mode Routing Table

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

### Cloud Mode Execution

#### Route: `haiku`
Spawn a Haiku subagent for the task. Provide:
- Exact file paths and line ranges
- Single clear instruction
- Acceptance criteria

Haiku is fast but literal — be precise. Don't ask it to make judgment calls.

#### Route: `sonnet`
Use Sonnet as the primary workhorse. It handles:
- Multi-file edits with Read/Edit/Bash tools
- Debugging with error context
- Feature implementation from a clear spec

#### Route: `opus`
Full Opus session. Owns the entire task end-to-end:
- Architecture decisions
- Complex refactors
- Planning that Sonnet/Haiku will execute
- Verification of lower-tier work

#### Route: `opus:plan` → `sonnet:exec` (or `haiku:exec`)
**Step A — Opus produces a structured plan:**
```
Files to touch: [list]
Operations:
  - [file]: [what to do, one sentence each]
Acceptance criteria: [how to verify success]
```
**Step B — Sonnet or Haiku executes each step.**
**Step C — Opus verifies the result.**

### Hybrid Mode Execution

#### Route: `ollama:*` (local model)

```
mcp__ollama__ollama_query(
  model = "<configured model ID>",
  prompt = "[full task + code context]"
)
```

Do NOT use Ollama for tasks that require writing files — it generates text only.
If your setup supports Ollama tool-use or agentic execution, you can extend this route.

#### Route: `claude:plan`

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

#### Route: `claude:full`

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
- **Use cheaper tiers for reads** — in cloud mode, let Haiku do file exploration before Opus plans

---

## Step 8 — Failure Detection and Escalation

See full playbook in `references/escalation.md`. Summary:

**Failure signals:** non-zero exit, `error:` / `SyntaxError` / `fatal:` in output, empty diff, diff > 500 lines, "I'm not sure" / "I cannot"

### Cloud Mode Escalation
```
haiku → sonnet → opus
  ↑        ↑
2 retries  2 retries
```

### Hybrid Mode Escalation
```
ollama:small → ollama:medium → ollama:large → claude:full
       ↑              ↑              ↑
   2 retries      2 retries      2 retries
```

On each escalation: pass failure context forward, don't repeat the same prompt, `git checkout -- .` if build is broken.

**After every task:** log the outcome to `references/routing_log.jsonl` (see Step 9).

---

## Step 9 — Adaptive Learning

See full spec in `references/adaptive-routing.md`. Summary:

After every routed task, append one line to `references/routing_log.jsonl`:
```json
{"date":"2026-03-29","class":"DEBUGGING","model":"sonnet","success":false,"tokens":3200,"escalated_to":"opus"}
```

Before routing a new task, check if a routing log entry exists for the same CLASS:
```bash
grep '"class":"DEBUGGING"' references/routing_log.jsonl | python3 -c "
import sys, json
rows = [json.loads(l) for l in sys.stdin]
for model in ['haiku','sonnet','ollama:small','ollama:medium','ollama:large']:
    total = sum(1 for r in rows if r['model']==model)
    wins  = sum(1 for r in rows if r['model']==model and r['success'])
    if total >= 3:
        print(f'{model}: {wins}/{total} = {wins/total:.0%}')
"
```

**Routing adjustment rule:** If a model shows < 40% success rate for this CLASS with >= 3 data points, skip it.

---

## When Invoked as `/vex`

Output a routing audit for the current task:

```
ROUTING AUDIT
-------------
Mode:          [cloud | hybrid]
Task class:    [CLASS] (confidence: [N])
Impact score:  [LOW/MEDIUM/HIGH/CRITICAL] ([N] downstream files)
Risk score:    [N] → [LOW/MEDIUM/HIGH/CRITICAL]
Context est.:  [~N tokens]
Historical:    [model success rates for this class, if logged]
Assigned route: [route]

Overrides triggered:
  [list any pre-routing overrides, or "none"]

Offload opportunities:
  Tier 1: [tasks safe for cheapest model]
  Tier 2: [tasks for mid-tier model]

Token waste found:
  [list wasteful patterns with leaner alternatives]

Recommended execution plan:
  1. [step]
  2. [step]
```

---

## Environment Reference

### Cloud Mode Models

| Tier | Model | Best for | Relative cost |
|---|---|---|---|
| `tier:1` | Claude Haiku 4.5 | Trivial, mechanical, boilerplate | $$ |
| `tier:2` | Claude Sonnet 4.5 | Single/multi-file, debugging, features | $$$ |
| `tier:3` | Claude Opus 4.6 | Architecture, refactors, research, verification | $$$$ |

### Hybrid Mode Models (Ollama)

Configure in User Configuration section above. Example setup:

| Tier | Example Model | Best for | Cost |
|---|---|---|---|
| `tier:1` | qwen2.5-coder:7b | Trivial/Mechanical | Free |
| `tier:2` | qwen2.5-coder:14b | Single-file code | Free |
| `tier:3` | deepseek-coder-v2:16b | Complex code, debug | Free |
| Escalation | Claude Sonnet | Everything else | API cost |

**Verify Ollama is running:** `curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin)['models']]"`

**Dependencies:**
- [Ollama](https://ollama.ai) — local model runtime (hybrid mode only)
- Claude Code CLI or API access
- `git` — for impact analysis and diff-based context
- `grep` — for symbol reference counting
