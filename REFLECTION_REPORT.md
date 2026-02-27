# Reflection Report

## 1) Architecture and Decision Process

I implemented a five-agent design with one orchestrator and four worker agents to keep responsibilities clean and non-overlapping:

- **Orchestrator Agent** receives each request, sequences worker calls, and returns customer-safe output.
- **Inventory Agent** checks stock and reorder implications using inventory + supplier ETA tools.
- **Quote Agent** builds budget-aware quotes with loyalty and bulk discount logic.
- **Fulfillment Agent** finalizes outcomes and writes auditable transaction records.
- **Reporting Agent** computes cash and financial summary for transparency and operator monitoring.

The architecture was selected to satisfy project constraints (max five agents), preserve modularity, and make each decision stage traceable. The workflow in [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) maps every tool to specific helper functions in `project_starter.py`.

Repository note: the original provided `project_starter.py` artifact referenced by the assignment was not present in this repository snapshot. To keep alignment with the rubric, I recreated the starter helper interface in [project_starter.py](project_starter.py) with the required function signatures and used those helper functions directly in tool definitions.

## 2) Evaluation Summary

Evaluation was run across all 8 requests in `quote_requests_sample.csv`, producing `test_results.csv`.

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
