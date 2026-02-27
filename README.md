# Beavers_Choice_Udacity
Capstone - Beavers Choice

## Deliverables

- Workflow diagram: [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md)
- Starter helper module: [project_starter.py](project_starter.py)
- Multi-agent implementation: [multi_agent_system.py](multi_agent_system.py)
- Starter review notes: [STARTER_REVIEW.md](STARTER_REVIEW.md)
- Evaluation input: [quote_requests_sample.csv](quote_requests_sample.csv)
- Evaluation output: [test_results.csv](test_results.csv)
- Reflection report: [REFLECTION_REPORT.md](REFLECTION_REPORT.md)

## Run

1. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

	Optional (if available for your Python version in your package index):

	```bash
	pip install -r requirements-optional.txt
	```

2. Run evaluation:

	```bash
	python multi_agent_system.py
	```

3. Run smoke tests:

	```bash
	pytest -q
	```

## Output contracts

- `OrchestratorAgent.handle_request(...)` returns a customer-safe response and does **not** expose internal cash metrics.
- `OrchestratorAgent.handle_request_for_operations(...)` appends operator telemetry used for evaluation outputs.
- `test_results.csv` includes `operator_cash_balance_after` (operator-only), not a customer-facing cash field.

## CI

- GitHub Actions runs `pytest -q` on pushes and pull requests to `main` via [.github/workflows/tests.yml](.github/workflows/tests.yml).
