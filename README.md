# Vex

**Stop paying Opus prices for typo fixes.**

Vex is a Claude Code skill that looks at every coding task before it runs and asks one question: *does this actually need the most expensive model?* If not, it sends it somewhere cheaper. If that fails, it escalates. If it keeps failing, it learns.

Two modes. Zero config hassle.

> **Cloud** — Opus thinks, Sonnet builds, Haiku does the boring stuff.
> **Hybrid** — Claude plans, your local Ollama models do the grunt work for free.

---

### The pitch in 10 seconds

```
You: "rename this variable"
Vex: routes to Haiku (0.3s, ~$0.001)

You: "refactor auth into middleware"
Vex: routes to Opus (full power, full context)

You: "add docstrings to these 12 functions"
Vex: routes to Haiku/Ollama (why waste Opus on boilerplate?)
```

**Result: 40–70% less spend. Same quality. It learns what works.**

---

## How it works

```
                    ┌─────────────┐
                    │  Your Task  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Classify   │  confidence 0.0–1.0
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌──▼───┐ ┌──────▼──────┐
       │   Impact    │ │ Risk │ │   Context   │
       │  Analysis   │ │Score │ │  Estimate   │
       └──────┬──────┘ └──┬───┘ └──────┬──────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │    Route    │◄── learns from history
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
  ┌──────▼──────┐   ┌─────▼─────┐   ┌──────▼──────┐
  │   Tier 1    │   │  Tier 2   │   │   Tier 3    │
  │ Haiku/Local │   │  Sonnet   │   │    Opus     │
  │   (cheap)   │   │(balanced) │   │ (full send) │
  └─────────────┘   └───────────┘   └─────────────┘
```

Nine steps, every task:

1. **Classify** — what kind of task is this? (trivial → architectural)
2. **Impact** — how many files break if this goes wrong?
3. **Risk** — CI configs? DB migrations? Auth code? Score it.
4. **Context** — how many tokens does this need?
5. **Route** — pick the cheapest model that can handle it
6. **Execute** — run it with an optimized prompt
7. **Optimize** — grep before read, diff instead of re-read, no prose
8. **Catch failures** — errors, empty output, corrupt patches → escalate
9. **Learn** — log the outcome, adjust routing next time

---

## Quick start

```bash
git clone https://github.com/yusufdxb/vex.git
cp -r vex/ ~/.claude/skills/vex/
```

Edit the config block at the top of `SKILL.md`:

**Cloud mode** (just Claude, no local models):
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

That's it. Vex triggers automatically on every coding task.

---

## `/vex` — see the routing decision

Run `/vex` in Claude Code to see exactly why a task was routed where it was:

```
ROUTING AUDIT
─────────────
Mode:          cloud
Task class:    SINGLE_FILE (confidence: 0.85)
Impact:        LOW (1 downstream file)
Risk:          1 → MEDIUM
Context:       ~2400 tokens
Historical:    haiku 4/5 = 80% for SINGLE_FILE
Route:         haiku

Overrides:     none
Token waste:   full file read on 400-line file — use grep+offset
```

---

## Routing tables

### Cloud mode

| | Low risk | Med risk | High+ risk |
|---|---|---|---|
| **Trivial** | Haiku | Haiku | Sonnet |
| **Mechanical** | Haiku | Haiku | Sonnet |
| **Single file** | Haiku | Sonnet | Sonnet |
| **Multi file** | Sonnet | Opus | Opus |
| **Refactor** | Sonnet | Opus | Opus |
| **Architectural** | Opus | Opus | Opus |
| **Debugging** | Sonnet | Opus | Opus |

### Hybrid mode

| | Low risk | Med risk | High+ risk |
|---|---|---|---|
| **Trivial** | ollama:small | ollama:small | claude:plan |
| **Mechanical** | ollama:medium | claude:plan | claude:full |
| **Single file** | ollama:medium | ollama:large | claude:plan |
| **Multi file** | ollama:large | claude:full | claude:full |
| **Refactor** | claude:plan | claude:full | claude:full |
| **Architectural** | claude:full | claude:full | claude:full |
| **Debugging** | ollama:large | claude:full | claude:full |

**Hard overrides** — always top tier, no exceptions:
- Confidence below 0.65
- Impact or risk = CRITICAL
- ARCHITECTURAL or RESEARCH tasks

---

## It learns

Every routing decision gets logged:

```json
{"class":"SINGLE_FILE","model":"haiku","success":true,"tokens":400}
```

After 3+ data points per model+task combo:
- **< 40% success** → skipped automatically next time
- **> 80% success** → preferred even at slightly higher risk

Your routing table evolves. Week 1 uses bootstrap estimates. Week 4 uses your data.

---

## Escalation

Models fail. Vex handles it.

**Cloud:** `Haiku → Sonnet → Opus` (2 retries per tier)
**Hybrid:** `small → medium → large → Claude` (2 retries per tier)

Each escalation:
- Passes failure context forward (never repeats the same prompt)
- Reverts partial changes (`git checkout -- .`)
- Logs the failure for adaptive learning

---

## What's inside

```
vex/
├── SKILL.md              # The brain — 9-step routing pipeline
├── references/
│   ├── adaptive-routing.md   # How the learning loop works
│   ├── escalation.md         # Failure detection & recovery
│   ├── impact-analysis.md    # Blast radius estimation
│   ├── token-ops.md          # 8 token optimization techniques
│   └── routing_log.jsonl     # Created at runtime
├── README.md
├── CHANGELOG.md
├── CLAUDE.md             # Contributor guidelines
├── CODE_OF_CONDUCT.md
├── LICENSE               # MIT
├── .gitignore
└── .gitattributes
```

---

## Who is this for

- You're tired of paying Opus rates for `s/foo/bar/g`
- You have a local GPU and want it to earn its keep
- You want to actually see *why* a model was chosen, not just trust vibes
- You want routing that gets smarter over time, not a static heuristic

---

## Philosophy

**Route by evidence.** The log tells you what works. Bootstrap estimates get replaced by real data.

**Fail fast, escalate smart.** Two retries, then move up. Don't burn tokens on a losing bet.

**Minimize tokens, not quality.** Grep before read. Diff instead of re-read. The cheapest token is the one you never use.

**No lock-in.** Cloud mode, hybrid mode, swap models in one config block.

---

## Contributing

Fork it, branch it, PR it. See [CLAUDE.md](CLAUDE.md) for guidelines.

## License

[MIT](LICENSE)

## Links

- [Issues](https://github.com/yusufdxb/vex/issues)
- [Changelog](CHANGELOG.md)
