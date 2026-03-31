# smart-routing

Intelligent LLM routing skill for Claude Code that minimizes API cost by offloading simple tasks to local Ollama models while keeping complex work on Claude.

## What it does

When you start any coding task, smart-routing automatically:

1. **Classifies** the task (trivial, mechanical, single-file, multi-file, refactor, etc.)
2. **Scores confidence** based on scope clarity, file count, and ambiguity
3. **Analyzes impact** via grep/git to estimate blast radius
4. **Calculates risk** from file types and change patterns
5. **Routes** to the cheapest model that can handle it reliably
6. **Escalates** automatically if a local model fails (with 2 retries per tier)
7. **Learns** from outcomes — logs every routing decision and adjusts future routes based on actual success rates

## Installation

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- [Ollama](https://ollama.ai) installed and running with at least one code model
- `git` and `grep` (standard on most systems)

### Setup

1. Copy the `smart-routing/` folder into your Claude Code skills directory:
   ```bash
   cp -r smart-routing/ ~/.claude/skills/smart-routing/
   ```

2. Edit the **User Configuration** block at the top of `SKILL.md` to match your local Ollama models:
   ```
   OLLAMA_SMALL:    qwen2.5-coder:7b
   OLLAMA_MEDIUM:   qwen2.5-coder:14b
   OLLAMA_LARGE:    deepseek-coder-v2:16b
   OLLAMA_ENDPOINT: http://localhost:11434
   CLOUD_MODEL:     claude-sonnet-4-5
   ```

3. Verify Ollama is running:
   ```bash
   ollama list
   ```

## Usage

### Automatic mode

The skill triggers automatically on any coding task. It silently classifies, scores, and routes — you just see the result.

### Manual audit

Invoke `/smart-routing` in Claude Code to see a full routing audit for the current task:

```
ROUTING AUDIT
-------------
Task class:    SINGLE_FILE (confidence: 0.85)
Impact score:  LOW (1 downstream file)
Risk score:    1 → MEDIUM
Context est.:  ~2400 tokens
Historical:    ollama:medium 4/5 = 80%
Assigned route: ollama:medium
```

## How routing works

| Task type | Low risk | Medium risk | High+ risk |
|---|---|---|---|
| Trivial | ollama:small | ollama:small | claude:plan |
| Mechanical | ollama:medium | claude:plan | claude:full |
| Single file | ollama:medium | ollama:large | claude:plan |
| Multi file | ollama:large | claude:full | claude:full |
| Refactor | claude:plan | claude:full | claude:full |
| Architectural | claude:full | claude:full | claude:full |
| Debugging | ollama:large | claude:full | claude:full |

**Safety overrides** — these always go to Claude regardless of the table:
- Confidence below 0.65
- Impact or risk scored CRITICAL
- Task class is ARCHITECTURAL or RESEARCH

## Adaptive learning

Every routing decision is logged to `references/routing_log.jsonl`. After 3+ data points for a model+task-class combo, routing adjusts:
- Success rate < 40% → skip that model tier
- Success rate > 80% → prefer that tier even at slightly higher risk

## File structure

```
smart-routing/
  SKILL.md                          # Main skill definition
  README.md                         # This file
  CHANGELOG.md                      # Version history
  references/
    adaptive-routing.md             # Adaptive learning spec
    escalation.md                   # Failure detection & recovery
    impact-analysis.md              # Blast radius estimation
    token-ops.md                    # Token optimization techniques
    routing_log.jsonl               # Created at runtime — routing history
```

## Example use cases

- **Solo developer** wanting to cut Claude API costs by 40–70% on routine tasks
- **Team with shared Ollama server** routing boilerplate and formatting tasks locally
- **CI/CD integration** where trivial lint fixes can be handled without API calls
- **Learning tool** — the routing audit teaches you which tasks actually need powerful models

## License

MIT
