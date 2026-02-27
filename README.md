# Beavers_Choice_Udacity
Capstone - beavers choice

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

	Optional (if available in your package index):

	```bash
	pip install smolagents
	```

2. Run evaluation:

	```bash
	python multi_agent_system.py
	```

3. Run smoke tests:

	```bash
	pytest -q
	```

## CI

- GitHub Actions runs `pytest -q` on pushes and pull requests to `main` via [.github/workflows/tests.yml](.github/workflows/tests.yml).
