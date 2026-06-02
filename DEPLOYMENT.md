# 部署指南 / Deployment Guide

本文档介绍如何在不同环境中部署 **区域产业经济分析平台**。

This document describes how to deploy the **Regional Industrial Economic Analysis Platform** in different environments.

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

### 5. 启动后端

```bash
# 方式 1: 通过 Makefile
make run

# 方式 2: 直接启动
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 启动前端（新终端）

```bash
# 方式 1
make run-frontend

# 方式 2
cd frontend && python3 -m http.server 8080
```

### 7. 访问应用

- 前端: <http://localhost:8080>
- 后端 API: <http://localhost:8000/api/v1>
- API 文档: <http://localhost:8000/api/docs>

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
| `api` | 8000 | FastAPI 后端 |
| `frontend` | 8080 | 静态前端 (Nginx) |
| `db` | 5432 | PostgreSQL (可选) |
| `redis` | 6379 | Redis 缓存 (可选) |

### 单独构建镜像

```bash
# 后端
docker build -t rea-backend:latest .

# 前端 (使用独立 Dockerfile)
docker build -t rea-frontend:latest -f Dockerfile.frontend .
```

### 推送至镜像仓库

```bash
docker tag rea-backend:latest your-registry.example.com/rea-backend:v4.0.0
docker push your-registry.example.com/rea-backend:v4.0.0
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

    # 前端静态资源
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

- GitHub Issues: <https://github.com/your-org/regional-economic-analysis/issues>
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

**最后更新**: 2026-06-02
**适用版本**: v4.0.0+
