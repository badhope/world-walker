# 部署指南 / Deployment Guide

本文档介绍如何在不同环境中部署 **Regional Economic Analysis Agent** (v9.1.0)。

This document describes how to deploy the **Regional Economic Analysis Agent** in different environments (currently v9.1.0).

---

## 目录 / Table of Contents

1. [系统要求](#系统要求--system-requirements)
2. [本地开发部署](#本地开发部署--local-development)
3. [Docker 部署](#docker-部署--docker-deployment)
4. [生产环境部署](#生产环境部署--production-deployment)
5. [Nginx 反向代理](#nginx-反向代理--nginx-reverse-proxy)
6. [环境变量](#环境变量--environment-variables)
7. [监控与日志](#监控与日志--monitoring--logging)
8. [性能调优](#性能调优--performance-tuning)
9. [备份与恢复](#备份与恢复--backup--recovery)
10. [故障排查](#故障排查--troubleshooting)
11. [Web Console 部署](#web-console-部署-v91)

---

## 系统要求 / System Requirements

### 最低配置 / Minimum

| 项目 | 要求 |
|------|------|
| CPU | 2 核 |
| 内存 | 4 GB RAM |
| 磁盘 | 20 GB |
| Python | 3.11+ |
| Docker | 24.0+ (可选) |
| OS | Linux / macOS / Windows |

### 推荐配置 / Recommended (Production)

| 项目 | 要求 |
|------|------|
| CPU | 4 核+ |
| 内存 | 8 GB+ RAM |
| 磁盘 | 50 GB+ SSD |
| Python | 3.11 / 3.12 |
| 反向代理 | Nginx 1.20+ |

### 依赖服务 / Optional Services

- **PostgreSQL** 14+ (生产数据库，可选 SQLite 替代)
- **Redis** 7+ (缓存层，可选)
- **Prometheus + Grafana** (监控)

---

## 本地开发部署 / Local Development

### 1. 克隆仓库

```bash
git clone <repository-url>
cd regional-economic-analysis
```

### 2. 创建虚拟环境

```bash
python3.11 -m venv venv
source venv/bin/activate            # Linux/macOS
# venv\Scripts\activate             # Windows
```

### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少修改 SECRET_KEY
```

### 5. 启动后端(前端 v9.1+ 已挂到后端 8000)

```bash
# 方式 1: 通过 Makefile
make run

# 方式 2: 直接启动
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

> **v9.1+ 重要变更**:Web Console (`/console/`) 和 Web Dashboard (`/`) 都已挂在后端 :8000,**不再需要单独启前端 server**。如果想保留 v6.0 之前的 split 模式(前端在 :8080),依然可用 — `cd frontend && python3 -m http.server 8080`,但 Console 只能在 :8000 访问。

### 6. 访问应用

- Web Dashboard: <http://localhost:8000/>
- **Web Console v9.1**: <http://localhost:8000/console/>
- Swagger API 文档: <http://localhost:8000/docs>
- (legacy,可选) 前端: <http://localhost:8080>
- (legacy,可选) 后端 API: <http://localhost:8000/api/v1>

---

## Docker 部署 / Docker Deployment

### 快速开始

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 服务组成

| 服务 | 端口 | 说明 |
|------|------|------|
| `api` | 8000 | FastAPI 后端(**含 Web Console v9.1 mount 在 `/console/`**) |
| `frontend` | 8080 | 静态前端 (Nginx) — 投资 dashboard(只读) |
| `db` | 5432 | PostgreSQL (可选) |
| `redis` | 6379 | Redis 缓存 (可选) |

### 单独构建镜像

```bash
# 后端 (FastAPI)
docker build -t rea-backend:latest .

# 前端是纯静态 HTML，直接由 docker-compose 里的 nginx:alpine 挂载 ./frontend 即可，
# 不需要单独的 Dockerfile.frontend——也避免引入多余的构建层。
```

> 💡 如果需要把前端打成独立镜像（例如推到私有 registry），可以这样：
> ```bash
> # 把 frontend/ 内容打成一个最小 nginx 镜像（多阶段构建，单层）
> echo 'FROM nginx:alpine
> COPY frontend/ /usr/share/nginx/html' > Dockerfile.frontend
> docker build -t rea-frontend:latest -f Dockerfile.frontend .
> ```

### 推送至镜像仓库

```bash
docker tag rea-backend:latest your-registry.example.com/rea-backend:v9.1.0
docker push your-registry.example.com/rea-backend:v9.1.0
```

### 投资级镜像(v6.1+)— statsforecast / arch / pmdarima 预装

[`Dockerfile`](Dockerfile) 默认基础 `python:3.11-slim` + `build-essential` +
`gfortran`,预装投资级 3 库(版本与 Python 3.11 + numpy 2.x 兼容):

| 库 | 版本 | 作用 |
|---|---|---|
| `statsforecast` | `>=1.5,<3.0` | 高速 AutoARIMA + 多季节 + 节假日 |
| `arch` | `>=7.0,<8.0` | GARCH(1,1) 条件波动率 + 持续性 + 半衰期 |
| `pmdarima` | `>=2.0,<3.0` | `auto_arima` 备选 |

**验证镜像装上**:
```bash
docker compose up --build
curl -s http://localhost:8000/health | jq '.engine_stack'
# 期望: {"statsforecast": true, "arch": true, "pmdarima": true, "prophet": false}
```

**镜像大小影响**: 加上 `statsforecast` + `arch` + `pmdarima` + 编译依赖,
镜像从 ~350MB 增至 ~750MB。生产环境建议加 `--no-cache-dir` 和 `pip cache purge`。

**Sandbox / 无 Docker**: `engine_stack.py` 运行时自动探测,
`auto_arima_native` 走 `statsforecast > pmdarima > statsmodels` 优先级,
`garch_volatility` 走 `arch > rolling-std`。所有 API 输出 `"backend"` 字段
标识当前引擎,前端可显示。

### 多镜像变体(可选)

如果想区分"轻量"和"投资级"两个镜像,可加 `engine-stack` build arg:

```dockerfile
# Dockerfile.investment
FROM python:3.11-slim
ARG ENGINE_STACK=full
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gfortran curl
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
```

```bash
# 轻量(只 statsmodels,无 GARCH)
docker build -t rea:light -f Dockerfile.investment --build-arg ENGINE_STACK=base .

# 投资级(statsforecast + arch + pmdarima)
docker build -t rea:investment -f Dockerfile.investment --build-arg ENGINE_STACK=full .
```

---

## 生产环境部署 / Production Deployment

### 方案 A：Systemd 部署（推荐用于单节点）

#### 1. 创建用户

```bash
sudo useradd -r -s /bin/false rea
sudo mkdir -p /opt/rea
sudo chown rea:rea /opt/rea
```

#### 2. 部署代码

```bash
sudo -u rea git clone <repo> /opt/rea/app
cd /opt/rea/app
sudo -u rea python3.11 -m venv venv
sudo -u rea venv/bin/pip install -r requirements.txt
```

#### 3. 创建 systemd 服务 `/etc/systemd/system/rea-api.service`

```ini
[Unit]
Description=Regional Economic Analysis API
After=network.target

[Service]
Type=exec
User=rea
Group=rea
WorkingDirectory=/opt/rea/app
Environment="PATH=/opt/rea/app/venv/bin"
EnvironmentFile=/opt/rea/app/.env
ExecStart=/opt/rea/app/venv/bin/uvicorn backend.api.main:app \
    --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rea-api

[Install]
WantedBy=multi-user.target
```

#### 4. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable rea-api
sudo systemctl start rea-api
sudo systemctl status rea-api
```

### 方案 B：Gunicorn + Uvicorn Workers

```bash
pip install gunicorn
gunicorn backend.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

### 方案 C：Kubernetes (K8s)

参考 `deploy/k8s/` 目录下的清单文件 (如需自行创建)：

- `deployment.yaml`
- `service.yaml`
- `ingress.yaml`
- `configmap.yaml`
- `secret.yaml`

---

## Nginx 反向代理 / Nginx Reverse Proxy

### 配置示例 `/etc/nginx/sites-available/rea`

```nginx
upstream rea_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name rea.example.com;
    client_max_body_size 50M;

    # Web Console v9.1 (basic auth 套在 /console/ 路径,因为没内置认证)
    location /console/ {
        auth_basic "RCA Console";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://rea_backend/console/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SSE 专用 — 长 timeout
    location /api/v1/admin/chat/stream {
        proxy_pass http://rea_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;  # 关键:SSE 必须禁用 buffer
        proxy_cache off;
        proxy_read_timeout 600s;
    }

    # 前端静态资源(Dashboard)
    location / {
        root /opt/rea/app/frontend;
        try_files $uri $uri/ /index.html;
        expires 1h;
    }

    # API 代理
    location /api/ {
        proxy_pass http://rea_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_read_timeout 300s;
    }

    # Swagger
    location /docs {
        proxy_pass http://rea_backend/docs;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://rea_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }

    # 健康检查
    location /health {
        proxy_pass http://rea_backend/health;
        access_log off;
    }
}
```

### 启用 HTTPS（Let's Encrypt）

```bash
sudo certbot --nginx -d rea.example.com
```

---

## 环境变量 / Environment Variables

完整列表见 [`.env.example`](./.env.example)。

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_ENV` | `development` | 运行环境 |
| `APP_DEBUG` | `false` | 调试模式 |
| `APP_HOST` | `0.0.0.0` | 监听地址 |
| `APP_PORT` | `8000` | 监听端口 |
| `SECRET_KEY` | (必填) | JWT 签名密钥 |
| `DATABASE_URL` | `sqlite:///./data/rea.db` | 数据库连接 |
| `CORS_ORIGINS` | `http://localhost:8080` | 跨域白名单 (逗号分隔) |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `CACHE_TTL` | `300` | 缓存秒数 |
| `WORKERS` | `4` | Worker 数量 |

---

## 监控与日志 / Monitoring & Logging

`/health` 端点现在包含 `engine_stack` 字段,可纳入监控告警。

```bash
# 健康检查
curl -s http://localhost:8000/health | jq

# 监控脚本(伪代码)
HEALTH=$(curl -fs http://localhost:8000/health)
if ! echo "$HEALTH" | jq -e '.engine_stack.statsforecast or .engine_stack.arch' >/dev/null; then
    alert "Investment-grade engine not fully loaded"
fi
```

### 日志位置

- 应用日志: `./logs/rea-api.log`
- 访问日志: Nginx `/var/log/nginx/access.log`
- 系统日志: `journalctl -u rea-api`

### 集成 Prometheus

`/metrics` 端点已暴露 Prometheus 指标（需安装 `prometheus-fastapi-instrumentator`）。

```python
# 在 main.py 中
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

### Grafana 仪表板

导入 `deploy/grafana/rea-dashboard.json` (自行创建)。

### 健康检查

```bash
curl http://localhost:8000/health
# 返回 {"status": "ok"}
```

---

## 性能调优 / Performance Tuning

### 1. Worker 数量

经验公式：`workers = (2 * CPU_CORES) + 1`

### 2. 数据库连接池

```python
# config/settings.py
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
```

### 3. 启用缓存

```bash
# .env
CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=600
```

### 4. 静态资源 CDN

将 `frontend/` 目录部署至 CDN (Cloudflare / 阿里云 OSS / AWS S3)。

### 5. 启用 Gzip

Nginx 配置：

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1024;
```

---

## 备份与恢复 / Backup & Recovery

### 数据库备份

```bash
# SQLite
cp data/rea.db backup/rea-$(date +%Y%m%d).db

# PostgreSQL
pg_dump -U rea rea_db | gzip > backup/rea-$(date +%Y%m%d).sql.gz
```

### 自动备份脚本

```bash
#!/bin/bash
# /opt/rea/scripts/backup.sh
BACKUP_DIR=/opt/rea/backups
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /opt/rea/app/data/rea.db $BACKUP_DIR/rea-$DATE.db
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
```

添加到 crontab：

```cron
0 2 * * * /opt/rea/scripts/backup.sh
```

### 恢复

```bash
cp backup/rea-20251201.db data/rea.db
systemctl restart rea-api
```

---

## 故障排查 / Troubleshooting

### 常见问题

#### 端口被占用

```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

#### 数据库锁定 (SQLite)

```bash
# 删除锁文件
rm -f data/rea.db-journal
```

#### CORS 错误

确认 `.env` 中 `CORS_ORIGINS` 包含前端实际地址。

#### 内存不足

- 减少 `WORKERS` 数量
- 启用 `CACHE_BACKEND=redis` 释放内存

#### 慢请求

- 启用缓存: `CACHE_TTL=600`
- 增加数据库索引
- 使用 `py-spy` 分析热点：

```bash
py-spy top --pid $(pgrep -f "uvicorn backend.api.main")
```

### 日志分析

```bash
# 实时跟踪
journalctl -u rea-api -f

# 最近错误
journalctl -u rea-api -p err -n 100

# 按时间范围
journalctl -u rea-api --since "1 hour ago"
```

### 联系支持

- GitHub Issues: <https://github.com/badhope/national_stats/issues>
- 邮箱: <security@rea.example.com>
- 文档: <https://rea.example.com/docs>

---

## 升级流程 / Upgrade Procedure

```bash
# 1. 备份
./scripts/backup.sh

# 2. 拉取新代码
cd /opt/rea/app
sudo -u rea git pull origin main

# 3. 更新依赖
sudo -u rea venv/bin/pip install -r requirements.txt

# 4. 数据库迁移（如有）
sudo -u rea venv/bin/alembic upgrade head

# 5. 重启服务
sudo systemctl restart rea-api

# 6. 验证
curl http://localhost:8000/health
```

---

## AI 助手 + 本地 Ollama (v7.0+)

```bash
# 1. 启动 ollama 服务
docker compose -f docker-compose.ollama.yml up -d

# 2. 拉模型
docker exec -it $(docker compose ps -q ollama) ollama pull qwen2.5:7b

# 3. 启 API
LLM_DEFAULT_BACKEND=ollama docker compose up --build

# 4. 验证
curl -s http://localhost:8000/api/v1/ai/config | jq
# 期望: active_backend = "ollama", model = "qwen2.5:7b"
```

数据完全在本机,适合生产/隐私场景。

---

**最后更新**: 2026-06-05
**当前版本**: v9.1.0
**配套文档**: [README.md](README.md) · [QUICKSTART.md](QUICKSTART.md) · [METHODOLOGY.md](docs/METHODOLOGY.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [API.md](API.md) · [CONSOLE_GUIDE.md](docs/CONSOLE_GUIDE.md) · [SDK_CLI_GUIDE.md](docs/SDK_CLI_GUIDE.md)
**适用版本**: v9.1.0+

---

## Web Console 部署 (v9.1+)

Web Console (`/console/`) 是一组静态 HTML + JS + CSS,挂在后端 :8000。**不需要单独的 frontend server**。

### 基本(同后端)

后端起来后,浏览器开 <http://localhost:8000/console/> 即可。

### 生产:加 basic auth

Web Console **没内置认证**。生产环境强烈建议在 nginx 层加 basic auth:

```bash
# 1. 创建密码文件
sudo apt install apache2-utils       # 装 htpasswd
sudo htpasswd -c /etc/nginx/.htpasswd console_user

# 2. nginx 配置 — 套 /console/ 路径(见上文 nginx 段)
location /console/ {
    auth_basic "RCA Console";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://rea_backend/console/;
}
```

### 生产:配置 SSE proxy

Web Console 的 chat 用 SSE (`/api/v1/admin/chat/stream`)。**Nginx 默认 buffer 会破坏 SSE** — 必须显式禁用:

```nginx
location /api/v1/admin/chat/stream {
    proxy_pass http://rea_backend;
    proxy_buffering off;       # 关键:禁用 buffer
    proxy_cache off;
    proxy_read_timeout 600s;   # 长 timeout,LLM 慢
}
```

### 部署后验证

```bash
# 1. 后端启动后能拉到 console 静态资源
curl -s -o /dev/null -w "HTTP %{http_code} size=%{size_download} bytes\n" \
    http://localhost:8000/console/index.html
# 期望: HTTP 200 size > 5000

# 2. 9 tool 端点都能返 data
for t in get_forecast get_diagnostics get_backtest get_risk get_scenarios \
         get_monte_carlo get_data_provenance get_macro_data get_list_cities; do
  echo -n "$t: "
  curl -s -o /dev/null -w "HTTP %{http_code}\n" \
    -X POST "http://localhost:8000/api/v1/admin/tools/$t/run" \
    -H 'Content-Type: application/json' \
    -d '{"scope":"city","name":"shenzhen","indicator":"gdp"}'
done
# 期望: 9 个 HTTP 200(macro_data/list_cities/body 需 {} )

# 3. config PUT 工作
curl -s -X PUT http://localhost:8000/api/v1/admin/config \
    -H 'Content-Type: application/json' \
    -d '{"temperature":0.5}' | jq '.temperature'
# 期望: 0.5

# 4. history 写入工作
curl -s "http://localhost:8000/api/v1/admin/history?limit=5" | jq '.items | length'
# 期望: 5(刚跑过的 5 个 tool)
```

详细 Console 用户指南:[docs/CONSOLE_GUIDE.md](docs/CONSOLE_GUIDE.md)

---

## Python SDK + CLI 部署 (v9.0+)

如果部署环境需要程序化调用分析工具,在 host 装 SDK:

```bash
pip install -e /opt/rea/app

# 验证
rca --version
python -c "import rca; print(rca.__version__)"   # 期望: 9.1.0(或者 git describe)
```

SDK 是 stateless,直接调后端 in-process 分析引擎。**不** 需要后端运行 — 适合 cron / ETL / 离线分析。

CLI 默认 3 种输出格式: `rich` / `plain` / `json`。

```bash
# 离屏 / cron
rca --format json forecast --city shenzhen --indicator gdp --years 5 > forecast.json

# pipe 给 jq
rca --format json monte-carlo --city shenzhen --indicator gdp --years 5 | jq '.data.quantiles.p50'
```

详细 SDK + CLI 用户指南:[docs/SDK_CLI_GUIDE.md](docs/SDK_CLI_GUIDE.md)

---
