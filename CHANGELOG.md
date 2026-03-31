# Changelog

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
- `/smart-routing` command for manual routing audits
