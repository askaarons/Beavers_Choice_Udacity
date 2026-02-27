from __future__ import annotations

import csv
from pathlib import Path

from multi_agent_system import run_evaluation


REQUIRED_COLUMNS = {
    "request_id",
    "customer_name",
    "paper_type",
    "quantity",
    "quote_total",
    "status",
    "fulfilled",
    "rationale",
    "operator_cash_balance_after",
    "framework",
}


def test_evaluation_contract(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = repo_root / "quote_requests_sample.csv"
    output_csv = tmp_path / "test_results.csv"

    results = run_evaluation(str(input_csv), str(output_csv))

    assert len(results) > 0
    assert output_csv.exists()

    fulfilled_count = sum(1 for row in results if bool(row["fulfilled"]))
    assert fulfilled_count >= 3

    non_fulfilled_count = sum(1 for row in results if not bool(row["fulfilled"]))
    assert non_fulfilled_count >= 1

    balances = [float(row["operator_cash_balance_after"]) for row in results]
    balance_changes = sum(1 for i in range(1, len(balances)) if balances[i] != balances[i - 1])
    assert balance_changes >= 2
    assert fulfilled_count >= 3

    with output_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert len(rows) == len(results)
    assert set(reader.fieldnames or []) == REQUIRED_COLUMNS
