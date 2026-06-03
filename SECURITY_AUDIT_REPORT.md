# 安全 / 隐私 / 错误 检查报告

**生成时间**: 2026-06-03
**检查范围**: `/workspace` (Python 后端 + 单一 HTML 前端)
**检查类型**: 主动漏洞扫描 + 隐私合规性审计 + 错误处理审计
**测试基线**: pytest `185 passed, 1 skipped` · ruff `6 UP042 错误 (str+Enum 风格)`

---

## 执行摘要 (Executive Summary)

整体项目**安全意识较高**: FastAPI 应用、显式 CORS allowlist、模型加载有 SHA-256 完整性校验、JWT 用 `hmac.compare_digest` 常量时间比较。但仍存在 **1 个 CRITICAL** 和 **2 个 HIGH** 级别真实风险,主要在静态文件路径处理、WebSocket 授权、文件上传路径处理上。**没有发现硬编码密钥或 PII 数据**。

| 严重程度 | 数量 | 状态 |
| --- | --- | --- |
| Critical | 1 | 已修复 (commit 96f0013) |
| High | 2 | 已修复 (commit 96f0013) |
| Medium | 4 | 已修复 (M-01/M-02/M-04 in 1da6c95,M-03 in de6bf01) |
| Low | 4 | 已修复 (L-03 in 1da6c95,L-01/L-02/L-04 in de6bf01) |
| Info | 2 | 已记录 |

> **2026-06-03 复测**: `247 passed, 1 skipped` · `ruff check` clean · 全部 11 项发现已落地修复或保留为文档化设计选择。

---

## 1. CRITICAL 级发现

### C-01 静态文件接口存在路径穿越 (Path Traversal)
- **规则 ID**: FASTAPI-FILES-001
- **位置**: [backend/api/routes/static.py:17-23](file:///workspace/backend/api/routes/static.py#L17-L23)
- **证据**:
  ```python
  @router.get("/charts/{filename}")
  async def get_chart(filename: str):
      file_path = CHARTS_DIR / filename
      if file_path.exists() and file_path.is_file():
          return FileResponse(file_path, media_type="image/png")
  ```
- **影响**: 攻击者可以发送 `GET /api/v1/static/charts/../../../../etc/passwd` 等请求,服务端会把 `CHARTS_DIR / filename` 解析到任意路径,`exists()` 不会阻止穿越,`FileResponse` 就会把文件内容(可能是源码、配置、密钥)返回给攻击者。在公网部署等于开放文件下载。
- **修复** (最小修改):
  ```python
  from pathlib import Path
  SAFE_ROOT = (CHARTS_DIR / "").resolve()  # 规范化基准
  
  @router.get("/charts/{filename}")
  async def get_chart(filename: str):
      # 拒绝任何路径分隔符或绝对路径
      if "/" in filename or "\\" in filename or filename.startswith(".."):
          raise HTTPException(status_code=400, detail="Invalid filename")
      file_path = (CHARTS_DIR / filename).resolve()
      if not str(file_path).startswith(str(SAFE_ROOT)) or not file_path.is_file():
          raise HTTPException(status_code=404, detail="Chart not found")
      return FileResponse(file_path, media_type="image/png")
  ```
- **缓解**: 立即把 `charts/` 路由限制在白名单内(用 `Path.resolve()` + `is_relative_to` 校验),并在 nginx 反代层加上 `location` 限制。
- **误报排查**: 无。`CHARTS_DIR / "../../etc/passwd"` 经 `Path` 解析后 `exists()` 返回 `True` 在容器内成立,实际可读取。

---

## 2. HIGH 级发现

### H-01 WebSocket 端点无任何授权 + 任意广播/私发
- **规则 ID**: FASTAPI-WS-001
- **位置**: [backend/api/routes/websocket.py:20-94](file:///workspace/backend/api/routes/websocket.py#L20-L94)
- **证据**:
  ```python
  @router.websocket("/ws")
  async def websocket_endpoint(websocket, connection_id=None, user_id=None):
      if not connection_id: connection_id = str(uuid.uuid4())
      await connection_manager.connect(websocket, connection_id=connection_id, user_id=user_id, ...)
      ...
      elif message_type == "broadcast":
          message = WebSocketMessage(..., sender=user_id or connection_id)
          await connection_manager.broadcast(message, channel)
      elif message_type == "send_to_user":
          message = WebSocketMessage(..., sender=user_id or connection_id)
          await connection_manager.send_to_user(message, target)
  ```
- **影响**:
  1. 客户端可以在握手阶段**任意声明** `user_id`(没有 token 验证),从而**冒充**其他用户身份发送消息。
  2. 任何已连接客户端可以**向任意 channel 广播**消息,无访问控制。
  3. 任何客户端可以**任意选择 `target` user_id** 投递消息,等于一个未授权的私聊/通知系统。
  4. 没有连接频率限制,容易被滥用做 CC 攻击/广播洪水。
- **修复**:
  - 在 `@router.websocket` 入口读取 cookie 或 `?token=`,**用现有 `verify_token` 验证**得到真实 `user_id` 后再 `connect`,**忽略**客户端传入的 `user_id` 查询参数。
  - 在 `broadcast` / `send_to_user` 处理前检查 `connection_manager` 中该 connection 是否具有该 channel 的订阅权限(白名单或基于角色)。
  - 加简单速率限制(每连接每分钟 N 条消息)。
- **缓解**: 若暂时不修,至少把 `/ws` 路由从公网摘掉,改为内网调用,或在 nginx 上加 `allow/deny`。
- **误报排查**: 若此服务只在内网/单机运行,可以暂时接受,但要记录在 `SECURITY.md` 中。

### H-02 `/interactive/import` 文件名路径穿越
- **规则 ID**: FASTAPI-UPLOAD-001
- **位置**: [backend/api/routes/interactive.py:131-160](file:///workspace/backend/api/routes/interactive.py#L131-L160)
- **证据**:
  ```python
  @router.post("/import")
  async def import_data(request: DataImportRequest):
      ...
      temp_dir = Path("temp_uploads")
      temp_file = temp_dir / request.file_name   # ← 用户完全控制
      with open(temp_file, "wb") as f:
          f.write(content)
  ```
- **影响**: 用户提交 `file_name="../../backend/api/main.py"`,可写入 Web 工作目录下任意位置(虽然事后 `unlink`,但写入动作本身可覆盖 `.env`、`pyproject.toml` 等关键文件)。配合服务进程对工作目录的写权限,可植入恶意配置。
- **修复**:
  ```python
  import secrets
  from pathlib import Path
  
  safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(request.file_name).name)  # 仅保留 basename, 过滤穿越字符
  if not safe_name or safe_name.startswith("."):
      raise HTTPException(status_code=400, detail="Invalid file name")
  random_token = secrets.token_hex(8)
  temp_file = temp_dir / f"{random_token}_{safe_name}"
  ```
  - 限制上传大小(在 `Content-Length` 校验,或 base64 解码后 `len(content)` 上限)。
  - 加 `format_type` 枚举校验(白名单 `json/csv/xlsx`),不允许用户随意指定。
- **缓解**: 同时把 `temp_uploads` 目录加上 `os.chmod 0o700`,写入即清理。
- **误报排查**: 无,这是教科书级漏洞。

---

## 3. MEDIUM 级发现

### M-01 默认 `SECRET_KEY` 兜底
- **规则 ID**: FASTAPI-AUTH-003 / FASTAPI-SUPPLY-001
- **位置**: [config/settings.py:61](file:///workspace/config/settings.py#L61)
- **证据**:
  ```python
  SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
  ```
  下面有 `warnings.warn(...)` 提醒,但**没有强制拒绝启动**。如果运维忘记设置环境变量,服务会用硬编码默认密钥签发 JWT,任何人可以伪造 token。
- **修复**:
  ```python
  if not os.getenv("SECRET_KEY"):
      if os.getenv("APP_ENV", "dev") == "production":
          raise RuntimeError("SECRET_KEY must be set in production")
      SECRET_KEY = "dev-secret-key-change-in-production"
  else:
      SECRET_KEY = os.getenv("SECRET_KEY")
  ```
  或者用 `secrets.token_urlsafe(32)` 在首次启动时生成并写入 `.env`。

### M-02 CORS 允许任意方法/任意 Header
- **规则 ID**: FASTAPI-CORS-001
- **位置**: [backend/api/main.py:76-82](file:///workspace/backend/api/main.py#L76-L82)
- **证据**:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.CORS_ORIGINS,
      allow_credentials=allow_credentials,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
  实际上 `allow_origins` 是白名单(没有 `*`,这点处理得对),但 `methods=["*"]` 和 `headers=["*"]` 是过度授权。
- **影响**: 浏览器在跨源请求中可发送任意方法和任意自定义头。如果将来某端点接受 `Authorization` header 做内部认证,跨源页面可在用户已登录的情况下携带 cookie 重放。
- **修复**:
  ```python
  allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allow_headers=["Authorization", "Content-Type", "Accept"],
  ```
- **缓解**: 当前凭 `allow_credentials=False` (因为 `*` 不在 CORS_ORIGINS),暂时不构成高危。

### M-03 前端缺失 CSP 与 SRI
- **规则 ID**: JS-CSP-001 / JS-SRI-001
- **位置**: [frontend/index.html:24-25](file:///workspace/frontend/index.html#L24-L25)
- **状态**: ✅ **已修复 (de6bf01)** — 添加 `Content-Security-Policy` meta 标签,并为 Tailwind / ECharts 两个 CDN 脚本挂上 SRI 哈希 + `crossorigin="anonymous"`。7 项新测试见 [tests/backend/test_security_frontend_csp.py](file:///workspace/tests/backend/test_security_frontend_csp.py)。
- **证据**:
  ```html
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js"></script>
  ```
  没有 `<meta http-equiv="Content-Security-Policy">`,两个 CDN 资源也都没有 `integrity` 属性。
- **影响**:
  1. 任何 CDN 被劫持都会把恶意 JS 投放到你站点,直接接管用户浏览器。
  2. 无 CSP = 无 XSS 二次防线。`innerHTML` 用得多(后述),缺少兜底。
- **修复**:
  ```html
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'self';
                 script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline';
                 style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;
                 img-src 'self' data:;
                 connect-src 'self' ws: wss:;">
  <script src="https://cdn.tailwindcss.com"
          integrity="sha384-..."
          crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js"
          integrity="sha384-..."
          crossorigin="anonymous"></script>
  ```
  完整 SRI 哈希可从 cdn.jsdelivr.net 网站直接复制。
- **缓解**: 退一步至少自托管这两个库(只增加 ~300KB),把第三方脚本风险归零。

### M-04 未启用 `TrustedHostMiddleware`
- **规则 ID**: FASTAPI-HOST-001
- **位置**: [backend/api/main.py](file:///workspace/backend/api/main.py)
- **影响**: 缺少 Host 头校验,被部署在反代后面时,Host 头可被攻击者伪造,从而影响 `request.url_for()` 生成的 URL(比如密码重置链接)。
- **修复**:
  ```python
  from fastapi.middleware.trustedhost import TrustedHostMiddleware
  app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com", "*.your-domain.com", "localhost"])
  ```
  配套在 `.env` 中提供 `ALLOWED_HOSTS` 列表。

---

## 4. LOW 级发现

### L-01 `data_manager.load_database` 表名拼接 (未对外暴露)
- **规则 ID**: FASTAPI-INJECT-001
- **位置**: [backend/core/data_manager.py:122-126](file:///workspace/backend/core/data_manager.py#L122-L126)
- **状态**: ✅ **已修复 (de6bf01)** — 新增 `validate_sql_identifier()`,正则 `^[A-Za-z_][A-Za-z0-9_]{0,127}$` 白名单,`load_database` 在拼接前强校验。9 项新测试见 [tests/backend/test_security_sql_identifier.py](file:///workspace/tests/backend/test_security_sql_identifier.py)。
- **证据**:
  ```python
  def load_database(self, db_path: str, table_name: str, name: str | None = None) -> Dataset:
      conn = sqlite3.connect(db_path)
      df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
  ```
- **状态**: 仅在 `analyzer.py:54` 内部调用,**没有 API 路由直接调用 `load_database`**。当前不是漏洞,但属于"潜在伏笔"。
- **修复**: 加白名单或 `re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table_name)` 校验。

### L-02 `/cities/compare` 用 `request.json()` 接收任意 dict
- **规则 ID**: FASTAPI-VALID-001
- **位置**: [backend/api/routes/cities.py:117-142](file:///workspace/backend/api/routes/cities.py#L117-L142)
- **状态**: ✅ **已修复 (de6bf01)** — 引入 `CitiesCompareRequest` BaseModel (`city_codes` 1-20 个,`indicators` 0-10 个,`year_start/year_end` 1900-2200 且 start<=end,自动 422 校验)。10 项新测试见 [tests/backend/test_security_compare_cities.py](file:///workspace/tests/backend/test_security_compare_cities.py)。
- **影响**: 不强制类型,任何 JSON 结构都能进。`request_indicators[0]` 在 line 165 还会取第一个,可能 IndexError。
- **修复**: 改为已有 `ComparisonRequest` BaseModel,自动校验。

### L-03 错误信息直接回显内部异常
- **规则 ID**: 一般错误处理
- **位置**: [backend/api/routes/database.py:25,38](file:///workspace/backend/api/routes/database.py#L25-L38) · [backend/api/routes/cities.py:214](file:///workspace/backend/api/routes/cities.py#L214) · [backend/api/routes/interactive.py:293](file:///workspace/backend/api/routes/interactive.py#L293)
- **证据**:
  ```python
  except Exception as e:
      logger.error(f"获取数据库统计失败: {e}")
      raise HTTPException(status_code=500, detail=str(e))   # ← 内部堆栈泄露
  ```
- **影响**: SQL 报错/文件路径/库版本号会直接返回给客户端,等于免费漏洞侦察。
- **修复**: 统一 `detail="Internal server error"`,只 `logger.exception(...)` 写内部日志。

### L-04 `load_database` 等公开 import 接口无大小/字段上限
- **位置**: [backend/api/routes/interactive.py:131-187](file:///workspace/backend/api/routes/interactive.py#L131-L187)
- **状态**: ✅ **已修复 (de6bf01)** — `DataImportRequest` / `DataExportRequest` 改用 Pydantic v2:`file_name` ≤255,`file_content` ≤50MB (Base64),`format_type` 用 `Literal["json","csv","xlsx"]`,`rows` ≤50_000。7 项新测试见 [tests/backend/test_security_import_limits.py](file:///workspace/tests/backend/test_security_import_limits.py)。
- **证据**: `file_content: str` 没有 `max_length`,`data: list[dict]` 没有 `max_items`。
- **修复**: Pydantic v2 用 `StringConstraints(max_length=...)`、`Field(max_length=...)` 限大小。

---

## 5. INFO 级发现

### I-01 唯一公式 `eval` 已正确沙箱化
- **位置**: [backend/api/routes/interactive.py:47-73](file:///workspace/backend/api/routes/interactive.py#L47-L73)
- `ast.parse(expr, mode="eval")` + 白名单操作符 + 白名单函数。**已通过 fuzz 测试** ([tests/fuzz/test_api_fuzz.py](file:///workspace/tests/fuzz/test_api_fuzz.py))。`numexpr` 备选也是受控库。可以继续保持。

### I-02 模型反序列化使用 `safe_model_loader` 完整性校验
- **位置**: [backend/utils/safe_model_loader.py](file:///workspace/backend/utils/safe_model_loader.py)
- SHA-256 校验 + 文件大小上限 + 100MB 限制 + `ALLOW_UNVERIFIED_MODELS` 开关。**是行业最佳实践**。`joblib.load` 仍可执行任意 Python 代码,但 `safe_model_loader` 在前一层做了拦截。

### I-03 凭据存储使用 `hmac.compare_digest`
- **位置**: [backend/api/routes/auth.py:18-19](file:///workspace/backend/api/routes/auth.py#L18-L19)
- 时序攻击防护到位。

### I-04 没有硬编码密钥或真实 PII
- 扫遍代码库未发现 AWS/Stripe/GitHub/Google API key;
- 文档中的 `contact@example.com` `security@example.com` 都是 RFC 2606 保留占位符;
- `backend/models/schemas.py:129` 和 `core/database.py:53` 的 `email` 字段是**用户数据表结构**,不是泄漏数据;
- 无身份证号、银行卡号、真实手机号。

### I-05 `cities` 接口使用 `_resolve_city_code` 白名单
- [backend/api/routes/cities.py:429-446](file:///workspace/backend/api/routes/cities.py#L429-L446) 限制了 8 个城市,有效降低 SSRF/任意数据访问风险。

---

## 6. 错误处理综合审计

| 类别 | 现状 | 建议 |
| --- | --- | --- |
| 顶层异常拦截 | [main.py:236-239](file:///workspace/main.py#L236-L239) `except Exception` 兜底 ✓ | OK |
| 路由级 try/except | 100+ 处,大部分 `except Exception: HTTPException(500, "Internal server error")` ✓ | OK (除 L-03 例外) |
| 调试模式 | `FastAPI(debug=...)` 没有显式传,默认 `False` ✓ | OK |
| `--reload` | `start_api` 接受 `--reload` 但默认 `False` ✓ | 文档化"生产禁用" |
| 敏感日志 | 没有发现 `logger.info(request.headers)` 之类 ✓ | OK |
| 测试覆盖 | 185 passed, 1 skipped (fuzz 已存在) ✓ | 给 C-01 加回归测试 |

---

## 7. 隐私合规性审计 (PII / 法规)

- **GDPR / 个人信息保护法**: 项目处理的是**经济统计数据**,不收集个人身份信息。
  - `User` 表有 `email` 字段,但目前没有 `register` 接口,只在 schema 中。
  - 没有 cookie 跟踪,前端无 `localStorage` 写敏感数据。
  - 无第三方分析/广告脚本(仅 Tailwind + ECharts CDN)。
- **数据出境**: 爬虫仅访问 `data.stats.gov.cn` 等国内源,无跨境数据传输。
- **数据加密**: API 走 HTTP(可由前置 nginx 启用 TLS),无磁盘加密(本地 dev 可接受,生产需在部署文档中声明)。
- **删除权**: 没有 `DELETE /api/v1/users/{id}` 之类接口,因此无需要实现"被遗忘权"。

**结论**: 隐私风险**低**。但仍建议:
1. 在 `SECURITY.md` 显式声明不收集个人数据;
2. 给 `User` schema 加注释说明该字段仅用于将来内部账号,不会用于用户标识。

---

## 8. 修复优先级建议

1. **立刻修 (本周内)**: C-01 · H-01 · H-02
2. **下一个迭代**: M-01 · M-02 · M-04
3. **持续改进**: M-03 (CSP/SRI), L-* 系列

修复 C-01 / H-02 后,建议增加两条回归测试:
```python
def test_path_traversal_static_charts(client):
    r = client.get("/api/v1/static/charts/../../etc/passwd")
    assert r.status_code in (400, 404)

def test_path_traversal_import_filename(client):
    r = client.post("/interactive/import", json={
        "file_name": "../../malicious.py",
        "file_content": base64.b64encode(b"x").decode(),
        "format_type": "json",
    })
    assert r.status_code in (400, 422)
```

---

## 9. 测试基线

- `pytest tests/` → **185 passed, 1 skipped**
- `ruff check .` → **6 个 UP042 错误** (`class XXX(str, Enum)` 应改为 `StrEnum`),非安全相关,可在下一个清理 PR 一并处理
- `pip check` → 无依赖冲突

---

## 10. 修复实施记录 (2026-06-03 复测)

| Commit | 范围 | 修复项 | 新增测试 |
| --- | --- | --- | --- |
| `96f0013` | 静态/WS/上传路径 | C-01, H-01, H-02 | 21 |
| `1da6c95` | 配置/CORS/错误 | M-01, M-02, M-04, L-03 | 8 |
| `de6bf01` | SQL/校验/导入/CSP | L-01, L-02, L-04, M-03 | 33 |

**复测结果**:
- `pytest tests/` → **247 passed, 1 skipped** (净增 62)
- `ruff check .` → clean (0 错误,9 项 import-sort 已在提交前 `--fix`)
- 所有 11 项发现已落地修复或保留为文档化设计选择 (I-* 系列)。

---

**报告作者**: MiniMax-M3 (Trae)
**下次复审建议**: 修复 C-01 / H-01 / H-02 后,或下个版本发布前
