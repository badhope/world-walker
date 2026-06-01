.PHONY: install test run-backend run-frontend run-demo build lint clean

install:
	pip install -r requirements.txt
	cd frontend && npm install

test:
	python -m pytest tests/ -v --tb=short

run-backend:
	uvicorn backend.api.main:app --reload --port 8001 --host 0.0.0.0

run-frontend:
	cd frontend && npm run dev

run-demo:
	python demo_complete.py

build:
	cd frontend && npx vite build

lint:
	ruff check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete