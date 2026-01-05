# CodinzHub Sprint Guardian - System Architecture & Engineering Specification

## Executive Summary

**CodinzHub Sprint Guardian** is an enterprise-grade, developer-centric Agile Sprint Orchestrator and Scrum Co-Pilot. By bridging Large Language Models (LLMs) with Atlassian Jira via the **Model Context Protocol (MCP)**, Sprint Guardian automates sprint scope shaping, queue triaging, workload rebalancing, and standup reporting—underpinned by a **Human-in-the-Loop (HITL)** approval gatekeeper and audit logging engine.

---

## High-Level System Architecture

```text
+-----------------------------------------------------------------------------------+
|                              AGENTS & INTERFACES                                 |
|  [Claude Code / Codex / Cursor / Antigravity]     [Bash / PowerShell Automation]   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        MODEL CONTEXT PROTOCOL (MCP) LAYER                         |
|  - MCP Tool Server (stdio JSON-RPC)                                               |
|  - Tools: shape_sprint, triage_queue, suggest_owner, balance_load, standup_brief  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     HUMAN-IN-THE-LOOP (HITL) GOVERNANCE GATE                      |
|  - Safety Guardrail Interceptor: dry-run vs apply verification                    |
|  - Authority Validator: verifies approved-by against team-map assigning_authorities|
|  - Cryptographic Audit Logger: writes immutable TSV and JSONL audit logs          |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           CORE ORCHESTRATION ENGINES                              |
|  +-------------------+  +-------------------+  +-------------------+              |
|  |   Shape Sprint    |  |   Triage Queue    |  |   Suggest Owner   |              |
|  +-------------------+  +-------------------+  +-------------------+              |
|  |   Balance Load    |  |  Inspect Sprint   |  |   Surface Risk    |              |
|  +-------------------+  +-------------------+  +-------------------+              |
|  |  Progress Pulse   |  |   Standup Brief   |  |    Retro Notes    |              |
|  +-------------------+  +-------------------+  +-------------------+              |
|                                                                                   |
|  ALGORITHMIC SCORING ENGINES:                                                     |
|  - Multi-Criteria Ownership Scorer (Components, Skills, WIP, Capacity, Allowlist)  |
|  - Sprint Readiness Scorer (Priority, Dependencies, Acceptance Criteria, Sizing)   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                JIRA DATA ADAPTERS                                 |
|  [MockJiraClient (In-Memory)]    [McpJiraClient (MCP)]    [RestJiraClient (REST)] |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                          EXTERNAL ATLASSIAN JIRA PLATFORM                         |
|  - Active Sprints, Boards, Backlog Queues, JQL AST Query Execution, Custom Fields |
+-----------------------------------------------------------------------------------+
```

---

## Algorithmic Decision Frameworks

### 1. Multi-Criteria Ownership Scoring Algorithm

Candidate selection is formulated as a weighted multi-attribute utility function:

$$\text{Score}(c, i) = \sum_{k} w_k \cdot \mathbf{1}_{\{P_k(c, i)\}} - \sum_{m} \lambda_m \cdot \mathbf{1}_{\{N_m(c, i)\}}$$

Where:
- $P_1$ (Component Ownership): $+4$
- $P_2$ (Label / Feature Area): $+3$
- $P_3$ (Skill Match Vector): $+3$
- $P_4$ (Recent PR / Commit Activity): $+2$
- $P_5$ (Backup Owner Designation): $+1$
- $N_1$ (Not in Allowlist): $-5$ (Hard Blocker)
- $N_2$ (Unavailable in Sprint Window): $-4$ (Hard Blocker)
- $N_3$ (At or Above WIP Limit): $-4$ (Hard Blocker)
- $N_4$ (Exceeds Sprint Capacity Points): $-3$
- $N_5$ (Outside Team Map Routing): $-3$
- $N_6$ (Blocked Issue): $-2$
- $N_7$ (Missing Acceptance Criteria): $-2$

#### Confidence Tiering:
- **HIGH**: Score $\ge 6$, no hard blockers, within sprint capacity.
- **MEDIUM**: Score between $3$ and $5$, or one soft risk.
- **LOW**: Score $< 3$, or any active hard blocker.

---

### 2. Workload Balancing (Pareto WIP Optimization)

Let $W_c$ denote the current active WIP of candidate $c$, and $M_c$ denote their defined WIP limit (`max_in_progress`).
An engineer is flagged as **Overloaded** if:
$$W_c > M_c \quad \text{or} \quad \sum_{i \in \text{Issues}(c)} \text{Points}(i) > \text{Capacity}(c)$$

The balancer finds non-blocked tickets assigned to overloaded engineers and solves a bipartite matching transfer to underutilized engineers:
$$\max \sum_{(i, c')} \text{AffinityScore}(c', i)$$
Subject to:
$$W_{c'} + 1 \le M_{c'}$$
$$\text{Points}_{c'} + \text{Points}(i) \le \text{Capacity}(c')$$

---

## Security & Governance Guardrails

1. **Deterministic Dry-Run Default**: Every execution starts in non-mutative read mode.
2. **Authority Signature Verification**: Any mutation touching Jira assignees requires `--apply --approved-by "<name_or_email>"` where the identity must strictly match `approval.assigning_authorities` in `team-map.yaml`.
3. **Immutable Audit Trail**: Every approved mutation produces an immediate write to `automation/output/approvals.log` (TSV) and `automation/output/audit.jsonl` (JSON Lines).
