# Agent Workflow Diagram

## Step 1 Draft + Updated Flow

```mermaid
flowchart TD
    C[Customer Request\nquote_requests_sample.csv] --> O[Orchestrator Agent\nRoutes inquiry and explains decisions]

    O --> I[Inventory Agent]
    O --> Q[Quote Agent]
    O --> F[Fulfillment Agent]
    O --> R[Reporting Agent]

    I --> T1[get_all_inventory\nTool: list inventory]
    I --> T2[get_stock_level\nTool: stock by paper type]
    I --> T3[get_supplier_delivery_date\nTool: replenishment ETA]

    Q --> T4[search_quote_history\nTool: prior pricing context]
    Q --> T2

    F --> T5[create_transaction\nTool: write quote/sale rows]
    F --> T2
    F --> T3

    R --> T6[get_cash_balance\nTool: current liquidity]
    R --> T7[generate_financial_report\nTool: reporting summary]

    T1 --> DB[(SQLite DB)]
    T2 --> DB
    T3 --> EXT[Supplier lead-time model]
    T4 --> DB
    T5 --> DB
    T6 --> DB
    T7 --> DB

    F --> O
    Q --> O
    I --> O
    R --> O
    O --> U[Customer-facing response\nQuote, fulfillment status, rationale]
```

## Agent Responsibilities (Non-overlapping)

- **Orchestrator Agent**: accepts request, sequences worker agents, composes final customer-safe response.
- **Inventory Agent**: answers stock questions and reorder viability (with supplier ETA).
- **Quote Agent**: computes price and discount strategy, references quote history.
- **Fulfillment Agent**: confirms/denies orders, updates records via transaction tools.
- **Reporting Agent**: fetches cash/reporting metrics for explainability and monitoring.

## Tool Mapping to Starter Helper Functions

- `inventory_lookup_tool` -> `get_all_inventory`, `get_stock_level`
- `supplier_timeline_tool` -> `get_supplier_delivery_date`
- `quote_history_tool` -> `search_quote_history`
- `transaction_tool` -> `create_transaction`
- `cash_balance_tool` -> `get_cash_balance`
- `financial_report_tool` -> `generate_financial_report`

This mapping replaces hypothetical tools with concrete helper-function-backed tools from the starter module.
