# Preliminary compression-mode measurement — 2026-04-17

> **Status: Preliminary.** Single run, n=1 per (prompt, mode) combo. Results below are first-look data, not verified evidence. See the "Caveats" section before citing any number.

## Methodology

- 6 prompts from `evaluation/compression_prompts.jsonl` (TRIVIAL, MECHANICAL, SINGLE_FILE, DEBUGGING, RESEARCH, ARCHITECTURAL).
- 3 modes: `normal`, `terse`, `caveman`.
- Backend: `claude -p --output-format json --tools "" --no-session-persistence --model sonnet`, with the mode rule injected via `--append-system-prompt`.
- Token counts taken from the JSON result's `usage.output_tokens` field.
- 18 total calls, run 2026-04-17.

Reproduce via the committed measurement script:

```bash
python3 evaluation/scripts/measure_compression.py --backend claude-cli --runs 3
```

## Per-mode summary

| Mode    | N | Avg out | Total out | vs normal |
|---------|---|---------|-----------|-----------|
| normal  | 6 | 245.2   | 1471      | —         |
| terse   | 6 | 173.7   | 1042      | **-29.2%** |
| caveman | 6 | 245.5   | 1473      | ≈ 0% *(distorted — see caveat 1)* |

## By task class (avg output tokens)

| Class          | normal | terse | caveman | Notes |
|----------------|--------|-------|---------|-------|
| TRIVIAL        | 49     | 49    | 49      | Replies identical — mode ignored |
| MECHANICAL     | 89     | 89    | 89      | Replies identical — mode ignored |
| SINGLE_FILE    | 75     | 54    | 42      | 28% / 44% savings |
| DEBUGGING      | 220    | 130   | 845     | Caveman outlier — model rebelled |
| RESEARCH       | 759    | 499   | 346     | 34% / 54% savings |
| ARCHITECTURAL  | 279    | 221   | 102     | 21% / 63% savings |

## Caveats

1. **Caveman DEBUGGING outlier.** The single `debugging_trace/caveman` call reported 845 output tokens (vs 220 for normal). The reply text itself was only 278 characters — the token inflation may reflect extended-thinking tokens on that session, or a transient model deviation. Drop this call and the per-prompt caveman average is ~46% lower than normal; keep it and caveman shows 0% aggregate savings.
2. **Skill contamination.** `claude -p` loads the user's installed skills by default. The `research_concept/terse` reply literally began with *"I'll check for relevant skills before responding."* — that is Claude Code's superpowers meta-skill bleeding through, not the model responding to the prompt. Using `--bare` would isolate the measurement but disables OAuth/subscription auth. Tradeoff not resolved for this run.
3. **TRIVIAL / MECHANICAL prompts are uncompressible.** When the prompt says "output the full updated function" or "add a docstring", the direct instruction outranks the mode rule and all three modes produce the same code block. This is expected behavior, not a bug — modes compress *prose*, and these prompts have almost none.
4. **n=1 per combo.** A single bad call dominates the aggregate. The `--runs 3` flag in the script exists for this reason; it was not used here.
5. **Output tokens only.** Code written to files via Edit/Write, tool call arguments, and input tokens are all unaffected by these modes. A session dominated by tool use will see smaller total savings than the prose-only table above suggests.
6. **Model: Sonnet.** Measured on `claude-sonnet-4-5` only. Caveman and terse compliance likely varies by model. No Opus or Haiku data.

## Provisional takeaway

On prose-heavy tasks (RESEARCH, ARCHITECTURAL, DEBUGGING) with Sonnet:

- `terse` saves roughly **25–40%** of output tokens.
- `caveman` saves roughly **45–60%** on the prompts where the model complies, but compliance is not 100% — at least one call in six produced an outlier.

These ranges are based on six prompts in one run. They are not verified evidence. Treat as directional until a `--runs >= 3` measurement across 15+ prose-heavy prompts is logged.

## What to change before treating this as evidence

- Rerun with `--runs 3` (minimum) or `--runs 5` (preferred) to smooth variance.
- Expand the prompt set to 15+ items; drop TRIVIAL and MECHANICAL since modes cannot affect them.
- Resolve the skill-contamination issue: either use `--bare` with the API backend, or document the skill-contaminated baseline explicitly and keep it consistent across runs.
- Repeat on Opus and Haiku to check whether compliance and savings are model-dependent.
- Log cost per session in dollars against the user's actual plan (not just tokens).
