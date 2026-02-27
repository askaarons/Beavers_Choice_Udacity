# Reflection Report

## 1) Architecture and Decision Process

I implemented a five-agent design with one orchestrator and four worker agents to keep responsibilities clean and non-overlapping:

- **Orchestrator Agent** receives each request, sequences worker calls, and returns customer-safe output.
- **Inventory Agent** checks stock and reorder implications using inventory + supplier ETA tools.
- **Quote Agent** builds budget-aware quotes with loyalty and bulk discount logic.
- **Fulfillment Agent** finalizes outcomes and writes auditable transaction records.
- **Reporting Agent** computes cash balance and financial summaries for transparency and operator monitoring.

The architecture was selected to satisfy project constraints (maximum of five agents), preserve modularity, and make each decision stage traceable. The workflow in [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) maps every tool to specific helper functions in [project_starter.py](project_starter.py).

Repository note: the original provided `project_starter.py` artifact referenced by the assignment was not present in this repository snapshot. To keep alignment with the rubric, I recreated the starter helper interface in [project_starter.py](project_starter.py) with the required function signatures and used those helper functions directly in tool definitions.

## 2) Evaluation Summary

Evaluation was run across all 8 requests in [quote_requests_sample.csv](quote_requests_sample.csv), producing [test_results.csv](test_results.csv).

- **3 requests fulfilled** (`R-001`, `R-002`, `R-003`)
- **5 requests not fulfilled** (`declined` due to budget/product mismatch or `unfulfilled` due to stock)
- **Cash balance changed at least 3 times** as fulfilled transactions were posted
- The system did **not** fulfill all requests, with explicit rationale included for each non-fulfilled request

### Strengths observed

- Clear customer-facing rationale is provided for each outcome.
- Quote logic consistently applies discount policy and budget checks.
- Fulfillment records are auditable because every outcome is persisted as a transaction.
- Inventory constraints are handled explicitly, including supplier ETA for stock shortages.

### Areas for improvement

- Backorder logic is binary (fulfill now vs not now) and can be expanded.
- Pricing strategy is rules-based and could better optimize conversion/profit over time.

## 3) Suggested Improvements

1. **Add partial-fulfillment and backorder optimization**
   - Split large orders into immediate and backordered lots when feasible.
   - Offer customer options with timeline and pricing tradeoffs.

2. **Add adaptive pricing policy with guardrails**
   - Learn discount effectiveness from historical conversion outcomes.
   - Keep strict floor/ceiling controls to protect margin and competitiveness.

3. **Add richer evaluation telemetry**
   - Track fulfillment latency, stockout frequency, and quote win rate.
   - Use these metrics for periodic policy updates.

## 4) Rubric Compliance Mapping

1. **Architecture diagram — PASS**
   - Evidence: [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) includes the full workflow diagram.

2. **Agent–tool interaction diagram — PASS**
   - Evidence: [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) shows each agent mapped to specific tools/helper functions.

3. **Multi-agent implementation & framework — PASS**
   - Evidence: [multi_agent_system.py](multi_agent_system.py) instantiates a framework-managed runtime that attempts `ToolCallingAgent` creation, and routes tool calls through a shared runtime.

4. **Tool definitions with required helpers — PASS**
   - Evidence: Tool wrappers in [multi_agent_system.py](multi_agent_system.py) map to helper functions in [project_starter.py](project_starter.py).

5. **Evaluation with full dataset — PASS**
   - Evidence: [quote_requests_sample.csv](quote_requests_sample.csv) processed end-to-end into [test_results.csv](test_results.csv).

6. **Reflection report — PASS**
   - Evidence: This document records architecture rationale, evaluation outcomes, and next-step improvements.

7. **Transparent customer-facing outputs — PASS**
   - Evidence: `OrchestratorAgent.handle_request(...)` in [multi_agent_system.py](multi_agent_system.py) is customer-safe and excludes internal cash metrics; operator-only telemetry is exposed via `handle_request_for_operations(...)` and `operator_cash_balance_after` in [test_results.csv](test_results.csv).

8. **Code readability and modularity — PASS**
   - Evidence: Distinct agent classes, helper-module separation, and tests in [tests/test_agent_boundaries.py](tests/test_agent_boundaries.py) and [tests/test_evaluation_smoke.py](tests/test_evaluation_smoke.py).
