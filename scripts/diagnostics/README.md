# Diagnostic & Browser-test Scripts / 诊断与浏览器测试脚本

> Scripts that were previously mis-located in `screenshots/`. They
> are not part of the canonical CI pipeline and are kept here for
> ad-hoc debugging only.

| Script | Purpose |
|--------|---------|
| `browser_test.py` | End-to-end browser automation test (Playwright) |
| `diagnose_browser.py` | Captures all network requests to find 404s |
| `find_404.py` | Locates the last 404 in a running session |
| `find_404_v2.py` | Detailed diagnostics: all 4xx/5xx + console messages |

## Usage

These scripts require a **running frontend on port 8080** and a
**running API on port 8000**:

```bash
# 1. start the stack
docker compose up -d

# 2. run a diagnostic
python scripts/diagnostics/find_404_v2.py
```

## When to use them

- A PR adds a new API endpoint and the frontend shows 404s
- Lighthouse / manual QA finds broken links
- You need to capture browser screenshots for issue reports

## When NOT to use them

- For regular test runs. Use `pytest tests/` instead.
- For CI. None of these are wired into the workflow (intentionally,
  they require a live browser + frontend).
