# GitHub Project Control Plane — Infinity Invention Machine

> **Org:** Infinity-X-One-Systems  
> **Version:** 1.0.0  
> **Governance:** TAP Protocol (Policy > Authority > Truth)  
> **Related:** [architecture.md](./architecture.md)

---

## 1. Overview

A **single GitHub Projects v2 board** serves as the unified control plane for the Infinity Invention
Machine. It surfaces repositories, pull requests, ideas/inventions, pipeline state, and finished
"system-in-a-box" outputs in one place.

---

## 2. Board Specification

### 2.1 Project Metadata

| Field | Value |
|-------|-------|
| **Name** | Infinity Invention Machine |
| **Owner** | Infinity-X-One-Systems (org) |
| **Visibility** | Private (org members only) |
| **Template** | None — custom board |

---

### 2.2 Custom Fields

| Field Name | Type | Options / Notes |
|------------|------|----------------|
| `Stage` | Single-select | Idea · Spec · CodeGen · Validation · Packaging · Released · Parked |
| `Priority` | Single-select | 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low |
| `Vision Score` | Number | 0–100; novelty × feasibility × market signal |
| `System Repo` | Text | Link to finished system repo (e.g. `Infinity-X-One-Systems/my-system`) |
| `Pipeline Run` | Text | URL of the most recent automation workflow run |
| `Gate Status` | Single-select | ✅ Approved · ⏳ Awaiting Review · ❌ Blocked · — Not Applicable |
| `Estimated Effort` | Single-select | XS · S · M · L · XL |
| `TAP Decision` | Text | Link to TAP decision log entry (if any) |

---

### 2.3 Views

| View Name | Layout | Group By | Sort | Filter |
|-----------|--------|----------|------|--------|
| **Pipeline Board** | Board | `Stage` | `Priority` desc | — |
| **All Items** | Table | — | `Priority` desc, created desc | — |
| **Active Inventions** | Table | `Stage` | `Vision Score` desc | `Stage` ≠ Parked, ≠ Released |
| **Released Systems** | Table | — | updated desc | `Stage` = Released |
| **Awaiting Gate** | Table | — | `Priority` desc | `Gate Status` = Awaiting Review |
| **Repo Inventory** | Table | — | name asc | type = Repository |

---

### 2.4 Automation Rules

| Trigger | Action |
|---------|--------|
| Issue opened with label `idea` | Add to board, set `Stage = Idea` |
| Issue opened with label `spec` | Set `Stage = Spec` |
| PR opened | Add to board, set `Gate Status = Awaiting Review` |
| PR merged | Set `Gate Status = Approved` |
| Issue closed | Set `Stage = Released` or `Parked` based on closing label |
| Workflow `portfolio-audit` runs | Repository items refreshed (via GraphQL mutation) |

---

## 3. Creation — Step-by-Step

The following steps use the **GitHub CLI** (`gh`) and the **GitHub Projects v2 GraphQL API**.
Run these once from a machine authenticated with a token that has `project:write` scope.

### Step 1 — Create the project

```bash
gh project create \
  --owner "Infinity-X-One-Systems" \
  --title "Infinity Invention Machine" \
  --format json
```

Save the returned `number` (e.g. `1`) and `id` (node ID) — you will need both below.

```bash
PROJECT_NUMBER=<number from above>
PROJECT_ID=<id from above>
```

### Step 2 — Add custom fields

Use the GraphQL mutation `createProjectV2Field`. Example for the `Stage` field:

```bash
gh api graphql -f query='
mutation {
  createProjectV2Field(input: {
    projectId: "'"$PROJECT_ID"'"
    dataType: SINGLE_SELECT
    name: "Stage"
    singleSelectOptions: [
      { name: "Idea",       color: BLUE,   description: "Raw idea submitted" }
      { name: "Spec",       color: PURPLE, description: "Specification in progress" }
      { name: "CodeGen",    color: YELLOW, description: "Code generation underway" }
      { name: "Validation", color: ORANGE, description: "Automated validation running" }
      { name: "Packaging",  color: GREEN,  description: "Building system-in-a-box" }
      { name: "Released",   color: GREEN,  description: "Shipped to finished systems repo" }
      { name: "Parked",     color: GRAY,   description: "Deferred — revisit later" }
    ]
  }) {
    projectV2Field { ... on ProjectV2SingleSelectField { id name } }
  }
}'
```

Repeat for `Priority`, `Gate Status`, and `Estimated Effort` (all `SINGLE_SELECT`).  
Use `dataType: NUMBER` for `Vision Score`.  
Use `dataType: TEXT` for `System Repo`, `Pipeline Run`, and `TAP Decision`.

### Step 3 — Create views

```bash
# Pipeline Board view (group by Stage)
gh api graphql -f query='
mutation {
  createProjectV2View(input: {
    projectId: "'"$PROJECT_ID"'"
    name: "Pipeline Board"
    layout: BOARD_LAYOUT
  }) { projectV2View { id name } }
}'

# All Items view (table)
gh api graphql -f query='
mutation {
  createProjectV2View(input: {
    projectId: "'"$PROJECT_ID"'"
    name: "All Items"
    layout: TABLE_LAYOUT
  }) { projectV2View { id name } }
}'
```

### Step 4 — Enable automation rules (UI only)

GitHub Projects v2 automation rules (item-added, PR-merged, etc.) are currently **only configurable
via the browser UI**. Navigate to:

```
https://github.com/orgs/Infinity-X-One-Systems/projects/<PROJECT_NUMBER>/settings/workflows
```

Enable the following built-in workflows:
- **Item added to project** → set Status to "Idea"
- **Pull request merged** → set Gate Status to "Approved"
- **Item closed** → set Stage to "Released"

### Step 5 — Link the project to the orchestrator repo

```bash
gh project link $PROJECT_NUMBER \
  --owner "Infinity-X-One-Systems" \
  --repo "infinity-orchestrator"
```

---

## 4. Ongoing Maintenance

| Task | Frequency | Automation |
|------|-----------|-----------|
| Portfolio audit (repo inventory refresh) | Weekly + on-demand | `portfolio-audit.yml` workflow |
| Add new idea items | As ideas arrive | Idea issue template → auto-added |
| Update pipeline state | On each stage transition | Agent automation (Phase 1+) |
| Prune stale parked items | Quarterly | Manual review |

---

## 5. Required Permissions

| Token / Secret | Required Scope | Used For |
|---------------|---------------|---------|
| `INFINITY_APP_TOKEN` | `project:write`, `repo` | Creating / updating project items |
| `GITHUB_TOKEN` | `repo` (default) | Reading repo metadata for audit |

> **Note:** `project:write` scope requires a GitHub App or a Fine-Grained PAT. The default
> `GITHUB_TOKEN` does **not** have project write access. See P-005 in the TAP Protocol.

---

*Infinity Orchestrator · GitHub Project Control Plane v1.0.0 · Infinity-X-One-Systems*
