# CodinzHub Sprint Guardian: Balance Load

## 1. Summary
Analyzed active sprint workload across 3 team members (6 active issues). Identified **1 overloaded engineer(s)** and **2 team member(s) with available capacity**. Generated **1 workload rebalancing proposal(s)**.

- **Execution Mode**: `dry-run`
- **Assignee Approval**: `not provided`

## 2. Workload Load Balance Analysis
### Current Team Workload & WIP Distribution

| Engineer | Active WIP | Max WIP Limit | Sprint Points | Capacity Limit | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Coder Coder** (`coder.coder@codinzhub.com`) | 3 tickets | 3 | 15 pts | 15 pts | 🔴 **OVERLOADED** |
| **Engineer One** (`engineer.one@example.com`) | 1 tickets | 2 | 3 pts | 8 pts | 🟢 Optimal |
| **Engineer Two** (`engineer.two@example.com`) | 1 tickets | 2 | 6 pts | 8 pts | 🟢 Optimal |

### Proposed Workload Reassignment Plan

| Issue Key | Summary | Current Overloaded Owner | Target Available Owner | Affinity Reason |
| :--- | :--- | :--- | :--- | :--- |
| `CodinzHub-102` | Build dynamic Work-In-Progress (WIP) load rebalancer | `Coder Coder` | `Engineer One` | +10 pts: +4 component ownership, +3 label match, +3 skill match |

## 3. Assignment Approval Items
**PENDING APPROVAL: CodinzHub-102**
- **Current Owner**: `coder.coder@codinzhub.com`
- **Proposed Owner**: `engineer.one@example.com`
- **Confidence**: `high`
- **Reason**: Workload rebalancing recommendation (+10 pts: +4 component ownership, +3 label match, +3 skill match)
- **Risk**: Pending human lead sign-off before mutating active sprint assignment
- **Authority Needed**: Configured Assigning Authority (e.g. Coder Coder)

## 4. Recommended Jira Actions
- Execute with `--apply --approved-by "<Assigning Authority>"` to apply the 1 workload rebalancing moves in Jira.

## 5. Missing Inputs or Risks
- ⚠️ Coder Coder is overloaded (WIP: 3/3, Points: 15/15).
