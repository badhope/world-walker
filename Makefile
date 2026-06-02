.PHONY: install test run run-demo lint clean

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short

run:
	uvicorn backend.api.main:app --port 8000 --host 0.0.0.0

run-frontend:
	cd frontend && python3 -m http.server 8080

run-all:
	@echo "Starting backend on :8000 and frontend on :8080..."
	@trap 'kill 0' SIGINT SIGTERM EXIT; \
	uvicorn backend.api.main:app --port 8000 --host 0.0.0.0 & \
	cd frontend && python3 -m http.server 8080 & \
	wait

diagnose:
	python full_diagnose.py

browser-test:
	python scripts/diagnostics/browser_test.py

docker-build:
	docker build -t regional-economic-analysis:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

run-demo:
	python main.py --mode example

lint:
	ruff check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete