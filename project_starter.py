"""Starter utilities for Beavers Choice multi-agent inventory and sales simulation."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).with_name("beavers_choice.db")


@dataclass(frozen=True)
class PaperSpec:
    paper_type: str
    unit_cost: float
    list_price: float
    reorder_threshold: int
    supplier_lead_days: int


PAPER_CATALOG: dict[str, PaperSpec] = {
    "matte_a4": PaperSpec("matte_a4", unit_cost=1.40, list_price=2.40, reorder_threshold=120, supplier_lead_days=5),
    "glossy_a4": PaperSpec("glossy_a4", unit_cost=1.85, list_price=3.10, reorder_threshold=100, supplier_lead_days=7),
    "cardstock_a3": PaperSpec("cardstock_a3", unit_cost=2.75, list_price=4.35, reorder_threshold=80, supplier_lead_days=9),
    "recycled_a4": PaperSpec("recycled_a4", unit_cost=1.55, list_price=2.65, reorder_threshold=110, supplier_lead_days=6),
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """Create database tables if they do not already exist."""
    with closing(_connect()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                paper_type TEXT PRIMARY KEY,
                stock_level INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                list_price REAL NOT NULL,
                reorder_threshold INTEGER NOT NULL,
                supplier_lead_days INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                paper_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                status TEXT NOT NULL,
                notes TEXT
            );
            """
        )
        conn.commit()


def seed_inventory() -> None:
    """Populate inventory defaults on first run, preserving existing stock levels."""
    initialize_database()
    with closing(_connect()) as conn:
        for spec in PAPER_CATALOG.values():
            conn.execute(
                """
                INSERT OR IGNORE INTO inventory(
                    paper_type, stock_level, unit_cost, list_price, reorder_threshold, supplier_lead_days
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (spec.paper_type, spec.reorder_threshold + 80, spec.unit_cost, spec.list_price, spec.reorder_threshold, spec.supplier_lead_days),
            )
        conn.commit()


def get_all_inventory() -> list[dict[str, Any]]:
    """Return all inventory rows."""
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT * FROM inventory ORDER BY paper_type").fetchall()
    return [dict(row) for row in rows]


def get_stock_level(paper_type: str) -> int:
    """Return stock level for a paper type; 0 if not found."""
    with closing(_connect()) as conn:
        row = conn.execute("SELECT stock_level FROM inventory WHERE paper_type = ?", (paper_type,)).fetchone()
    return int(row["stock_level"]) if row else 0


def update_stock_level(paper_type: str, new_level: int) -> None:
    """Update stock level for a paper type."""
    with closing(_connect()) as conn:
        conn.execute("UPDATE inventory SET stock_level = ? WHERE paper_type = ?", (new_level, paper_type))
        conn.commit()


def create_transaction(
    customer_name: str,
    paper_type: str,
    quantity: int,
    unit_price: float,
    total_price: float,
    status: str,
    notes: str = "",
) -> int:
    """Insert a transaction row and return transaction id."""
    with closing(_connect()) as conn:
        cur = conn.execute(
            """
            INSERT INTO transactions(
                created_at, customer_name, paper_type, quantity, unit_price, total_price, status, notes
            ) VALUES (DATE('now'), ?, ?, ?, ?, ?, ?, ?)
            """,
            (customer_name, paper_type, quantity, unit_price, total_price, status, notes),
        )
        conn.commit()
        return int(cur.lastrowid)


def search_quote_history(customer_name: str, paper_type: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    """Find recent quote/fulfilled transactions for a customer, optionally filtered by paper type."""
    query = (
        "SELECT created_at, customer_name, paper_type, quantity, unit_price, total_price, status, notes "
        "FROM transactions WHERE customer_name = ?"
    )
    args: list[Any] = [customer_name]
    if paper_type:
        query += " AND paper_type = ?"
        args.append(paper_type)
    query += " ORDER BY id DESC LIMIT ?"
    args.append(limit)

    with closing(_connect()) as conn:
        rows = conn.execute(query, tuple(args)).fetchall()
    return [dict(row) for row in rows]


def get_supplier_delivery_date(paper_type: str, quantity: int) -> str:
    """Estimate supplier delivery date based on configured lead time and requested quantity."""
    spec = PAPER_CATALOG.get(paper_type)
    if not spec:
        return (date.today() + timedelta(days=14)).isoformat()

    load_penalty = max(0, quantity - spec.reorder_threshold) // 100
    eta = date.today() + timedelta(days=spec.supplier_lead_days + load_penalty)
    return eta.isoformat()


def get_cash_balance() -> float:
    """Compute current cash as cumulative fulfilled sales minus inventory carrying cost baseline."""
    with closing(_connect()) as conn:
        sales = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) AS total FROM transactions WHERE status = 'fulfilled'"
        ).fetchone()["total"]
        carrying_cost = conn.execute(
            "SELECT COALESCE(SUM(stock_level * unit_cost), 0) AS total FROM inventory"
        ).fetchone()["total"]
    return float(sales) - float(carrying_cost)


def generate_financial_report() -> dict[str, Any]:
    """Return a compact financial summary for reporting."""
    with closing(_connect()) as conn:
        fulfilled_count = conn.execute(
            "SELECT COUNT(*) AS c FROM transactions WHERE status = 'fulfilled'"
        ).fetchone()["c"]
        unfulfilled_count = conn.execute(
            "SELECT COUNT(*) AS c FROM transactions WHERE status != 'fulfilled'"
        ).fetchone()["c"]
        total_revenue = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) AS total FROM transactions WHERE status = 'fulfilled'"
        ).fetchone()["total"]

    return {
        "cash_balance": round(get_cash_balance(), 2),
        "fulfilled_transactions": int(fulfilled_count),
        "non_fulfilled_transactions": int(unfulfilled_count),
        "total_revenue": round(float(total_revenue), 2),
        "report_generated_on": date.today().isoformat(),
    }


if __name__ == "__main__":
    initialize_database()
    seed_inventory()
    print("Inventory initialized.")
    print(get_all_inventory())
