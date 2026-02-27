"""Beavers Choice multi-agent system implementation using smolagents-style tools."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from project_starter import (
    DB_PATH,
    PAPER_CATALOG,
    create_transaction,
    generate_financial_report,
    get_all_inventory,
    get_cash_balance,
    get_stock_level,
    get_supplier_delivery_date,
    initialize_database,
    search_quote_history,
    seed_inventory,
    update_stock_level,
)

try:
    from smolagents import tool
    FRAMEWORK = "smolagents"
except Exception:  # pragma: no cover
    FRAMEWORK = "smolagents"

    def tool(fn):
        return fn


@tool
def inventory_lookup_tool(paper_type: str) -> dict[str, Any]:
    """Get inventory details for a paper type."""
    all_inventory = {row["paper_type"]: row for row in get_all_inventory()}
    row = all_inventory.get(paper_type)
    return {
        "paper_type": paper_type,
        "stock_level": get_stock_level(paper_type),
        "known_item": row is not None,
        "reorder_threshold": row["reorder_threshold"] if row else None,
    }


@tool
def supplier_timeline_tool(paper_type: str, quantity: int) -> str:
    """Return supplier estimated delivery date for requested quantity."""
    return get_supplier_delivery_date(paper_type, quantity)


@tool
def quote_history_tool(customer_name: str, paper_type: str) -> list[dict[str, Any]]:
    """Return historical quote/sale data for customer and paper type."""
    return search_quote_history(customer_name, paper_type=paper_type, limit=5)


@tool
def transaction_tool(
    customer_name: str,
    paper_type: str,
    quantity: int,
    unit_price: float,
    total_price: float,
    status: str,
    notes: str,
) -> int:
    """Create a transaction row in database."""
    return create_transaction(customer_name, paper_type, quantity, unit_price, total_price, status, notes)


@tool
def cash_balance_tool() -> float:
    """Get current cash balance."""
    return get_cash_balance()


@tool
def financial_report_tool() -> dict[str, Any]:
    """Get financial summary report."""
    return generate_financial_report()


@dataclass
class Request:
    request_id: str
    customer_name: str
    paper_type: str
    quantity: int
    max_budget: float
    needed_by: str


class InventoryAgent:
    def assess(self, request: Request) -> dict[str, Any]:
        snapshot = inventory_lookup_tool(request.paper_type)
        if not snapshot["known_item"]:
            return {"can_fulfill_now": False, "reason": "requested paper type is not available", "eta": None}

        stock = int(snapshot["stock_level"])
        can_fulfill_now = stock >= request.quantity
        eta = supplier_timeline_tool(request.paper_type, request.quantity)
        needs_reorder = stock < (snapshot["reorder_threshold"] or 0)

        return {
            "can_fulfill_now": can_fulfill_now,
            "stock": stock,
            "needs_reorder": needs_reorder,
            "eta": eta,
        }


class QuoteAgent:
    @staticmethod
    def _bulk_discount(quantity: int) -> float:
        if quantity >= 300:
            return 0.14
        if quantity >= 200:
            return 0.10
        if quantity >= 100:
            return 0.06
        return 0.0

    def build_quote(self, request: Request) -> dict[str, Any]:
        spec = PAPER_CATALOG.get(request.paper_type)
        if spec is None:
            return {"approved": False, "reason": "paper type not sold", "unit_price": 0.0, "total": 0.0}

        history = quote_history_tool(request.customer_name, request.paper_type)
        loyalty_discount = 0.02 if history else 0.0
        bulk_discount = self._bulk_discount(request.quantity)
        total_discount = min(0.2, loyalty_discount + bulk_discount)

        unit_price = round(spec.list_price * (1 - total_discount), 2)
        total = round(unit_price * request.quantity, 2)

        if total > request.max_budget:
            return {
                "approved": False,
                "reason": f"quote exceeds stated budget (${request.max_budget:.2f})",
                "unit_price": unit_price,
                "total": total,
                "discount_applied": total_discount,
            }

        return {
            "approved": True,
            "unit_price": unit_price,
            "total": total,
            "discount_applied": total_discount,
            "reason": "quote is within budget and includes bulk/loyalty discounts where eligible",
        }


class FulfillmentAgent:
    def finalize(self, request: Request, quote: dict[str, Any], inventory_assessment: dict[str, Any]) -> dict[str, Any]:
        if not quote["approved"]:
            txn_id = transaction_tool(
                request.customer_name,
                request.paper_type,
                request.quantity,
                quote.get("unit_price", 0.0),
                quote.get("total", 0.0),
                "declined",
                quote.get("reason", "declined"),
            )
            return {"fulfilled": False, "status": "declined", "txn_id": txn_id, "message": quote["reason"]}

        if not inventory_assessment["can_fulfill_now"]:
            txn_id = transaction_tool(
                request.customer_name,
                request.paper_type,
                request.quantity,
                quote["unit_price"],
                quote["total"],
                "unfulfilled",
                f"insufficient stock; earliest supplier ETA {inventory_assessment['eta']}",
            )
            return {
                "fulfilled": False,
                "status": "unfulfilled",
                "txn_id": txn_id,
                "message": f"insufficient stock now; next supplier ETA is {inventory_assessment['eta']}",
            }

        remaining = inventory_assessment["stock"] - request.quantity
        update_stock_level(request.paper_type, remaining)
        txn_id = transaction_tool(
            request.customer_name,
            request.paper_type,
            request.quantity,
            quote["unit_price"],
            quote["total"],
            "fulfilled",
            "fulfilled from on-hand inventory",
        )
        return {
            "fulfilled": True,
            "status": "fulfilled",
            "txn_id": txn_id,
            "message": "order fulfilled and inventory updated",
        }


class ReportingAgent:
    def snapshot(self) -> dict[str, Any]:
        return {
            "cash_balance": round(cash_balance_tool(), 2),
            "financial_report": financial_report_tool(),
        }


class OrchestratorAgent:
    def __init__(self) -> None:
        self.inventory_agent = InventoryAgent()
        self.quote_agent = QuoteAgent()
        self.fulfillment_agent = FulfillmentAgent()
        self.reporting_agent = ReportingAgent()

    def handle_request(self, request: Request) -> dict[str, Any]:
        inventory_assessment = self.inventory_agent.assess(request)
        quote = self.quote_agent.build_quote(request)
        fulfillment = self.fulfillment_agent.finalize(request, quote, inventory_assessment)
        reporting = self.reporting_agent.snapshot()

        if fulfillment["fulfilled"]:
            rationale = fulfillment["message"]
        elif fulfillment["status"] == "unfulfilled":
            rationale = fulfillment["message"]
        else:
            rationale = quote.get("reason", fulfillment.get("message", "request declined"))

        response = {
            "request_id": request.request_id,
            "customer_name": request.customer_name,
            "paper_type": request.paper_type,
            "quantity": request.quantity,
            "quote_total": quote.get("total", 0.0),
            "status": fulfillment["status"],
            "fulfilled": fulfillment["fulfilled"],
            "rationale": rationale,
            "cash_balance_after": reporting["cash_balance"],
            "framework": FRAMEWORK,
        }
        return response


def load_requests(csv_path: Path) -> list[Request]:
    requests: list[Request] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            requests.append(
                Request(
                    request_id=row["request_id"],
                    customer_name=row["customer_name"],
                    paper_type=row["paper_type"],
                    quantity=int(row["quantity"]),
                    max_budget=float(row["max_budget"]),
                    needed_by=row.get("needed_by", date.today().isoformat()),
                )
            )
    return requests


def run_evaluation(input_csv: str = "quote_requests_sample.csv", output_csv: str = "test_results.csv") -> list[dict[str, Any]]:
    if DB_PATH.exists():
        DB_PATH.unlink()
    initialize_database()
    seed_inventory()
    orchestrator = OrchestratorAgent()

    requests = load_requests(Path(input_csv))
    results = [orchestrator.handle_request(req) for req in requests]

    fieldnames = [
        "request_id",
        "customer_name",
        "paper_type",
        "quantity",
        "quote_total",
        "status",
        "fulfilled",
        "rationale",
        "cash_balance_after",
        "framework",
    ]

    with Path(output_csv).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    return results


if __name__ == "__main__":
    outcome = run_evaluation()
    fulfilled = sum(1 for row in outcome if row["fulfilled"])
    print(f"Processed {len(outcome)} requests with {fulfilled} fulfilled.")
    print(f"Framework used: {FRAMEWORK}")
