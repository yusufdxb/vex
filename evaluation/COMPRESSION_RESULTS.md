# Compression-mode measurement

**Measured 2026-04-18.** 54 calls — 6 prompts × 3 modes (normal, terse, caveman) × 3 runs — against `claude-sonnet-4-5` via `claude -p --output-format json --tools "" --no-session-persistence`, with the mode rule injected via `--append-system-prompt`. Raw data in `evaluation/data/compression_results.jsonl` (gitignored).

Reproduce:

```bash
python3 evaluation/scripts/measure_compression.py --backend claude-cli --runs 3
```

## Per-mode summary (n=18 per mode)

| Mode    | Avg output tokens | Total output | vs normal |
|---------|-------------------|--------------|-----------|
| normal  | 845               | 15,201       | —         |
| terse   | 684               | 12,309       | **-19.0%** |
| caveman | 666               | 11,992       | **-21.1%** |

## Per-class, per-mode (avg across 3 runs, positive = savings)

| Class          | normal | terse (Δ)    | caveman (Δ)  |
|----------------|-------:|-------------:|-------------:|
| TRIVIAL        | 1012   | 621 (+39%)   | 573 (+43%)   |
| MECHANICAL     | 641    | 557 (+13%)   | 620 (+3%)    |
| SINGLE_FILE    | 717    | 846 (-18%)   | 736 (-3%)    |
| DEBUGGING      | 855    | 700 (+18%)   | 411 (+52%)   |
| RESEARCH       | 1136   | 598 (+47%)   | 840 (+26%)   |
| ARCHITECTURAL  | 707    | 781 (-10%)   | 818 (-16%)   |

## What the data says

**Modes reliably save tokens on prose-heavy prompts.** DEBUGGING, RESEARCH, and TRIVIAL are the clear wins — terse cuts 18-47%, caveman cuts 26-52%. These are the prompt classes where the model would otherwise produce long explanations.

**Modes can hurt on structural-output prompts.** SINGLE_FILE and ARCHITECTURAL show negative savings in some cells — the mode rule fights with "output the full function" or "give reasoning with tradeoffs", and the model either over-pads short replies or produces a messy long reply that costs more than the clean normal version. If the task requires a specific code block or structured answer, the compression mode is worse than normal.

**Variance is high at n=3.** Per-prompt min/max spreads are wide: ARCHITECTURAL caveman ranged 332–1699 across three runs, DEBUGGING terse ranged 366–1168. A single bad call can flip the aggregate sign of that cell. Ranges should be read as directional, not precise.

**Skill contamination is still present.** `claude -p` loads the user's installed skills by default. Some replies begin with meta-skill preambles ("I'll check for relevant skills before responding") that inflate the token counts in all three modes. This makes the baseline noisier than it should be; using `--bare` would isolate the model from skills but disables subscription auth and requires `ANTHROPIC_API_KEY`. The 19-21% aggregate savings is the contaminated-baseline number; the clean-baseline savings could be higher or lower.

## Provisional guidance

Use compression modes when:

- The task is prose-heavy (debugging explanations, research/how-does, trivial rename with context)
- You're in a long session where output tokens dominate cost

Avoid compression modes when:

- The task output is structured (code block, PR body, commit message, design doc)
- The task is ARCHITECTURAL or SINGLE_FILE — the data shows they can make replies longer, not shorter

## Caveats

1. **Measured on Sonnet only.** No Haiku or Opus data. Compliance with the mode rule is likely model-dependent.
2. **Claude-cli backend includes skill contamination.** See above.
3. **Output tokens only.** Code written to files via Edit/Write, tool call arguments, and input tokens are all unaffected by these modes.
4. **6 prompts is a small set.** Each class has only one representative prompt. A larger prompt set would smooth per-class noise.
5. **Measures prompt-injected rule compliance, not slash-command behavior.** The script tests whether the model follows a rule when instructed to. Whether Claude Code correctly honors `/vex terse` and `/vex caveman` in a real session is a separate, in-session question not covered by this measurement.

## What would strengthen these numbers

- Repeat with `--runs 5` on a 15+ prompt set weighted toward prose-heavy tasks
- Run the same measurement against `claude-haiku-4-5` and `claude-opus-4-6`
- Resolve skill contamination — either use `--bare` with an API key, or document the contaminated baseline and keep it consistent
- Log actual per-session cost in dollars against a real plan, not estimated-from-pricing-table cost
