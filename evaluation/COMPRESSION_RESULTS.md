# Compression-mode measurement

**Measured 2026-04-18.** 90 calls — 6 prompts × 5 modes (normal, terse, caveman, tight, ghost) × 3 runs — against `claude-sonnet-4-6` via `claude -p --output-format json --tools "" --no-session-persistence`, with the mode rule injected via `--append-system-prompt`. Raw data in `evaluation/data/compression_results.jsonl` (gitignored).

Reproduce:

```bash
python3 evaluation/scripts/measure_compression.py --backend claude-cli --runs 3
```

## The headline finding

**Compression modes are class-specific tools, not general compressors.** In aggregate across all 6 prompt classes, only `terse` saves any tokens (-6%), and `tight` / `caveman` actively cost *more* tokens than `normal`. But each individual class has a mode that cuts output 28-55%. The right move is to match the mode to the task class, not pick one "best" mode.

## Per-mode summary (n=18 per mode)

| Mode    | Mean  | Median | Stdev | vs normal (mean) | vs normal (median) |
|---------|------:|-------:|------:|-----------------:|-------------------:|
| normal  | 845   | 892    | 352   | —                | —                  |
| terse   | 794   | 780    | 356   | **-6.0%**        | -12.6%             |
| caveman | 922   | 718    | 482   | +9.1%            | -19.5%             |
| tight   | 976   | 778    | 593   | +15.5%           | -12.8%             |
| ghost   | 865   | 822    | 468   | +2.4%            | -7.8%              |

Mean-vs-median divergence indicates heavy right-tail: a small number of rebellion calls (where the model spat out 2000+ tokens against the mode rule) drags the aggregate mean well above the median. **Read the medians as the typical case, the means as "aggregate with tail risk."**

## Per-class best mode (this is the actionable table)

| Class          | Best mode | Avg tokens | Saves vs normal |
|----------------|-----------|-----------:|----------------:|
| TRIVIAL        | ghost     | 345        | **-55%**        |
| MECHANICAL     | tight     | 476        | **-47%**        |
| RESEARCH       | terse     | 540        | **-40%**        |
| ARCHITECTURAL  | ghost     | 700        | **-33%**        |
| SINGLE_FILE    | terse     | 729        | **-28%**        |
| DEBUGGING      | terse     | 434        | -5% (marginal)  |

## Full per-class, per-mode table

Avg output tokens (bold = best mode for that class):

| Class          | normal | terse | caveman | tight | ghost |
|----------------|-------:|------:|--------:|------:|------:|
| TRIVIAL        | 775    | 1023  | 647     | 613   | **345** |
| MECHANICAL     | 891    | 1156  | 996     | **476** | 498 |
| SINGLE_FILE    | 1011   | **729** | 1637 | 1636  | 1012  |
| DEBUGGING      | 459    | **434** | 507  | 940   | 1408  |
| RESEARCH       | 895    | **540** | 568  | 1298  | 1228  |
| ARCHITECTURAL  | 1038   | 883   | 1179    | 895   | **700** |

## What worked, what didn't

**Works:**
- `ghost` on TRIVIAL and ARCHITECTURAL — the 10-word `done:` format holds up when the task has a clean terminal state ("renamed", "use gRPC for internal RPC").
- `tight` on MECHANICAL — dropping preamble/summary around a one-liner docstring is most of the call's output, so removing it cuts heavily.
- `terse` on RESEARCH, SINGLE_FILE, DEBUGGING — the 15-word cap forces compression of explanation prose that normal mode pads with.

**Doesn't work:**
- Any mode on DEBUGGING except terse — `tight` and `ghost` both more than *doubled* the DEBUGGING output (+105% and +207%). The model rebelled hard against the compression rule when asked to diagnose an error.
- `tight` on SINGLE_FILE and RESEARCH — output went UP, not down. The `tight` rule is too soft; the model produced a normal-length reply without the preamble, which happened to be longer overall on average.
- `caveman` on SINGLE_FILE, MECHANICAL, ARCHITECTURAL — output went UP. Caveman has zero-article rules that the model either ignored (producing normal replies plus compliance preamble) or half-obeyed (producing both broken-grammar and normal versions).

## High-variance cells (spread > 1000 tokens across 3 runs)

- `SINGLE_FILE/tight`: 704 – 2711 (spread 2007)
- `TRIVIAL/terse`: 573 – 1663 (spread 1090)

Both are cases where one of the three runs produced a rebellion reply. n=3 is not enough to smooth these; a larger run (n=5 or more) on just these cells would help bracket the true cost.

## Why aggregate changed from the v1.5.0 run

The previous 54-call run reported terse -19% and caveman -21%. This 90-call run reports terse -6% and caveman +9%. The same `claude-cli` backend was used both times. The difference is almost entirely **skill contamination and per-run noise**:

- Each `claude -p` invocation loads the user's installed Claude Code skills by default. Those skills produce a meta-preamble ("I'll check for relevant skills before responding") that inflates all three modes' baseline output unpredictably.
- With n=3 per cell, a single inflated reply moves the mean by hundreds of tokens.
- The aggregate -19% terse figure from v1.5.0 was within the noise floor of this n=3 measurement, not a stable property of terse mode.

**Read the current numbers as directional, not precise.** The per-class best-mode recommendations are robust (each winner beats normal in at least 2 of 3 runs) but the exact savings percentages will move with more data.

## Caveats

1. **Sonnet only.** No Haiku or Opus data. Mode compliance is probably model-dependent.
2. **Skill contamination of baseline.** `--bare` mode would isolate this but requires `ANTHROPIC_API_KEY` and loses the subscription backend.
3. **6 prompts total.** One representative per class. A larger prompt set is needed before any class-specific claim carries real weight.
4. **n=3 per cell.** Insufficient to smooth rebellion spikes; the medians are more reliable than the means.
5. **Output tokens only.** Code via Edit/Write, tool call arguments, and input tokens are unaffected.
6. **Measures prompt-rule compliance, not `/vex` slash-command behavior.** Real in-session compliance with `/vex tight` etc. is a separate in-session audit.

## Recommended usage (based on this data)

Instead of toggling one compression mode manually, **match the mode to the classification**:

- Default the skill to `/vex auto`, which picks the mode from the classification step
- For manual override, use the "best mode" table above
- For DEBUGGING tasks, leave compression off — the data says every mode except terse rebelled, and terse only saves 5%. Not worth the risk.

## What would strengthen these numbers

- Rerun with `--runs 5` or `--runs 10` on the rebellion-prone cells (SINGLE_FILE/tight, TRIVIAL/terse) to bracket the true rebellion rate.
- Expand the prompt set to 3+ prompts per class.
- Resolve skill contamination: either `--bare` + API key, or document and hold the contaminated baseline constant across the longitudinal study.
- Repeat on Haiku and Opus to check whether the per-class best-mode mapping is model-invariant.
