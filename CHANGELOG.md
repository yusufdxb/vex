# Changelog

## v1.0.0 — 2026-03-31

### Initial release

- 9-step routing system: classify, impact analysis, risk scoring, context estimation, route, execute, token optimization, escalation, adaptive learning
- Configurable Ollama model tiers (small/medium/large) — no hardcoded model names
- Confidence-based routing with automatic Claude escalation below 0.65
- Impact analysis via grep/git for blast radius estimation
- Generalized risk scoring for any tech stack (no domain-specific signals)
- 3-tier escalation ladder with 2 retries per tier
- Adaptive learning via routing_log.jsonl with automatic threshold adjustment
- Token optimization reference guide
- `/smart-routing` command for manual routing audits

### Forked from

Private `optimize-usage` skill — stripped of Codex integration, machine-specific paths, and domain-specific (ROS2) risk signals. Generalized for public use.
