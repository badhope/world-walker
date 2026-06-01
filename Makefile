.PHONY: install test run run-demo lint clean

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short

run:
	uvicorn backend.api.main:app --port 8001 --host 0.0.0.0

run-demo:
	python demo_complete.py

lint:
	ruff check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete