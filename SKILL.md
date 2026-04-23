---
name: vex
description: Prompt-based LLM routing heuristic — intended to reduce cost by routing tasks to cheaper model tiers. Triggers when: any coding task begins, user mentions usage/cost/tokens/routing/models, task involves file edits, refactors, debugging, or build system changes. Routes tasks across model tiers using confidence scoring, impact analysis, risk scoring, and adaptive learning. Supports two modes — cloud-only (Opus/Sonnet/Haiku) and hybrid (Claude + Ollama local models). Opus 4.7 compliant.
user-invocable: true
---

# Vex — LLM Routing Skill

## User Configuration

Choose your routing mode and configure it below.

### Mode A — Cloud Only (no local models needed)

```
ROUTING_MODE:  cloud
TIER_1:        claude-haiku-4-5    # fast, cheap — trivial/mechanical tasks
TIER_2:        claude-sonnet-4-5   # balanced — single/multi-file, debugging
TIER_3:        claude-opus-4-7     # full power — architecture, refactors, research
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
## Example — assumes an Ollama MCP server is configured in your Claude Code setup.
## Adapt the function name and parameters to match your actual MCP server.
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

On each escalation: pass failure context forward, don't repeat the same prompt. If the build is broken, `git stash` first to preserve any unrelated work, then `git checkout -- .` to revert. See `references/escalation.md` for safety details.

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

## Step 10 — Output Compression Modes

Output tokens are as real as input tokens. Four opt-in modes compress Claude's own prose output when the user doesn't need long-form explanation. All are session-scoped toggles, activated via `/vex`.

### Tight mode (recommended default)

Activated by `/vex tight`. Deactivated by `/vex tight off` or `/vex normal`.

The most conservative mode — only cuts preamble and trailing summary. Length and structure are otherwise normal.

While active, every Claude text response must:
- Skip opening sentences about what you are about to do (`I'll...`, `Let me...`, `Sure,...`, `Here is...`)
- Skip closing sentences summarizing what you just did
- If the reply is a code block, output only the code block with no prose wrapping unless explanation was requested

Example:
- Off: "I'll read the config file, then patch the routing table, then run the tests. ...I've now read the config, patched the routing table, and run the tests."
- On:  "Config read. Patched `route.py:42` for the new tier. Tests pass."

### Terse mode

Activated by `/vex terse`. Deactivated by `/vex terse off` or `/vex normal`.

While active, every Claude text response must:
- Fit in 15 words or fewer per reply
- Use full sentences but cut all preamble, throat-clearing, and recap
- Omit markdown headers, bullet lists, code fences around prose, and trailing summaries
- State only the result, the next action, or the blocker

Example:
- Off: "I'll read the config file first, then patch the routing table, then run the tests to confirm."
- On:  "Reading config. Patching route. Running tests."

### Caveman mode

Activated by `/vex caveman`. Deactivated by `/vex caveman off` or `/vex normal`.

While active, every Claude text response must:
- Be 1 to 5 words total
- Use broken grammar, no articles, no punctuation
- Drop pronouns and auxiliary verbs

Example:
- Off: "I've finished reading the file and I'm about to edit it."
- On:  "file read edit next"

### Ghost mode (maximum compression)

Activated by `/vex ghost`. Deactivated by `/vex ghost off` or `/vex normal`.

The most aggressive mode. For pure-execution tasks where the user does not need narration — the tool calls and file diffs already tell the story.

While active, every Claude text response must:
- Be at most 10 words of prose, in the form `done: <what>` or `blocked: <why>`
- Never narrate what was done or will be done — the tool calls and file writes are self-evident
- Never echo code that was written to a file
- If a code block is the natural reply, output only the code block with zero prose

Example:
- Off: "I've read the config, patched the routing table in config.py (added the new tier between sonnet and haiku), and run the tests — all 12 pass. Let me know if you'd like me to..."
- On:  `done: new tier added, 12/12 tests pass`

### Auto mode (recommended)

Activated by `/vex auto`. Deactivated by `/vex auto off` or `/vex normal`.

Measurement (n=3 per combo on Sonnet, see `evaluation/COMPRESSION_RESULTS.md`) shows no single compression mode wins across all task classes. Each class has a different best mode; picking one mode globally either leaves savings on the table or actively costs tokens. `/vex auto` solves this by picking the mode from the classification step:

| Task class      | Auto-selected mode | Measured saving vs normal |
|-----------------|-------------------|--------------------------|
| `TRIVIAL`       | `ghost`           | -55%                     |
| `MECHANICAL`    | `tight`           | -47%                     |
| `RESEARCH`      | `terse`           | -40%                     |
| `ARCHITECTURAL` | `ghost`           | -33%                     |
| `SINGLE_FILE`   | `terse`           | -28%                     |
| `DEBUGGING`     | `normal` (no mode) | (all modes rebelled)    |
| `MULTI_FILE`    | `tight` (default) | no data — inferred       |
| `REFACTOR`      | `tight` (default) | no data — inferred       |
| `INFRASTRUCTURE`| `tight` (default) | no data — inferred       |

The auto mapping is loaded from the measurement table above. When `/vex auto` is active, the classification from Step 1 selects the compression mode for that reply only. If the classification changes mid-session (e.g., TRIVIAL fix becomes a SINGLE_FILE debugging trace), the auto mapping re-selects.

Manual overrides (`/vex terse`, `/vex tight`, etc.) take precedence over auto for the rest of the session. `/vex auto` can be re-enabled with another `/vex auto` call.

### Per-class output budgets

Independent of the above modes, each task class has a soft output-token budget that Claude should aim for. These are anchors, not hard caps — exceed them only when the task legitimately needs more prose.

| Class | Prose budget (tokens) | Rationale |
|---|---|---|
| `TRIVIAL` | 80 | A rename or comment addition needs no explanation |
| `MECHANICAL` | 150 | Docstrings/formatting are self-evident |
| `SINGLE_FILE` | 300 | One-file fix with brief cause + fix |
| `MULTI_FILE` | 500 | Brief per-file rationale |
| `REFACTOR` | 600 | Reason for structure + before/after |
| `ARCHITECTURAL` | 1200 | Trade-off discussion legitimately needs space |
| `DEBUGGING` | 300 | Cause, fix, verify — three lines |
| `RESEARCH` | 1000 | Explanation is the deliverable |
| `INFRASTRUCTURE` | 300 | Config is code; minimal prose |

Measurement shows normal-mode replies consistently exceed these budgets (e.g., `TRIVIAL` averages ~1000 tokens for a simple rename). Aiming for the budget recovers most of the savings that compression modes provide, without the structured-output regressions.

### What the modes do NOT change

These modes compress **prose output only**. They must not degrade the actual work:
- Code written into files stays idiomatic and complete
- Commit messages, PR titles, and PR bodies stay professional
- Tool call arguments (grep patterns, bash commands, file paths) are unaffected
- Error messages surfaced from tools are passed through verbatim
- When the user explicitly asks for a full explanation, the mode is paused for that single reply

### Precedence

Manual modes take precedence over `/vex auto`. If multiple manual modes are somehow requested, the more aggressive wins: **ghost > caveman > terse > tight**. Only one mode is active at a time. Modes do not persist across sessions — each new session starts with all off.

### Interaction with routing

These modes stack with Step 7 token optimization and Step 11 cache-friendly operation. They are orthogonal to routing: Haiku, Sonnet, and Opus all obey them. When a lower-tier subagent is spawned, pass the active mode forward in its system prompt so its output stays compressed too.

---

## Step 11 — Cache-Friendly Operation

The Anthropic API prompt cache gives a ~90% input-token discount on cached reads with a 5-minute TTL. On long Claude Code sessions this is the single biggest input-side lever and is invisible to the user if the skill plays along.

### Rules for preserving cache hits

1. **Do not rewrite CLAUDE.md, SKILL.md, or any loaded-skill file mid-session.** Any edit invalidates every prefix-cached message after it. If a change is needed, batch it at session end.
2. **Do not reorder the system prompt or skill list between turns.** Prefix cache hits require byte-identical prefixes. Adding or removing a skill mid-session breaks the cache.
3. **Append, don't prepend.** Add new context to the end of messages, not the top. Prepending rewrites everything downstream.
4. **Prefer a single long-lived session over many short ones** when cache warmth matters. A 5-minute gap between turns drops the cache; under 5 minutes it holds.
5. **For repeated file reads, read once and reference.** Re-reading the same file flushes no cache but pays the full input cost every time. If you've already read `foo.py:42-80`, cite it by path+lines instead of reading again.

### When cache is NOT worth preserving

- First read of a file you will edit — the edit invalidates cache downstream anyway.
- Exploration sessions where the next prompt is unpredictable.
- Sessions that span > 5 minutes of user idle time.

### Output-side interaction

Prompt caching only discounts **input** tokens. Output tokens still cost full rate, which is why the Step 10 compression modes and per-class output budgets are separate levers. Use both together for compounded savings.

### Read-before-Read rule

Every `Read` call on a file > 200 lines is ~1K+ input tokens. Before reading a large file:

1. `Grep` for the symbol or keyword to find the relevant line range.
2. `Read` with `offset` and `limit` covering only that range plus a few lines of context.
3. Only read the whole file when the whole file is genuinely needed (small configs, policy docs, one-screen modules).

This rule also applies to sample/example files. Never read `examples/**`, `evaluation/examples/**`, or any file clearly labeled as sample data unless the user explicitly asked about the examples.

---

## When Invoked as `/vex`

### Subcommands

| Command | Effect |
|---|---|
| `/vex` | Emit a routing audit for the current task (see format below) |
| `/vex auto` | Enable auto mode — skill picks compression per task class (Step 10) |
| `/vex auto off` | Disable auto mode |
| `/vex tight` | Enable tight mode — drop preamble + trailing summary (Step 10) |
| `/vex tight off` | Disable tight mode |
| `/vex terse` | Enable terse mode — ≤15 words per reply (Step 10) |
| `/vex terse off` | Disable terse mode |
| `/vex caveman` | Enable caveman mode — 1-5 words, broken grammar (Step 10) |
| `/vex caveman off` | Disable caveman mode |
| `/vex ghost` | Enable ghost mode — tool calls + 10-word status only (Step 10) |
| `/vex ghost off` | Disable ghost mode |
| `/vex normal` | Disable all compression modes |

When a mode toggle is invoked, acknowledge the switch in the new mode's style (e.g., `/vex caveman` → reply `caveman on`) and apply it to every subsequent reply in the session.

### Routing audit format

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
| `tier:3` | Claude Opus 4.7 | Architecture, refactors, research, verification | $$$$ |

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
