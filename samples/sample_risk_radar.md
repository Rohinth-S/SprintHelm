# CodinzHub Sprint Guardian: Surface Risk

## 1. Summary
Delivery Risk Radar detected **2 critical delivery threat(s)** and **3 moderate risk(s)** across active project scope. Primary impediments: blocker dependencies, unstaffed critical path tickets, and stale items.

- **Execution Mode**: `dry-run`
- **Assignee Approval**: `not provided`

## 2. Delivery Risks
### Delivery Risk Radar & Impact Matrix

| Risk Tier | Issue Key | Impact Description | Probable Cause | Owner / Action Owner | Recommended Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 🔴 **CRITICAL** | `CodinzHub-104` | Blocks sprint goal delivery | Upstream blocker (`CodinzHub-101`) | `engineer.two@example.com` | Swarm technical dependency immediately |
| 🔴 **CRITICAL** | `CodinzHub-108` | High-priority work unstaffed | Backlog queue lag / no owner assigned | `Team Lead` | Run `codinzhub-suggest-owner` and assign |
| 🟡 **MODERATE** | `CodinzHub-106` | Review queue bottleneck | Testing/Review capacity constraints | `engineer.two@example.com` | Allocate dedicated peer reviewer today |
| 🟡 **MODERATE** | `CodinzHub-110` | Potential sprint rollover | Security review backlog | `Unassigned` | Route to security engineer allowlist |

## 3. Assignment Approval Items
No pending ownership approvals required for this run.

## 4. Recommended Jira Actions
- Convene emergency triage for all critical delivery threats before end-of-day.
- Reallocate code review capacity to clear testing bottlenecks.

## 5. Missing Inputs or Risks
- ⚠️ CRITICAL: CodinzHub-104 is blocking downstream deliverables.
- ⚠️ CRITICAL: CodinzHub-108 has priority High but no assignee.
