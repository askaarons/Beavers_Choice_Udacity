from __future__ import annotations

from multi_agent_system import (
    FulfillmentAgent,
    InventoryAgent,
    OrchestratorAgent,
    QuoteAgent,
    ReportingAgent,
    Request,
)
from project_starter import initialize_database, seed_inventory


def _sample_request() -> Request:
    return Request(
        request_id="T-001",
        customer_name="Schema Test Co",
        paper_type="matte_a4",
        quantity=40,
        max_budget=200.0,
        needed_by="2026-03-10",
    )


def test_agent_output_schemas_and_boundaries() -> None:
    initialize_database()
    seed_inventory()

    request = _sample_request()

    inventory_agent = InventoryAgent()
    inventory_result = inventory_agent.assess(request)
    assert {"can_fulfill_now", "stock", "needs_reorder", "eta"}.issubset(inventory_result.keys())
    assert "unit_price" not in inventory_result
    assert "cash_balance" not in inventory_result

    quote_agent = QuoteAgent()
    quote_result = quote_agent.build_quote(request)
    assert {"approved", "unit_price", "total", "reason"}.issubset(quote_result.keys())
    assert "stock" not in quote_result
    assert "cash_balance" not in quote_result

    fulfillment_agent = FulfillmentAgent()
    fulfillment_result = fulfillment_agent.finalize(request, quote_result, inventory_result)
    assert {"fulfilled", "status", "txn_id", "message"}.issubset(fulfillment_result.keys())
    assert "unit_price" not in fulfillment_result
    assert "cash_balance" not in fulfillment_result

    reporting_agent = ReportingAgent()
    reporting_result = reporting_agent.snapshot()
    assert {"cash_balance", "financial_report"}.issubset(reporting_result.keys())
    assert "stock" not in reporting_result
    assert "unit_price" not in reporting_result

    orchestrator = OrchestratorAgent()
    orchestrator_result = orchestrator.handle_request(_sample_request())
    assert {
        "request_id",
        "customer_name",
        "paper_type",
        "quantity",
        "quote_total",
        "status",
        "fulfilled",
        "rationale",
        "framework",
    }.issubset(orchestrator_result.keys())
    assert "cash_balance_after" not in orchestrator_result
    assert "operator_cash_balance_after" not in orchestrator_result
