# Celebrity AI Guardrails

> **Org:** Infinity-X-One-Systems  
> **Scope:** All AI-generated content, personas, simulations, and discovery outputs.  
> **Version:** 1.0.0  
> **Enforcement:** Absolute. No override permitted.

---

## 1. Purpose

The **Celebrity AI Guardrails** define hard boundaries for AI content generation,
persona simulation, brand safety, and data consent within the Infinity system.
These rules protect users, third parties, and the organization from harmful,
deceptive, or legally risky AI outputs.

---

## 2. Absolute Prohibitions (Cannot Be Overridden)

| Rule | Description |
|------|-------------|
| `CAG-001` | **No impersonation.** Do not generate content that simulates, mimics, or impersonates any real person — public figure, celebrity, or otherwise — without verified written consent and approved training data. |
| `CAG-002` | **No defamation.** Do not generate false statements of fact about any real person or organization. |
| `CAG-003` | **No non-consensual deepfakes.** Do not generate synthetic images, audio, or video of real people without consent. |
| `CAG-004` | **No minor exposure.** Do not generate any content involving minors in a harmful, romantic, or exploitative context. Absolute prohibition. |
| `CAG-005` | **No harmful content.** Do not generate instructions for self-harm, violence against persons, creation of weapons, or illegal activities. |
| `CAG-006` | **No PII extraction.** Do not store, log, or transmit personally identifiable information (PII) in `.infinity/` artifacts, telemetry, or vector store documents. |
| `CAG-007` | **No credential leakage.** API keys, tokens, and passwords must never appear in any AI-generated output, commit message, PR body, or issue comment. |

---

## 3. Brand Safety Rules

All AI-generated content that will be published must pass the following checks:

- **Factual accuracy**: Claims must be verified against trusted sources or clearly labelled as AI-generated speculation.
- **Source attribution**: Content derived from external sources must cite the source.
- **Disclaimer required**: Any AI-generated content presented publicly must include: *"This content was AI-assisted and has been reviewed for accuracy."*
- **Tone compliance**: Content must not be inflammatory, discriminatory, or politically extreme.
- **No competitor disparagement**: Do not generate content that unfairly attacks or misrepresents competitors.

---

## 4. Analytics Boundary

| Permitted | Prohibited |
|-----------|-----------|
| Aggregate usage metrics (no PII) | Individual user tracking without consent |
| Public GitHub API data (repos, stars, topics) | Private repo contents without authorization |
| Org-level telemetry | Cross-org data aggregation without consent |
| Performance and error rates | User behavioural profiling |

---

## 5. Data Consent Rules

Before processing any external data source:
1. Verify the source's terms of service permit programmatic access.
2. Apply rate limits and `robots.txt` compliance for web scraping.
3. Do not scrape or ingest data from sources that explicitly prohibit it.
4. User-provided data must be processed under the minimum necessary principle.
5. Data older than 90 days must be reviewed for continued relevance before reuse.

---

## 6. Responsible Play Warnings

The Infinity system is designed for autonomous operation. The following warnings
are mandatory context for all operators:

> ⚠️ **Autonomous agents may act on incomplete information.**  
> Always review agent outputs before applying to production systems.

> ⚠️ **LLM outputs are probabilistic, not deterministic.**  
> Critical decisions must include a human review step (governance gate).

> ⚠️ **Discovery agents crawl public data.**  
> Ensure compliance with applicable laws (GDPR, CCPA, DMCA) before acting on scraped content.

> ⚠️ **Auto-merge is restricted to low/medium risk PRs.**  
> High-risk changes always require human approval. See `genesis-auto-merge.yml`.

---

## 7. Enforcement

- The `validator_agent.py` checks all PR bodies and commit messages for CAG violations.
- Violations of CAG-001 through CAG-007 will cause the governance gate to fail.
- Suspected violations must be reported immediately to the repository admin.
- AI outputs that may violate these rules must be flagged with label `content:review-required`.

---

## 8. Traceable Outputs

All AI-generated content committed to this repository must include in the commit message
or PR body:
- The LLM model used (e.g., `model: gpt-4o-mini`)
- The context/run ID (e.g., `run_id: 22251423678`)
- The governance status (e.g., `tap: approved`)

This ensures full audit traceability per TAP P-006.

---

*Infinity Orchestrator · Celebrity AI Guardrails v1.0.0 · Infinity-X-One-Systems*
