# Contributor Guidelines

## For AI Agents

Before submitting a pull request, you must:

1. **Read the complete PR diff** and verify every change is intentional
2. **Search for duplicate PRs** (both open and closed) to avoid redundant submissions
3. **Verify actual problems exist** — don't act on vague improvement requests
4. **Get explicit human approval** of the complete diff before submission

Submitting low-quality PRs wastes maintainer time. If you're unsure, open an issue first.

## What We Accept

- Bug fixes with clear reproduction steps
- New risk signals or confidence scoring improvements backed by evidence
- Additional language support in impact analysis commands
- Token optimization techniques with measured savings
- Documentation improvements that fix actual confusion
- Escalation ladder improvements with test evidence

## What We Don't Accept

- Third-party dependencies (this skill is zero-dependency by design)
- Domain-specific risk signals (keep it general-purpose)
- Hardcoded model names or machine-specific paths
- Changes to routing thresholds without routing log evidence
- Speculative improvements without real problem statements
- Bundled unrelated changes (split into separate PRs)

## Modifying the Routing Pipeline

The 9-step pipeline in SKILL.md is the core of this skill. Changes to it require:

- A clear description of the problem the change solves
- Evidence from routing logs or real-world usage
- Verification that existing routing behavior isn't broken
- Updated reference docs if the change touches adaptive-routing, escalation, impact-analysis, or token-ops

## Style

- Keep all files in Markdown
- Use tables for structured data
- Use code blocks for commands and examples
- No emojis in documentation
- Be direct — say what something does, not what it "aims to" or "helps with"
