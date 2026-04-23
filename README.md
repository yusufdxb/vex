# Vex

A Claude Code skill that routes coding tasks to cheaper model tiers when full-power models aren't needed, plus four opt-in output-compression modes (ghost / caveman / terse / tight), per-class output budgets, and cache-friendly operation rules — all aimed at cutting token cost without cutting correctness.

[![version](https://img.shields.io/badge/version-1.6.0-blue)](CHANGELOG.md)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## What it is

Vex is a [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code) — a structured prompt that Claude reads and follows. It classifies each coding task by complexity, estimates risk and blast radius, then routes to the cheapest model tier that should be able to handle it. If that tier fails, it escalates.

It is **not** a standalone application, API, or runtime. It's a Markdown file (`SKILL.md`) plus four reference docs that change how Claude Code behaves when installed as a skill.

**Two routing modes:**
- **Cloud** — routes between Opus, Sonnet, and Haiku
- **Hybrid** — routes between local Ollama models and Claude

**Five output-compression modes** (opt-in, session-scoped):
- `/vex auto` — **recommended.** Skill picks the compression mode from the task classification using a measured best-per-class table. Gets the per-class wins (28-55%) without the aggregate regressions of a single fixed mode.
- `/vex tight` — drop preamble + trailing summary only, length otherwise normal
- `/vex terse` — full sentences, ≤15 words, no preamble
- `/vex caveman` — 1-5 words, broken grammar, no punctuation
- `/vex ghost` — tool calls + a single 10-word `done:` / `blocked:` status line, no prose at all

**Per-class output budgets** — soft token caps per task class (TRIVIAL ≤80, DEBUGGING ≤300, ARCHITECTURAL ≤1200, etc.) so even without a compression mode active, Claude aims smaller on prompts that don't need prose.

**Cache-friendly rules** — don't rewrite loaded skills mid-session, append don't prepend, prefer one long session over many short ones. See `SKILL.md` Step 11 for the full set. Anthropic's prompt cache is 90% off on input tokens with a 5-min TTL — it's the biggest input-side lever if the skill doesn't invalidate it.

---

## Install

```bash
git clone https://github.com/yusufdxb/vex.git
cp -r vex/ ~/.claude/skills/vex/
```

Edit the config block at the top of `SKILL.md`:

**Cloud mode (Claude only):**
```
ROUTING_MODE:  cloud
TIER_1:        claude-haiku-4-5
TIER_2:        claude-sonnet-4-6
TIER_3:        claude-opus-4-7
```

**Hybrid mode (Claude + Ollama):**
```
ROUTING_MODE:    hybrid
OLLAMA_SMALL:    qwen2.5-coder:7b
OLLAMA_MEDIUM:   qwen2.5-coder:14b
OLLAMA_LARGE:    deepseek-coder-v2:16b
OLLAMA_ENDPOINT: http://localhost:11434
CLOUD_MODEL:     claude-sonnet-4-6
```

Once installed, the skill prompt is available to Claude Code on every task.

---

## How routing works

```
Task → Classify → Impact analysis → Risk score → Context estimate → Route → Execute → Log outcome
```

1. **Classify** — trivial rename through architectural change
2. **Impact** — how many files reference the symbol being changed
3. **Risk** — does it touch CI, auth, migrations, or other sensitive areas
4. **Context** — token budget the task needs
5. **Route** — cheapest tier that fits the classification
6. **Execute** — optimized prompt for that tier
7. **Catch failures** — detect errors, empty output, corrupt patches → escalate
8. **Log** — record the outcome for future routing adjustments

### Routing tables

**Cloud mode:**

| | Low risk | Med risk | High+ risk |
|---|---|---|---|
| **Trivial** | Haiku | Haiku | Haiku |
| **Mechanical** | Haiku | Haiku | Sonnet |
| **Single file** | Sonnet | Sonnet | Sonnet |
| **Multi file** | Sonnet | Opus | Opus |
| **Refactor** | Sonnet | Sonnet | Opus |
| **Architectural** | Opus | Opus | Opus |
| **Debugging** | Sonnet | Opus | Opus |

**Hybrid mode:**

| | Low risk | Med risk | High+ risk |
|---|---|---|---|
| **Trivial** | ollama:small | ollama:small | ollama:small |
| **Mechanical** | ollama:medium | claude:plan | claude:full |
| **Single file** | ollama:medium | ollama:large | claude:plan |
| **Multi file** | ollama:large | claude:full | claude:full |
| **Refactor** | claude:plan | claude:plan | claude:full |
| **Architectural** | claude:full | claude:full | claude:full |
| **Debugging** | ollama:large | claude:full | claude:full |

> Hybrid mode routing also depends on context size — see `SKILL.md` for the full logic.

**Hard overrides** — always routed to the top tier:
- Classification confidence below 0.65
- Impact or risk scored as CRITICAL
- ARCHITECTURAL or RESEARCH tasks

---

## Output compression modes

Routing cuts input cost. Output tokens also cost money. Vex ships five opt-in modes:

| Command | Style | Example reply |
|---|---|---|
| `/vex auto` | Skill picks per task class (measured best-mode table) | — |
| `/vex tight` | Normal length, drop preamble + trailing summary only | `Config read. Patched route.py:42. Tests pass.` |
| `/vex terse` | Full sentences, ≤15 words, no preamble or markdown | `Reading config. Patching route. Running tests.` |
| `/vex caveman` | 1-5 words, broken grammar, no punctuation | `file read edit next` |
| `/vex ghost` | ≤10 words total, `done:` / `blocked:` format | `done: tier added, 12/12 tests pass` |
| `/vex normal` | Revert to default output style | — |

### Measured savings (Sonnet, 90 calls, n=3 per cell)

Aggregate compression is unreliable — only `terse` saves anything (-6%); `tight` and `caveman` actively cost more tokens than normal when applied blindly. **But every class has a winning mode with 28-55% savings.** That's why `/vex auto` is the recommended default — it matches the mode to the classification:

| Class          | Best mode | Saves vs normal |
|----------------|-----------|----------------:|
| TRIVIAL        | `ghost`   | **-55%**        |
| MECHANICAL     | `tight`   | **-47%**        |
| RESEARCH       | `terse`   | **-40%**        |
| ARCHITECTURAL  | `ghost`   | **-33%**        |
| SINGLE_FILE    | `terse`   | **-28%**        |
| DEBUGGING      | none      | -5% (all modes except terse rebelled) |

Full data, caveats, variance analysis, and the 90-call raw log: [`evaluation/COMPRESSION_RESULTS.md`](evaluation/COMPRESSION_RESULTS.md).

### Per-class output budgets

Even without a compression mode active, each task class has a soft output-token budget. TRIVIAL ≤80, MECHANICAL ≤150, SINGLE_FILE ≤300, DEBUGGING ≤300, RESEARCH ≤1000, ARCHITECTURAL ≤1200. Measurement showed normal-mode replies routinely exceed these (a rename produced ~1000 output tokens in the baseline); the budgets anchor Claude to stop padding.

Modes are session-scoped. See `SKILL.md` Step 10 for the full spec and Step 11 for cache-friendly operation rules.

---

## `/vex` — inspect routing decisions

Run `/vex` in Claude Code to see how a task would be routed:

```
ROUTING AUDIT
─────────────
Mode:          cloud
Task class:    SINGLE_FILE (confidence: 0.85)
Impact:        LOW (1 downstream file)
Risk:          1 → MEDIUM
Context:       ~2400 tokens
Historical:    no routing log data yet
Route:         haiku

Overrides:     none
Token waste:   full file read on 400-line file — use grep+offset
```

---

## Adaptive routing

The skill instructs Claude to log every routing decision to `references/routing_log.jsonl`. After 3+ data points per model+task combination, routing adjusts:

- **< 40% success rate** → that tier is skipped for that task type
- **> 80% success rate** → that tier is preferred even at slightly higher risk

Until enough data accumulates, routing uses author-estimated bootstrap rates (`references/adaptive-routing.md`). These are starting-point estimates that get replaced by your actual data.

---

## Escalation

When a model fails, Vex escalates to the next tier:

- **Cloud:** Haiku → Sonnet → Opus (2 retries per tier)
- **Hybrid:** small → medium → large → Claude (2 retries per tier)

Each escalation passes failure context forward and reverts partial changes before retrying.

---

## Repo structure

```
vex/
├── SKILL.md                     # Core routing logic (the skill prompt)
├── references/
│   ├── adaptive-routing.md      # Routing log spec and bootstrap estimates
│   ├── escalation.md            # Failure detection and recovery
│   ├── impact-analysis.md       # Blast radius estimation
│   └── token-ops.md             # Token optimization techniques
├── evaluation/
│   ├── METHODOLOGY.md           # Study design, metrics, threats to validity
│   ├── SCORING_RUBRIC.md        # 1-5 quality scoring rubric
│   ├── EXPERIMENT_PROTOCOL.md   # Daily workflow for logging tasks
│   ├── RESULTS_TEMPLATE.md      # Template for publishing findings
│   ├── COMPRESSION_RESULTS.md   # Measured output-compression savings
│   ├── compression_prompts.jsonl
│   ├── scripts/
│   │   ├── analyze.py
│   │   ├── log_task.sh
│   │   └── measure_compression.py
│   ├── examples/sample_eval_log.jsonl
│   └── data/                    # User evaluation data (gitignored)
├── tests/                       # Unit tests for measurement script
├── examples/routing_log_example.jsonl
├── EVALUATION.md                # Evaluation plan
├── CHANGELOG.md
├── CLAUDE.md                    # Contributor guidelines
├── CODE_OF_CONDUCT.md
├── LICENSE                      # MIT
└── README.md
```

---

## What is and isn't measured

**Measured:**
- Output-compression mode savings on Sonnet — `evaluation/COMPRESSION_RESULTS.md` (n=3 per combo, 54 total calls, 19-21% aggregate savings with per-class variance)

**Preliminary (60 tasks, reconstructed baselines — see [`evaluation/RESULTS.md`](evaluation/RESULTS.md)):**
- Routing saves an estimated **44% vs. Opus-only** and **6.1% vs. manual model selection**
- Quality: 4.85/5 mean, 100% pass rate, 5% rework rate
- SINGLE_FILE/LOW was over-routed to Haiku (16 downgrades) — routing table updated to route SINGLE_FILE/LOW to Sonnet
- Escalation effectiveness and hybrid-mode offload rate remain unmeasured (no real routing data yet)

A quick-log script (`evaluation/scripts/quick_log.sh`, 5 prompts) is available for ongoing data collection. See `evaluation/EXPERIMENT_PROTOCOL.md` for the daily workflow.

---

## Limitations (real, not boilerplate)

- **Prompt-based, not enforced.** Vex is instructions Claude follows. There is no runtime enforcement, no guaranteed execution path. Claude can deviate from the routing logic depending on session context.
- **Routing-quality claims are unverified.** The cost/quality tradeoffs of routing Haiku vs. Sonnet vs. Opus are plausible but have not been measured on real workloads in this repo. Bootstrap success rates in `references/adaptive-routing.md` are author estimates.
- **Compression savings are uneven.** ~20% aggregate on Sonnet, but negative on SINGLE_FILE and ARCHITECTURAL prompts (see measurement doc). Use modes when producing prose; avoid them when producing structured code output.
- **Ollama limits in hybrid mode.** Local models via Ollama can't use Claude Code's tool system (Read, Edit, Bash) — they generate text only. This caps how much work can be offloaded.
- **Escalation uses `git checkout -- .`** to revert failed patches, which discards unstaged changes. Intentional, but destructive if you have uncommitted work outside the current task.

---

## Who this is for

- You spend real money on Claude API calls and want to experiment with output-token reduction (measured) and tier routing (unmeasured but transparent)
- You have a local GPU and want to try offloading simple tasks to Ollama
- You want transparent routing decisions you can inspect and override with `/vex`
- You prefer a skill whose limitations are documented over one that overclaims

---

## Contributing

See [CLAUDE.md](CLAUDE.md) for guidelines. The most valuable contributions right now are:

- Evaluation data: log real tasks with `evaluation/scripts/log_task.sh` and share the JSONL
- Routing-threshold evidence from the routing log
- Language support in `references/impact-analysis.md`
- Additional compression-measurement runs on Opus or Haiku

## License

[MIT](LICENSE)
