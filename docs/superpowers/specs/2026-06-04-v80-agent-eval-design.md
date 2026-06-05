# v8.0 Agent 增强 + Eval 框架 — 设计

> Date: 2026-06-04
> Status: **Approved** (待 plan)
> Predecessor: v7.1 (tool-call UI + chip 链接),v7.0 (chat widget + ReAct)
> Scope: 自研增强(不引入 LangGraph / smolagents / Pydantic AI)

## 1. 目标

把现有自研 ReAct agent 补完到"生产可用"水平,并搭建一个 eval/benchmark 框架支撑后续迭代。

**用户已批准范围(最小可用子集)**:
- ✅ 多模型 fallback 链(35 个阿里百炼模型自动降级)
- ✅ 并行 tool 执行
- ✅ Trace 日志(decision observability)
- ✅ 反射重试(reflect on tool error)
- ✅ Golden eval 框架(tool-call 准确度 + 多模型对比)

**用户已决定不做(YAGNI)**:
- ❌ LangGraph / smolagents / Pydantic AI(走自研)
- ❌ 状态持久化(checkpoint/resume)— v8.1
- ❌ Human-in-the-loop — v8.1
- ❌ 真实 token-by-token streaming — v8.1
- ❌ 子 agent 委派 — v8.2
- ❌ 跨 session 长期记忆 — v8.2
- ❌ Chart 嵌入 — 已有 navigate_to chip 链接,实际 chart 渲染由前端投资 grade 页负责

## 2. 现状(v7.1 结尾状态)

`backend/ai/chat_service.py::chat_stream_with_trace()` 是单层 30 行循环:

```
thinking → llm_client.chat() → tool_calls?
   ├─ 无 → yield token + done
   └─ 有 → execute_tool (顺序) → 喂回 LLM
            ↓ 超 max_tool_rounds → 强制总结
```

**已有能力**:
- 同步 `chat()` + 流式 `chat_stream_with_trace()`
- 9 个 tool 通过 `tool_registry.TOOLS` 暴露
- SSE 事件链:`thinking → tool_call → token → done`
- 30 分钟 TTL session history
- Token 用量记录(但无成本追踪)

**缺口**:
- 单 LLM 调用,无 fallback
- 顺序 tool 执行
- 无 trace(出错难 debug)
- 无反思(tool 失败直接 yield error)
- 无 eval 框架(改 prompt/换模型后靠手工测)

## 3. 架构(方案 A:分层独立)

```
backend/ai/
  chat_service.py        # 改:组合调用 4 个新函数 (~30 行 diff)
  llm_client.py          # 不改
  tool_executor.py       # 不改
  tool_registry.py       # 不改
  conversation.py        # 不改
  config.py              # 改:加 fallback_chain / tool_timeout_sec 字段 (~20 行 diff)
  
  ├─ fallback.py         # 新:多模型降级链 (~60 行)
  ├─ parallel_tools.py   # 新:并行 tool 执行 (~40 行)
  ├─ trace.py            # 新:Step + TraceStore (~80 行)
  └─ retry.py            # 新:反射重试 (~50 行)
```

**总改动 ~280 行新代码 + ~50 行修改**。

### 3.1 `backend/ai/fallback.py`

```python
@dataclass(frozen=True)
class ModelEntry:
    backend: str      # "openai" / "anthropic" / "ollama"
    model: str        # "qwen-max" / "deepseek-v3" / ...
    priority: int     # 0=首选,1=次选...
    label: str        # 人读名,e.g. "qwen-max (默认)"

# 来自 docs/AI_MODEL_REGISTRY.md 实测 25 个全功能模型
DEFAULT_FALLBACK_CHAIN: list[ModelEntry] = [
    ModelEntry("openai", "qwen-max",                     0, "qwen-max (默认)"),
    ModelEntry("openai", "qwen-long",                    1, "qwen-long (长文本)"),
    ModelEntry("openai", "qwen-coder-turbo",             2, "qwen-coder-turbo (代码)"),
    ModelEntry("openai", "deepseek-v3",                  3, "deepseek-v3 (第三方)"),
    ModelEntry("openai", "kimi-k2.5",                    4, "kimi-k2.5 (兜底)"),
]

# 错误分类
class LLMError(Exception): ...            # 通用
class FallbackError(LLMError): ...        # 链全失败
class FatalLLMError(LLMError): ...        # 不可重试(Auth/NotFound/AccessDenied)

def run_with_fallback(
    messages: list[dict],
    tools: list[dict] | None,
    chain: list[ModelEntry] | None = None,
) -> tuple[LLMResponse, ModelEntry]:
    """循环 chain,成功立刻返;可重试错误降级下一项;致命错误抛 FatalLLMError;
    链全失败抛 FallbackError。
    
    可重试错误(timeout / network / free_tier_exhausted / 429 rate_limit)→ 降级
    不可重试错误(401 / 403 / 404)→ 立刻抛 FatalLLMError(不浪费降级预算)
    """
```

**错误分类规则** (在 litellm 异常上做 mapping):
| litellm 异常 | 分类 | 行为 |
|---|---|---|
| `litellm.Timeout` | retryable | 降级下一项 |
| `litellm.APIConnectionError` | retryable | 降级下一项 |
| `AuthenticationError` (401) | fatal | 抛 FatalLLMError |
| `PermissionDeniedError` (403) | fatal | 抛 FatalLLMError |
| `NotFoundError` (404) | fatal | 抛 FatalLLMError |
| `RateLimitError` (429) | retryable | 降级下一项 |
| 其他 APIError 含 "free tier" / "exhausted" | retryable | 降级下一项 |
| 其他 | retryable | 降级下一项 |

### 3.2 `backend/ai/parallel_tools.py`

```python
def execute_tools_parallel(
    tool_calls: list[ToolCall],
    max_workers: int = 5,
    tool_timeout_sec: int = 30,
) -> list[dict]:
    """concurrent.futures.ThreadPoolExecutor 并行 execute_tool。
    
    顺序:保持入参顺序返回
    异常:单个 tool 抛异常不影响其他,异常包装成 {"error": "<name>: <msg>", "navigate_to": None}
    超时:每个 tool 默认 30s(从 cfg.tool_timeout_sec 读)
    """
```

**实现细节**:
- 用 `ThreadPoolExecutor` 而非 `asyncio`,因为 `execute_tool` 是同步(可能调 CPU-bound 模拟)
- `max_workers=5` 默认,9 个 tool 不可能一次全调
- `tool_timeout_sec=30` 默认,某些 tool(forecast/monte_carlo)可能需要更久 — 留 cfg 配置

### 3.3 `backend/ai/trace.py`

```python
@dataclass
class Step:
    round: int                       # 第几轮 (1-indexed)
    type: str                         # "llm_call" / "tool_call" / "tool_result" / "fallback" / "retry" / "done"
    model_used: str | None = None     # 本步用了哪个 model
    tool_name: str | None = None
    tool_args: dict | None = None     # tool args(脱敏前 500 字符)
    tool_result_preview: str | None = None  # JSON.dumps 前 200 字符
    duration_ms: int = 0
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict: ...    # JSON-serializable

class TraceStore:
    def __init__(self, max_steps: int = 200): ...
    def append(self, step: Step) -> None: ...
    def get_all(self) -> list[dict]: ...    # 返 list of to_dict()
    def clear(self) -> None: ...
```

**事件类型**:
- `llm_call` — 一次 LLM 调用(记录 model_used / duration / token)
- `tool_call` — 一次 tool dispatch(记录 tool_name / args / duration)
- `tool_result` — tool 返值预览(记 result_preview)
- `fallback` — LLM 失败降级(记 from_model / to_model / reason)
- `retry` — 反射重试(记 tool_name / error / hint)
- `done` — agent 结束(记 reason / total_rounds / total_tokens)

**前端**:`done` 事件增加 `trace` 字段,前端可折叠显示 "decision trace"(v8.0.1)

### 3.4 `backend/ai/retry.py`

```python
# 可重试的 tool 错误白名单
RETRYABLE_TOOL_ERRORS: set[str] = {
    "city_not_found",         # 缺/错参数,让 LLM 改 name
    "data_unavailable",       # 数据缺失,让 LLM 换 scope/year
    "missing_required_fields",# 缺必填,让 LLM 补
    "timeout",
}

def should_retry(tool_result: dict) -> bool:
    """tool 返的 error 字段在 RETRYABLE_TOOL_ERRORS 白名单 → True"""

def build_retry_hint(tool_name: str, original_args: dict, error: str) -> str:
    """构造 user 消息 hint 给 LLM,引导它改参数重试。
    
    返回: "[系统提示] tool `get_forecast` 调用失败(错误: city_not_found)。
           原参数: {name: 'shenzhenx'}(可能是拼写错误)。
           请用正确的城市名(如 'shenzhen' 或 '深圳')重新调用。"
    """
```

**重试策略**:
- 单 tool 失败 → 在同一 round 内追加 user hint 消息(不重置 messages)
- 整 LLM 下一轮会看到 hint + 之前的 tool result,自动改参数再调
- 最多 1 次反射重试(避免无限循环)— 第 2 次还失败就 yield error
- 重试本身记入 trace(不消耗 max_tool_rounds)

### 3.5 `chat_service.py` 改造(伪代码)

```python
def chat_stream_with_trace(cfg, session_id, user_message):
    yield {"type": "thinking"}
    messages = _build_messages(session_id, user_message)
    trace = TraceStore()
    tool_rounds = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    last_error: str | None = None
    
    for _ in range(cfg.max_tool_rounds + 1):
        # 1. LLM (带 fallback + trace)
        t0 = time.perf_counter()
        try:
            resp, used_model = run_with_fallback(messages, TOOLS, cfg.fallback_chain)
        except FatalLLMError as e:
            trace.append(Step(type="llm_call", error=str(e), duration_ms=int((time.perf_counter()-t0)*1000)))
            yield {"type": "error", "message": str(e), "trace": trace.get_all()}
            return
        except FallbackError as e:
            trace.append(Step(type="llm_call", error=str(e), duration_ms=int((time.perf_counter()-t0)*1000)))
            yield {"type": "error", "message": f"所有模型都不可用: {e}", "trace": trace.get_all()}
            return
        total_prompt_tokens += resp.prompt_tokens
        total_completion_tokens += resp.completion_tokens
        trace.append(Step(round=tool_rounds+1, type="llm_call", model_used=used_model.model, duration_ms=int((time.perf_counter()-t0)*1000), metadata={"prompt_tokens": resp.prompt_tokens, "completion_tokens": resp.completion_tokens}))
        
        if not resp.tool_calls:
            # LLM 给了最终答案
            content = resp.content or ""
            yield {"type": "token", "content": content}
            conversation.append_message(session_id, {"role": "user", "content": user_message})
            conversation.append_message(session_id, {"role": "assistant", "content": content})
            trace.append(Step(round=tool_rounds+1, type="done", metadata={"reason": "stop", "total_tokens": total_prompt_tokens+total_completion_tokens}))
            yield {"type": "done", "finish_reason": "stop", "tool_rounds": tool_rounds, "tool_calls": [], "trace": trace.get_all()}
            return
        
        # 2. 把 LLM 的 tool_call 决策加进 messages
        messages.append({
            "role": "assistant",
            "content": resp.content or "",
            "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)}} for tc in resp.tool_calls],
        })
        
        # 3. 并行执行 tool
        t1 = time.perf_counter()
        results = execute_tools_parallel(resp.tool_calls, tool_timeout_sec=cfg.tool_timeout_sec)
        parallel_ms = int((time.perf_counter()-t1)*1000)
        for tc, result in zip(resp.tool_calls, results):
            preview = json.dumps(result.get("data") or result, ensure_ascii=False, default=str)[:200]
            tool_event = {
                "type": "tool_call",
                "name": tc.name,
                "args": tc.arguments,
                "navigate_to": result.get("navigate_to"),
                "data_preview": preview if "data" in result else None,
                "error": result.get("error"),
            }
            yield tool_event
            trace.append(Step(round=tool_rounds+1, type="tool_call", tool_name=tc.name, tool_args=tc.arguments, tool_result_preview=preview, duration_ms=parallel_ms//len(resp.tool_calls), error=result.get("error")))
        
        # 4. 反射重试 hint
        for tc, result in zip(resp.tool_calls, results):
            if should_retry(result):
                hint = build_retry_hint(tc.name, tc.arguments, result["error"])
                messages.append({"role": "user", "content": hint})
                trace.append(Step(type="retry", tool_name=tc.name, error=result["error"]))
        
        # 5. tool results 进 messages
        for tc, result in zip(resp.tool_calls, results):
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": tc.name,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
        
        tool_rounds += 1
        if tool_rounds >= cfg.max_tool_rounds:
            messages.append({"role": "user", "content": "请基于已有 tool 结果直接给最终答案,不要再调 tool。"})
            try:
                resp2, used_model2 = run_with_fallback(messages, TOOLS, cfg.fallback_chain)
            except (FatalLLMError, FallbackError) as e:
                resp2 = None
                last_error = str(e)
            content = (resp2.content if resp2 else None) or "(问题过于复杂,无法在限定步数内回答)"
            yield {"type": "token", "content": content}
            conversation.append_message(session_id, {"role": "user", "content": user_message})
            conversation.append_message(session_id, {"role": "assistant", "content": content})
            trace.append(Step(round=tool_rounds+1, type="done", metadata={"reason": "tool_rounds_exhausted", "forced_stop": True, "total_tokens": total_prompt_tokens+total_completion_tokens, "error": last_error}))
            yield {"type": "done", "finish_reason": "tool_rounds_exhausted", "tool_rounds": tool_rounds, "forced_stop": True, "tool_calls": [], "trace": trace.get_all()}
            return
    
    yield {"type": "done", "finish_reason": "max_rounds", "tool_rounds": tool_rounds, "tool_calls": [], "trace": trace.get_all()}
```

### 3.6 `config.py` 改造

```python
@dataclass
class AIConfig:
    # ... 现有字段 ...
    fallback_chain: list[ModelEntry] = field(default_factory=lambda: list(DEFAULT_FALLBACK_CHAIN))
    tool_timeout_sec: int = 30
    parallel_max_workers: int = 5
```

`load_config()` 从 env `LLM_FALLBACK_CHAIN` (JSON) 读,没设用 default。

## 4. Eval 框架

### 4.1 目录结构

```
tests/eval/
  __init__.py
  golden_cases.jsonl       # 10-20 个 case
  run_eval.py              # CLI 入口
  scorer.py                # 评分逻辑
  reporter.py              # 报表生成
  
  reports/                 # 自动生成(每次跑 eval 一个 JSON)
    2026-06-04-qwen-max.json
    2026-06-04-deepseek-v3.json
    ...
```

### 4.2 Golden case 格式

```json
{
  "id": "shenzhen-gdp-forecast-3y",
  "query": "深圳 GDP 2024-2026 预测多少?",
  "expected_tools": ["get_forecast"],
  "expected_args_match": {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3},
  "expected_keywords": ["深圳", "GDP", "预测", "万亿"],
  "max_tool_rounds": 2,
  "timeout_sec": 60
}
```

**字段说明**:
- `id` — 唯一标识
- `query` — 自然语言查询
- `expected_tools` — 期望调用的 tool 列表(顺序无关)
- `expected_args_match` — 期望的 args 子集(每个 key 都要匹配,允许 extra)
- `expected_keywords` — 最终答案里应包含的关键词(>= 50% 命中算 pass)
- `max_tool_rounds` — 超此数算 fail
- `timeout_sec` — 单 case 超时

### 4.3 评分维度(每 case 0-100 分)

| 维度 | 权重 | 评分 |
|------|------|------|
| **tool 选择** | 30 | 集合完全匹配 = 30,部分匹配按比例 |
| **args 匹配** | 20 | expected_args_match 全 key 命中 = 20,按命中比例 |
| **关键词** | 20 | expected_keywords 命中 >= 50% = 20,按比例 |
| **延迟** | 15 | < 10s = 15,< 30s = 10,< 60s = 5,>= 60s = 0 |
| **fallback 触发** | 10 | 0 次 = 10,1 次 = 5,>= 2 次 = 0(说明首选不稳定) |
| **token 效率** | 5 | < 2K = 5,< 5K = 3,>= 5K = 1 |

**总 pass 条件**:总分 >= 70 AND tool 选择分 >= 20(必须选中正确 tool)

### 4.4 CLI 用法

```bash
# 跑单模型
python -m tests.eval.run_eval --model qwen-max

# 跑多模型对比
python -m tests.eval.run_eval --compare qwen-max deepseek-v3 kimi-k2.5

# 跑指定 case 子集
python -m tests.eval.run_eval --model qwen-max --ids shenzhen-gdp-forecast-3y

# 报告输出
tests/eval/reports/2026-06-04-compare.json
{
  "summary": {
    "qwen-max":   {"avg_score": 87.5, "pass_rate": 0.90, "total_cases": 10},
    "deepseek-v3":{"avg_score": 82.0, "pass_rate": 0.80, "total_cases": 10},
    "kimi-k2.5":  {"avg_score": 79.0, "pass_rate": 0.70, "total_cases": 10}
  },
  "cases": [...]
}
```

## 5. 测试策略(~20 个新测试)

| 文件 | 测试数 | 覆盖 |
|------|--------|------|
| `tests/backend/test_ai_fallback.py` | 5 | 成功首选 / 首选超时降级 / 致命错误立即抛 / 链全失败抛 / 自定义链 |
| `tests/backend/test_ai_parallel_tools.py` | 3 | 3 个 tool 并行 / 1 失败不影响其他 / 顺序保持 |
| `tests/backend/test_ai_trace.py` | 3 | Step 序列化 / TraceStore append+get_all / max_steps 截断 |
| `tests/backend/test_ai_retry.py` | 3 | city_not_found 触发重试 / 非白名单不重试 / hint 含原 args |
| `tests/backend/test_ai_eval.py` | 4 | 读 golden / 跑 1 case / tool 匹配 / 报告生成 |
| `tests/backend/test_ai_chat_stream_v8.py` | 2 | fallback SSE event / trace 在 done 事件中 |

**总测试数:76 (v7.1) + 20 (v8.0) = 96 pass**

## 6. 验收标准

- ✅ 96/96 测试 pass(包括 v7.1 回归)
- ✅ multi-model smoke:25/34 仍 pass(链不破坏现有能力)
- ✅ 新增 eval:qwen-max vs deepseek-v3 vs kimi-k2.5 在 10 个 golden case 上对比报告
- ✅ 真 LLM SSE 端到端验证(单次 LLM 调用,不实际触发 fallback):
  - fallback event (mock 触发)
  - parallel tool_call(发 2 个 tool 的 query)
  - retry hint event(发 city_not_found 的 query)
  - trace 在 done 事件中
- ✅ Ruff clean(修改 + 新文件)
- ✅ Doc:
  - `docs/superpowers/specs/2026-06-04-v80-agent-eval-design.md` (本文件)
  - `docs/superpowers/plans/2026-06-04-v80-agent-eval-plan.md` (writing-plans 阶段出)
  - `docs/AI_MODEL_REGISTRY.md` (已存在,引用 fallback 链)

## 7. 风险 + 缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Fallback 链全失败(罕见) | 整体不可用 | FallbackError 含全部错误链,便于 debug;eval 报警 |
| 并行 tool 改变执行顺序(若有 side effect) | 行为变化 | 9 个 tool 都是 read-only / 计算,无 side effect |
| 反射重试循环(LLM 不改参数) | 多耗 1 轮 | 每 tool 最多重试 1 次 + max_tool_rounds 兜底 |
| Trace 数据大(200 步) | 内存 | max_steps=200 + JSON 前 200 字符预览 |
| Eval 评分主观(关键词匹配) | 假阳性 | 工具选择占 50% 权重,确保核心能力不被低估 |

## 8. 后续(v8.1+ roadmap,本次不做)

- v8.1:状态持久化(checkpoint/resume) + human-in-the-loop + 真实 token-by-token streaming
- v8.2:子 agent 委派(forecast-agent / risk-agent) + 跨 session 长期记忆
- v8.3:A/B testing 框架 + 模型 cost 仪表板
- v8.4:Chart 嵌入(LLM 返 chart spec → 前端 plot)
- v8.5:多模态(图片/PDF 输入)

## 9. 引用

- `backend/ai/chat_service.py` — v7.1 现有实现
- `backend/ai/llm_client.py` — litellm 包装
- `backend/ai/tool_executor.py` — 9 个 tool 执行
- `backend/ai/tool_registry.py` — tool schema 定义
- `docs/AI_MODEL_REGISTRY.md` — 35 个百炼模型清单
- `docs/superpowers/specs/2026-06-04-ai-agent-upgrade-design.md` — v7.1 spec(本次增强的前置)
