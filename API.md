# Regional Economic Analysis — REST API Reference / API 参考

> Complete reference for the **70+ REST endpoints** exposed by the FastAPI backend.
>
> Base URL: `http://localhost:8000/api/v1` (development) · OpenAPI: `http://localhost:8000/docs`

---

## Table of Contents / 目录

1. [Quick start](#quick-start)
2. [Authentication](#authentication)
3. [Endpoints by category](#endpoints-by-category)
   - [City data](#city-data)
   - [Enterprise analysis](#enterprise-analysis)
   - [Government analysis](#government-analysis)
   - [Retail site selection](#retail-site-selection)
   - [Sales forecast](#sales-forecast)
   - [Time series](#time-series)
   - [Data collection](#data-collection)
   - [Inference / prediction](#inference--prediction)
   - [Interactive](#interactive)
   - [Reports / export](#reports--export)
   - [WebSocket](#websocket)
   - [System / static](#system--static)
4. [Common request / response schemas](#common-request--response-schemas)
5. [Error handling](#error-handling)
6. [Versioning](#versioning)

---

## Quick start

```bash
# Health check
curl http://localhost:8000/health

# Get all cities
curl http://localhost:8000/api/v1/cities/list

# Run enterprise analysis
curl -X POST http://localhost:8000/api/v1/analysis/enterprise \
  -H 'Content-Type: application/json' \
  -d '{"city_name":"深圳"}'

# Compare cities
curl -X POST http://localhost:8000/api/v1/cities/compare \
  -H 'Content-Type: application/json' \
  -d '{"cities":["深圳","上海","北京"]}'
```

Interactive Swagger UI: **<http://localhost:8000/docs>**

---

## Authentication

Most endpoints are currently **publicly accessible**. Sensitive endpoints
require a JWT bearer token obtained from the `/api/v1/auth/login` endpoint.

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "change-me"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Use the token in subsequent requests:

```http
GET /api/v1/protected-endpoint
Authorization: Bearer <access_token>
```

---

## Endpoints by category

> Total: **70+ endpoints** across **11 functional groups**
> Auto-generated reference (live): <http://localhost:8000/openapi.json>

### City data / 城市数据

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/cities/list` | List all supported cities |
| GET | `/api/v1/cities/{city_name}` | Detailed metrics for a single city |
| GET | `/api/v1/cities/{city_name}/historical` | Multi-year time-series |
| GET | `/api/v1/cities/regions` | All cities grouped by region |
| GET | `/api/v1/cities/quality/report` | Data quality & completeness report |
| POST | `/api/v1/cities/compare` | Side-by-side comparison of multiple cities |
| POST | `/api/v1/cities/time-series` | Standardised time-series groups |

#### Examples

**List cities**:
```bash
curl http://localhost:8000/api/v1/cities/list
# → {"cities":["深圳","上海","北京",...], "total": 10}
```

**Compare 3 cities**:
```bash
curl -X POST http://localhost:8000/api/v1/cities/compare \
  -H 'Content-Type: application/json' \
  -d '{"cities":["深圳","上海","北京"]}'
```

### Enterprise analysis / 企业分析

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analysis/enterprise` | Site-selection analysis (cost / supply chain / talent) |
| GET | `/api/v1/analysis/enterprise/v3/{city_name}` | V3 analysis with detailed scoring |
| GET | `/api/v1/analysis/enterprise/list` | All enterprise analysis records |
| GET | `/api/v1/analysis/enterprise/{id}` | Get specific analysis record |
| GET | `/api/v1/analysis/enterprise/{id}/export` | Export analysis as JSON / CSV |

**Example request body** (`POST /api/v1/analysis/enterprise`):
```json
{
  "city_name": "深圳",
  "industry": "半导体",
  "company_size": "中大型",
  "weight_business_cost": 0.30,
  "weight_supply_chain": 0.25,
  "weight_policy_benefit": 0.15,
  "weight_talent_pool": 0.15,
  "weight_innovation": 0.10,
  "weight_infrastructure": 0.05
}
```

**Example response** (200 OK):
```json
{
  "city": "深圳",
  "industry": "半导体",
  "overall_score": 78.5,
  "business_costs": {
    "land_price_score": 65.0,
    "salary_score": 50.0,
    "energy_score": 80.0,
    "financing_score": 85.0,
    "tax_score": 70.0,
    "total_cost_score": 70.0
  },
  "supply_chain": {
    "supply_chain_score": 92.0,
    "local_support_rate": 78.0,
    "delivery_time": 2.5,
    "location_quotient": 1.85
  },
  "policy_benefits": {
    "policy_benefit_score": 88.0,
    "tax_reduction": 18.0,
    "tax_coverage": 65.0,
    "rd_subsidy": 220.0
  },
  "talent_pool": 92.0,
  "innovation_index": 95.5,
  "recommendations": [
    "深圳在供应链配套与创新生态方面具有显著优势",
    "土地与人工成本相对较高，建议聚焦高附加值环节",
    "..."
  ]
}
```

### Government analysis / 产业政策分析

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analysis/government` | Industry policy evaluation |
| GET | `/api/v1/analysis/government/{city}` | Government analysis for a city |
| GET | `/api/v1/analysis/government/list` | All government analysis records |
| GET | `/api/v1/analysis/government/{id}/export` | Export as JSON / PDF |

### Retail site selection / 零售选址

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/retail/analyze` | Run site-selection analysis |
| POST | `/api/v1/retail/score` | Score a candidate location |
| GET | `/api/v1/retail/list` | List all retail analyses |
| GET | `/api/v1/retail/{id}` | Get a specific analysis |

### Sales forecast / 销售预测

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/forecast/sales` | Forecast sales from historical data |
| GET | `/api/v1/forecast/sales/{id}` | Get forecast by ID |
| GET | `/api/v1/forecast/sales/{id}/export` | Export forecast as CSV / PNG |

### Time series / 时间序列

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/forecast/time-series` | Multi-year forecast for one or more metrics |
| GET | `/api/v1/forecast/time-series/{id}` | Retrieve forecast by ID |

**Request body**:
```json
{
  "city": "深圳",
  "metric": "gdp",
  "years": 10,
  "model": "linear"  // or "exponential", "arima", "prophet"
}
```

### Data collection / 数据采集

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/data/collect` | Trigger data collection from a source |
| GET | `/api/v1/data/sources` | List configured data sources |
| GET | `/api/v1/data/source/{id}` | Source details |
| POST | `/api/v1/data/source/{id}/sync` | Force sync from source |
| GET | `/api/v1/data/quality` | Data quality report |
| POST | `/api/v1/data/validate` | Validate a dataset |

### Inference / prediction / 推理与预测

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/inference/predict` | Run a model inference |
| GET | `/api/v1/inference/models` | List available models |
| GET | `/api/v1/inference/model/{id}` | Model metadata |

### Interactive / 交互式分析

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/interactive/analysis` | Run an interactive analysis session |
| GET | `/api/v1/interactive/sessions` | List active sessions |
| DELETE | `/api/v1/interactive/session/{id}` | End a session |
| POST | `/api/v1/interactive/session/{id}/query` | Send a query within a session |

### Reports / export / 报告导出

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/reports/list` | List generated reports |
| POST | `/api/v1/reports/generate` | Generate a new report |
| GET | `/api/v1/reports/{id}/download` | Download a generated report |
| POST | `/api/v1/exports/csv` | Export data as CSV |
| POST | `/api/v1/exports/json` | Export data as JSON |
| POST | `/api/v1/exports/pdf` | Export analysis as PDF |

### WebSocket / 实时通信

| Method | Path | Description |
|--------|------|-------------|
| WS | `/api/v1/ws/analysis` | Real-time analysis progress channel |
| WS | `/api/v1/ws/notifications` | Real-time notifications |

**Example (JavaScript)**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/analysis');
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'start',
    endpoint: 'enterprise',
    city_name: '深圳'
  }));
};
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(`Progress: ${msg.progress}% - ${msg.stage}`);
};
```

### System / static / 系统

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (no auth) |
| GET | `/` | API root (returns metadata) |
| GET | `/openapi.json` | OpenAPI 3.x spec (JSON) |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |
| GET | `/favicon.ico` | Favicon |
| GET | `/dashboard` | Interactive analysis dashboard |
| GET | `/dashboard/retail` | Retail dashboard |
| GET | `/dashboard/government` | Government dashboard |
| GET | `/dashboard/forecast` | Forecast dashboard |
| GET | `/static/{path}` | Static assets |

---

## Common request / response schemas

### CityComparisonRequest
```typescript
{
  cities: string[];      // ["深圳", "上海", "北京"]
  metrics?: string[];    // optional, defaults to all
}
```

### CityTimeSeriesRequest
```typescript
{
  city: string;
  years: number;          // 1-20
  metrics?: string[];
  model?: "linear" | "exponential" | "arima" | "prophet";
}
```

### Standard error response
```typescript
{
  detail: string;          // human-readable error
  code?: string;           // error code (when available)
  timestamp?: string;      // ISO 8601
}
```

---

## Error handling

All errors follow RFC 7807 (Problem Details for HTTP APIs):

| Status | Meaning |
|--------|---------|
| 200 / 201 | Success |
| 400 | Bad request — invalid input |
| 401 | Unauthorized — missing or invalid token |
| 403 | Forbidden — insufficient permissions |
| 404 | Not found — resource does not exist |
| 422 | Unprocessable entity — validation failure |
| 429 | Too many requests — rate limit |
| 500 | Internal server error |
| 503 | Service unavailable — backend down |

**Example**:
```bash
$ curl -X POST http://localhost:8000/api/v1/analysis/enterprise \
    -H 'Content-Type: application/json' -d '{"city_name":"火星"}'
# → 404 {"detail":"城市 火星 数据未找到"}
```

---

## Versioning

The API is versioned via the URL prefix `/api/v1`. Within a major version,
backward compatibility is preserved. Breaking changes require a new major
version (`/api/v2`).

See [CHANGELOG.md](CHANGELOG.md) for historical changes.

---

## Rate limits

| Endpoint group | Limit |
|----------------|-------|
| Public reads | 100 req / min / IP |
| Authenticated | 1000 req / min / user |
| Forecasts / heavy compute | 10 req / min / user |
| WebSocket | 1 concurrent connection / user |

---

## Code generation

You can generate client SDKs from the OpenAPI spec:

```bash
# Python
openapi-generator-cli generate -i http://localhost:8000/openapi.json \
  -g python -o ./sdk/python --additional-properties=packageName=rea_client

# TypeScript
openapi-generator-cli generate -i http://localhost:8000/openapi.json \
  -g typescript-axios -o ./sdk/typescript

# Java
openapi-generator-cli generate -i http://localhost:8000/openapi.json \
  -g java -o ./sdk/java --library=webclient
```

---

**Last updated**: 2026-06-02
**API version**: v1 (4.0.0)
**Total endpoints**: 70+
