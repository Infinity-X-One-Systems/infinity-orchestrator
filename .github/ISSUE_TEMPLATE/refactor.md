---
name: 🔧 Refactor
about: Propose a refactor, technical debt reduction, or code quality improvement
title: '[REFACTOR] '
labels: ['refactor', 'tech-debt', 'needs-triage']
assignees: []

---

## What Needs Refactoring?
<!-- File(s), module(s), or system area to be refactored. Be specific. -->

## Why Refactor Now?
<!-- What pain point does the current code cause? Performance, maintainability, security? -->

## Scope
- [ ] Single file / function
- [ ] Module / package
- [ ] Cross-repository
- [ ] Architecture-level

## Risk Level
- [ ] 🟢 Low — no behaviour change expected
- [ ] 🟡 Medium — interface changes; callers need updating
- [ ] 🔴 High — breaking change; requires migration plan

## Proposed Approach
<!-- How should the refactor be done? Include design notes if available. -->

## Acceptance Criteria
<!-- How will we know this refactor is complete and correct? -->

- [ ] All existing tests pass
- [ ] New tests added for changed behaviour
- [ ] Documentation updated
- [ ] No regression in performance benchmarks

## Dependencies
<!-- Other issues or PRs that must land first -->

## Estimated Effort
- [ ] XS (< 2 h)
- [ ] S (2–8 h)
- [ ] M (1–3 d)
- [ ] L (1–2 w)
- [ ] XL (> 2 w — requires architecture review)

## Additional Context
<!-- Relevant logs, profiling data, architecture diagrams -->
