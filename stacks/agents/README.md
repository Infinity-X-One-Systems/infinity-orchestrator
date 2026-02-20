# Agent Fleet

This directory contains the Python agents that power the Infinity Autonomous Engine.

## Agents

| Agent | Role | Phase |
|-------|------|-------|
| `discovery_agent.py` | Discover external signals from GitHub and news feeds | Phase 1 |
| `scoring_agent.py` | Score and rank signals across 5 dimensions | Phase 2 |
| `sandbox_agent.py` | Scaffold new repositories for top-scored ideas | Phase 3 |
| `validator_agent.py` | Enforce TAP governance checks | Phase 4 |
| `reporter_agent.py` | Generate Markdown run reports for GitHub Pages | Phase 5 |

## Shared Prompt Library

Agent roles, inputs, outputs, and audit checks are defined in
[`../prompts/agent_prompts.yml`](../prompts/agent_prompts.yml).

## Invocation

Each agent is invoked from the
[`autonomous-invention.yml`](../../.github/workflows/autonomous-invention.yml) workflow.
They can also be run locally:

```bash
python stacks/agents/discovery_agent.py --org Infinity-X-One-Systems --output /tmp/index.json
python stacks/agents/scoring_agent.py   --input /tmp/index.json --output /tmp/scorecard.json
python stacks/agents/validator_agent.py --repo-root . --output /tmp/tap_report.json
```
