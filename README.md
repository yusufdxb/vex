# Vex

A Claude Code skill that routes coding tasks to cheaper model tiers when full-power models aren't needed.

> **Status: Experimental.** Vex is a prompt-based routing heuristic, not battle-tested infrastructure. It has no benchmarks, no production usage data, and no measured savings yet. Use it if the idea interests you and you want to help validate it.

---

## What it is

Vex is a [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code) — a structured prompt that Claude reads and follows. It classifies each coding task by complexity, estimates risk and blast radius, then routes to the cheapest model tier that should be able to handle it. If that tier fails, it escalates.

It is **not** a standalone application, API, or runtime. It's a `.md` file that changes how Claude Code behaves.

**Two modes:**
- **Cloud** — routes between Opus, Sonnet, and Haiku based on task complexity
- **Hybrid** — routes between local Ollama models and Claude, keeping simple tasks local

---

## How routing works

```
Task → Classify → Impact analysis → Risk score → Context estimate → Route → Execute → Log outcome
```

Each task goes through:

1. **Classify** — what kind of task? (trivial rename → full architectural change)
2. **Impact** — how many files reference the symbol being changed?
3. **Risk** — does it touch CI, auth, migrations, or other sensitive areas?
4. **Context** — how many tokens does the task need?
5. **Route** — pick the cheapest tier that fits the classification
6. **Execute** — run with an optimized prompt for that tier
7. **Catch failures** — detect errors, empty output, corrupt patches → escalate to next tier
8. **Log** — record the outcome for future routing adjustments

### Routing tables

**Cloud mode:**

| | Low risk | Med risk | High+ risk |
|---|---|---|---|
| **Trivial** | Haiku | Haiku | Haiku |
| **Mechanical** | Haiku | Haiku | Sonnet |
| **Single file** | Haiku | Sonnet | Sonnet |
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

> These tables are simplified summaries. Hybrid mode routing also depends on context size — see `SKILL.md` for the full routing logic.

**Hard overrides** — always routed to the top tier:
- Classification confidence below 0.65
- Impact or risk scored as CRITICAL
- ARCHITECTURAL or RESEARCH tasks

---

## Quick start

```bash
git clone https://github.com/yusufdxb/vex.git
cp -r vex/ ~/.claude/skills/vex/
```

Edit the config block at the top of `SKILL.md`:

**Cloud mode** (Claude models only):
```
ROUTING_MODE:  cloud
TIER_1:        claude-haiku-4-5
TIER_2:        claude-sonnet-4-5
TIER_3:        claude-opus-4-6
```

**Hybrid mode** (Claude + Ollama):
```
ROUTING_MODE:    hybrid
OLLAMA_SMALL:    qwen2.5-coder:7b
OLLAMA_MEDIUM:   qwen2.5-coder:14b
OLLAMA_LARGE:    deepseek-coder-v2:16b
OLLAMA_ENDPOINT: http://localhost:11434
CLOUD_MODEL:     claude-sonnet-4-5
```

Once installed, the skill prompt is available to Claude Code on every task. Whether Claude follows it depends on how it interprets the skill — there is no runtime enforcement.

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

The skill instructs Claude to log every routing decision to `references/routing_log.jsonl`. After 3+ data points per model+task combination, routing is designed to adjust:

- **< 40% success rate** → that tier is skipped for that task type
- **> 80% success rate** → that tier is preferred even at slightly higher risk

Until enough data accumulates, routing uses author-estimated bootstrap rates (see `references/adaptive-routing.md`). These estimates are not measured — they are starting-point guesses that get replaced by your actual data.

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
│   ├── scripts/
│   │   ├── analyze.py           # Summary statistics from eval log
│   │   └── log_task.sh          # Interactive helper to log entries
│   ├── examples/
│   │   └── sample_eval_log.jsonl  # Example entries (SAMPLE, not real)
│   └── data/                    # Your evaluation data (gitignored)
├── examples/
│   └── routing_log_example.jsonl  # Sample routing log entries
├── EVALUATION.md                # Evaluation plan (no results yet)
├── CHANGELOG.md
├── CLAUDE.md                    # Contributor guidelines
├── CODE_OF_CONDUCT.md
├── LICENSE                      # MIT
└── README.md
```

---

## Limitations

- **No measured savings.** The premise — that routing saves money without sacrificing quality — is plausible but unproven for this implementation. Cost reduction depends entirely on how often cheaper tiers succeed for your workload.
- **Prompt-based, not enforced.** Vex is a set of instructions Claude follows. There is no runtime enforcement, no type checking, no guaranteed execution path. Claude interprets the skill prompt and may deviate.
- **Bootstrap estimates are guesses.** The initial success rates in `references/adaptive-routing.md` are author estimates, not empirical measurements. They exist to seed the routing tables until real data accumulates.
- **Ollama limitations.** Local models via Ollama cannot use Claude Code's tool system (Read, Edit, Bash). They generate text only. This limits what tasks can actually be offloaded in hybrid mode.
- **No evaluation results.** There are no benchmarks, A/B tests, or controlled comparisons. See `EVALUATION.md` for the planned evaluation approach.
- **Escalation uses `git checkout -- .`** to revert failed patches, which discards all unstaged changes. This is intentional but destructive — any uncommitted work outside the current task will be lost.

---

## Current evidence

**Honest status: none.**

There are no routing logs, benchmark results, or production usage reports. The routing tables and bootstrap estimates are based on the author's judgment about model capabilities, not measured outcomes.

An evaluation framework is available in `evaluation/` with a methodology, scoring rubric, experiment protocol, analysis scripts, and results template. See `EVALUATION.md` for the full plan.

What would constitute evidence:
- 50+ logged routing decisions across diverse task types (use `evaluation/scripts/log_task.sh`)
- Measured cost comparison against an Opus-only baseline
- Quality scores assigned per the rubric in `evaluation/SCORING_RUBRIC.md`
- Results published using `evaluation/RESULTS_TEMPLATE.md` with all caveats

If you generate this data, please share it via an issue or PR.

---

## Who this is for

- You spend significant money on Claude API calls and want to experiment with cost reduction
- You have a local GPU and want to try offloading simple tasks to Ollama
- You want transparent routing decisions you can inspect and override
- You're comfortable using an experimental, unvalidated tool

---

## Contributing

See [CLAUDE.md](CLAUDE.md) for guidelines. Evidence-backed improvements to routing thresholds, new language support for impact analysis, and evaluation data are especially welcome.

## License

[MIT](LICENSE)
