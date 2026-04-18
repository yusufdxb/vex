# Changelog

## v1.5.0 — 2026-04-18

### Measured compression data + test suite

- Ran `measure_compression.py --runs 3` on Sonnet: 54 calls (6 prompts × 3 modes × 3 runs). Terse saves **-19.0%** output tokens on average, caveman saves **-21.1%**. Per-class savings range from +52% (DEBUGGING/caveman) to -18% (SINGLE_FILE/terse) — modes help on prose-heavy prompts and hurt on structured-output prompts.
- Replaced `evaluation/PRELIMINARY_COMPRESSION_RESULTS.md` with `evaluation/COMPRESSION_RESULTS.md` — full per-class breakdown, variance ranges, and honest caveats about skill contamination and structured-output regressions.
- Added `tests/test_measure_compression.py` — 21 unit tests covering prompt loading, cost estimation, response parsing, summary computation, and pricing consistency. Stdlib-only (no pytest dependency). Runs in <10ms.
- Added `.github/workflows/tests.yml` — unit tests + Python syntax check on 3.9 / 3.11 / 3.12 for every push and PR to main.
- Rewrote `README.md`: dropped "Experimental" banner, added measured-savings table, split "measured vs not measured" explicitly, tightened limitations section to real constraints (prompt-based, routing unvalidated, compression uneven).
- Updated `EVALUATION.md` status line to reflect that compression is measured and routing data collection is the open item.

## v1.4.2 — 2026-04-17

### Preliminary compression measurement + claude-cli backend

- Added `evaluation/PRELIMINARY_COMPRESSION_RESULTS.md` with first-pass data from a single run on Sonnet (n=1 per combo): terse saves ~29% of output tokens overall, caveman ~45-60% on prose-heavy prompts but with one outlier that zeroed the aggregate. Results clearly marked preliminary with a full caveats section and explicit "what to change before treating as evidence" checklist.
- Added `--backend claude-cli` flag to `evaluation/scripts/measure_compression.py`: shells out to `claude -p --output-format json` so the script can run on a Claude Code subscription without an API key. Default remains `--backend api` for reproducibility by readers without Claude Code.
- Updated `EVALUATION.md` section 4 with both backend invocations and a link to the preliminary results doc.

## v1.4.1 — 2026-04-17

### Compression-mode measurement script

- Added `evaluation/scripts/measure_compression.py` — feeds a fixed prompt set through the Anthropic Messages API in normal, terse, and caveman modes and reports per-mode output tokens, estimated cost, and savings vs. normal (overall and per task class)
- Stdlib-only (no third-party packages); requires `ANTHROPIC_API_KEY`
- Added `evaluation/compression_prompts.jsonl` with 6 prompts spanning TRIVIAL, MECHANICAL, SINGLE_FILE, DEBUGGING, RESEARCH, ARCHITECTURAL classes
- Added "Output compression savings" section to `EVALUATION.md` describing methodology, metrics, caveats
- `evaluation/data/compression_results.jsonl` added to `.gitignore` — no measured results ship with the repo
- Methodology caveat: the script simulates compression via system-prompt injection. It measures whether the rule reduces tokens when the model is instructed to follow it, NOT whether the `/vex terse` or `/vex caveman` slash commands are reliably honored in a real Claude Code session — that requires separate in-session testing

## v1.4.0 — 2026-04-17

### Output compression modes

- Added Step 10 to `SKILL.md`: session-scoped output compression modes to reduce output token cost
- `/vex terse`: full sentences capped at 15 words per reply, no preamble, no markdown headers, no trailing summaries
- `/vex caveman`: 1-5 word replies, broken grammar, no punctuation
- `/vex normal`: reverts to default output style
- Modes compress prose only — code, commit messages, PR bodies, and tool call arguments are unaffected
- Caveman takes precedence if both are somehow active; modes do not persist across sessions
- Added subcommand table to the `/vex` invocation section and a feature summary to `README.md`

## v1.3.0 — 2026-04-02

### Evaluation framework

- Added `evaluation/` directory with complete evaluation workflow
- `METHODOLOGY.md`: study design, metrics definitions, threats to validity, minimum evidence thresholds, acceptable vs. invalid claims
- `SCORING_RUBRIC.md`: 1-5 quality scoring rubric with detailed criteria, pass/fail thresholds, rework severity classification
- `EXPERIMENT_PROTOCOL.md`: daily workflow for logging tasks, field definitions, edge case handling
- `RESULTS_TEMPLATE.md`: structured template for publishing findings with required disclaimers
- `scripts/analyze.py`: summary statistics from evaluation log (cost, quality, routing accuracy, per-class breakdown, data quality warnings)
- `scripts/log_task.sh`: interactive helper for appending JSONL log entries
- `examples/sample_eval_log.jsonl`: sample entries showing the evaluation log format (clearly labeled as non-real data)
- Rewrote `EVALUATION.md` to reference the new framework
- Updated README repo structure and evidence section
- Added evaluation data files to `.gitignore`

## v1.2.0 — 2026-04-02

### Public credibility pass

- Rewrote README: removed unsupported claims (40–70% savings, fabricated latency/cost numbers), added explicit experimental status, limitations section, and honest evidence assessment
- Added EVALUATION.md with evaluation plan and benchmark template (no results yet)
- Added examples/routing_log_example.jsonl with sample log entries
- Labeled bootstrap success rates as author estimates, not measured data
- Added safety warnings around `git checkout -- .` in escalation docs — now recommends `git stash` first
- Replaced marketing tone with technical documentation throughout

## v1.1.0 — 2026-03-31

### Dual-mode routing

- Added **Cloud mode**: Opus (mastermind) → Sonnet (workhorse) → Haiku (grunt) routing
- Added **Hybrid mode**: Claude + Ollama local models (original behavior)
- User Configuration block now supports `ROUTING_MODE: cloud | hybrid`
- Separate routing tables, escalation ladders, and bootstrap success rates for each mode
- Adaptive learning log now includes `mode` field
- Professional repo structure: LICENSE, CLAUDE.md, CODE_OF_CONDUCT.md, .gitignore, .gitattributes

## v1.0.0 — 2026-03-31

### Initial release

- 9-step routing system: classify, impact analysis, risk scoring, context estimation, route, execute, token optimization, escalation, adaptive learning
- Configurable Ollama model tiers (small/medium/large) — no hardcoded model names
- Confidence-based routing with automatic Claude escalation below 0.65
- Impact analysis via grep/git for blast radius estimation
- Generalized risk scoring for any tech stack
- 3-tier escalation ladder with 2 retries per tier
- Adaptive learning via routing_log.jsonl with automatic threshold adjustment
- Token optimization reference guide
- `/vex` command for manual routing audits (originally named `/smart-routing`)
