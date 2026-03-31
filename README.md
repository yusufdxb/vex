# Smart Routing

An intelligent LLM routing skill for Claude Code that picks the right model for every task — so you stop overpaying for typo fixes and underpowering architecture decisions.

## How it works

Every time you start a coding task, Smart Routing steps back and asks: does this task actually need the most expensive model?

It classifies the task by complexity, estimates blast radius via grep and git, scores risk from file types and change patterns, and routes to the cheapest model that can handle it reliably. If that model fails, it escalates automatically — passing failure context forward, not just retrying the same prompt.

**Two routing modes:**

- **Cloud mode** — Opus is the mastermind, Sonnet does the heavy lifting, Haiku handles the grunt work. No local setup needed.
- **Hybrid mode** — Claude handles planning and verification, local Ollama models execute the simple stuff for free.

The result: 40–70% cost reduction with no loss in quality, because the hard tasks still go to the strongest model. And because the skill triggers automatically, you don't need to do anything special.

```
                    ┌─────────────┐
                    │  Your Task  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Classify   │  confidence score 0.0–1.0
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
                    │    Route    │◄── adaptive learning
                    └──────┬──────┘    (routing_log.jsonl)
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
  ┌──────▼──────┐   ┌─────▼─────┐   ┌──────▼──────┐
  │   Tier 1    │   │  Tier 2   │   │   Tier 3    │
  │ Haiku/Small │   │Sonnet/Med │   │ Opus/Large  │
  │  (trivial)  │   │ (standard)│   │  (complex)  │
  └─────────────┘   └───────────┘   └─────────────┘
```

## Installation

### Claude Code (recommended)

Clone the repo and copy it into your Claude Code skills directory:

```bash
git clone https://github.com/yusufdxb/claude-smart-routing.git
cp -r claude-smart-routing/ ~/.claude/skills/smart-routing/
```

### Manual installation

Download and extract the [latest release](https://github.com/yusufdxb/claude-smart-routing/releases) into `~/.claude/skills/smart-routing/`.

### Prerequisites

| Dependency | Required for | Install |
|---|---|---|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Both modes | See Anthropic docs |
| git | Both modes | Pre-installed on most systems |
| [Ollama](https://ollama.ai) | Hybrid mode only | `curl -fsSL https://ollama.ai/install.sh \| sh` |

### Verify your setup

```bash
# For hybrid mode — check Ollama is running
ollama list

# Pull a starter model if you don't have one
ollama pull qwen2.5-coder:7b
```

## Configuration

Edit the **User Configuration** block at the top of `SKILL.md`.

### Cloud Mode (no local setup)

```
ROUTING_MODE:  cloud
TIER_1:        claude-haiku-4-5     # fast, cheap — trivial tasks
TIER_2:        claude-sonnet-4-5    # balanced — standard dev work
TIER_3:        claude-opus-4-6      # full power — architecture, refactors
```

### Hybrid Mode (Claude + Ollama)

```
ROUTING_MODE:    hybrid
OLLAMA_SMALL:    qwen2.5-coder:7b
OLLAMA_MEDIUM:   qwen2.5-coder:14b
OLLAMA_LARGE:    deepseek-coder-v2:16b
OLLAMA_ENDPOINT: http://localhost:11434
CLOUD_MODEL:     claude-sonnet-4-5
```

## The Nine-Step Pipeline

1. **Classify** — assign a task class (TRIVIAL through ARCHITECTURAL) with a confidence score
2. **Impact analysis** — grep + git to estimate how many files break if this goes wrong
3. **Risk scoring** — sum risk signals from file types, scope, and change patterns
4. **Context estimation** — calculate token budget from file sizes
5. **Route** — match inputs against routing table, check adaptive overrides
6. **Execute** — send to the assigned model with optimized prompts
7. **Optimize tokens** — grep-before-read, parallel calls, diff-based context
8. **Detect failures** — catch errors, empty outputs, corrupt patches, then escalate
9. **Learn** — log outcome, adjust future routing based on actual success rates

## Usage

### Automatic mode

The skill triggers automatically when you start any coding task in Claude Code. It silently classifies, scores, and routes. No commands needed.

### Manual routing audit

Invoke `/smart-routing` in Claude Code to see the full decision breakdown:

```
ROUTING AUDIT
─────────────
Mode:          cloud
Task class:    SINGLE_FILE (confidence: 0.85)
Impact score:  LOW (1 downstream file)
Risk score:    1 → MEDIUM
Context est.:  ~2400 tokens
Historical:    haiku 4/5 = 80% for SINGLE_FILE
Assigned route: haiku

Overrides triggered:
  none

Offload opportunities:
  Tier 1: rename variable, add docstring to helper
  Tier 2: implement feature from spec

Token waste found:
  Full file read on 400-line file — use grep+offset instead
```

## Routing Tables

### Cloud Mode

| Task type | Low risk | Medium risk | High+ risk |
|---|---|---|---|
| **Trivial** | Haiku | Haiku | Sonnet |
| **Mechanical** | Haiku | Haiku | Sonnet |
| **Single file** | Haiku | Sonnet | Sonnet |
| **Multi file** | Sonnet | Opus | Opus |
| **Refactor** | Sonnet | Opus | Opus |
| **Architectural** | Opus | Opus | Opus |
| **Debugging** | Sonnet | Opus | Opus |

### Hybrid Mode

| Task type | Low risk | Medium risk | High+ risk |
|---|---|---|---|
| **Trivial** | ollama:small | ollama:small | claude:plan |
| **Mechanical** | ollama:medium | claude:plan | claude:full |
| **Single file** | ollama:medium | ollama:large | claude:plan |
| **Multi file** | ollama:large | claude:full | claude:full |
| **Refactor** | claude:plan | claude:full | claude:full |
| **Architectural** | claude:full | claude:full | claude:full |
| **Debugging** | ollama:large | claude:full | claude:full |

**Safety overrides** — always routed to the highest tier:
- Confidence below 0.65
- Impact or risk scored CRITICAL
- Task class is ARCHITECTURAL or RESEARCH

## Adaptive Learning

Every routing decision is logged to `references/routing_log.jsonl`:

```json
{"date":"2026-03-29","class":"SINGLE_FILE","mode":"cloud","model":"haiku","success":true,"tokens":400}
```

After 3+ data points for any model + task-class combination:
- **Success rate < 40%** — that tier is skipped automatically
- **Success rate > 80%** — that tier is preferred even at slightly higher risk

The skill gets smarter the more you use it. Your routing table evolves to match your actual codebase.

## Escalation

When a model fails, smart-routing doesn't give up — it escalates:

### Cloud Mode
```
Haiku → Sonnet → Opus
  ↑        ↑
2 retries  2 retries
```

### Hybrid Mode
```
ollama:small → ollama:medium → ollama:large → claude:full
       ↑              ↑              ↑
   2 retries      2 retries      2 retries
```

On each escalation:
- Failure context is passed forward (not the same prompt repeated)
- Partial changes are reverted (`git checkout -- .`)
- The failure is logged for adaptive learning

## What's Inside

### Core

- **SKILL.md** — The complete 9-step routing pipeline with both cloud and hybrid mode routing tables, execution templates, and adaptive learning

### Reference Docs

- **adaptive-routing.md** — Routing log format, bootstrap success rates for both modes, threshold adjustment algorithm
- **escalation.md** — Failure detection signals, per-tier recovery for both cloud and hybrid modes, post-corruption recovery
- **impact-analysis.md** — Blast radius estimation commands for any language/build system, impact score thresholds
- **token-ops.md** — Eight concrete techniques for reducing token consumption

## Project Structure

```
smart-routing/
├── SKILL.md                        # Core skill definition (9-step pipeline)
├── README.md                       # This file
├── CHANGELOG.md                    # Version history
├── CLAUDE.md                       # Contributor guidelines
├── CODE_OF_CONDUCT.md              # Community standards
├── LICENSE                         # MIT
├── .gitignore
├── .gitattributes
└── references/
    ├── adaptive-routing.md         # Adaptive learning specification
    ├── escalation.md               # Failure detection & recovery playbook
    ├── impact-analysis.md          # Blast radius estimation methods
    ├── token-ops.md                # Token optimization techniques
    └── routing_log.jsonl           # Created at runtime
```

## Use Cases

- **Cloud-only user** who wants Opus-level quality but doesn't want to pay Opus prices for every typo fix
- **Solo developer** with a local GPU running Ollama, routing boilerplate tasks for free
- **Team with shared Ollama server** handling formatting, renames, and docstrings locally
- **Cost-conscious projects** where every API call needs justification
- **Learning tool** — the routing audit teaches you which tasks actually need powerful models

## Philosophy

- **Route by evidence, not intuition.** The routing log tells you what actually works for your codebase. Bootstrap estimates get replaced by real data.
- **Fail fast, escalate smart.** Two retries per tier, then move up. Don't burn tokens on a model that can't handle the task.
- **Minimize tokens, not quality.** Grep before read. Diff instead of re-read. The cheapest token is the one you don't use.
- **No vendor lock-in.** Cloud mode works with Claude models. Hybrid mode works with any Ollama-compatible model. Swap by changing one config block.

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a branch for your change
3. Follow the structure in `SKILL.md` and `references/` for any routing or analysis changes
4. Submit a PR with a clear description of what changed and why

See [CLAUDE.md](CLAUDE.md) for detailed contributor guidelines and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.

## License

[MIT](LICENSE) — use it however you want.

## Support

- **Issues**: https://github.com/yusufdxb/claude-smart-routing/issues
