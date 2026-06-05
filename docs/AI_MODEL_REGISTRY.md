# AI 模型注册表

> 验证时间: 2026-06-04
> 平台: 阿里云百炼 (DashScope OpenAI 兼容 API)
> Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
> 验证方法: 直接 chat completions + in-process 跑 `chat_stream_with_trace`

## 1. 可用模型 — 35 个

按"对 v7.1 agent 的适配度"分组。**全功能** = 能调 tool、返回 SSE 完整事件链;**窄任务** = 能响应但专精单一任务(数学/翻译/视觉),不调通用 tool。

### 1.1 全功能推荐 (默认 + 备份) — 18 个

| 优先级 | 模型 | 类别 | 备注 |
|--------|------|------|------|
| **默认** | `qwen-max` | 通用 | 当前生产默认,老模型 + free tier 稳定 |
| 1 | `qwen-long` | 长文本 | 长上下文场景 |
| 2 | `qwen-coder-turbo` | 代码 | 代码生成/分析 |
| 3 | `qwen-coder-plus-1106` | 代码 | coder plus 旧版 |
| 4 | `qwen-flash` | 通用 | qwen 轻量,快 |
| 5 | `qwen-max-longcontext` | 长文本 | max 长文本版 |
| 6 | `qwen3-30b-a3b-instruct-2507` | 通用 | qwen3 MoE 30B |
| 7 | `qwen3-235b-a22b-instruct-2507` | 通用 | qwen3 MoE 235B |
| 8 | `qwen3-235b-a22b` | 通用 | qwen3 235B (thinking 默认开) |
| 9 | `qwen3-235b-a22b-thinking-2507` | 推理 | qwen3 thinking 模式 |
| 10 | `qwen3-coder-flash` | 代码 | qwen3 coder 轻量 |
| 11 | `qwen3-coder-480b-a35b-instruct` | 代码 | qwen3 coder 大模型 |
| 12 | `qwen3-coder-plus-2025-09-23` | 代码 | qwen3 coder plus |
| 13 | `deepseek-v3` | 通用 | DeepSeek V3 |
| 14 | `deepseek-v3.1` | 通用 | DeepSeek V3.1 |
| 15 | `deepseek-v3.2` | 通用 | DeepSeek V3.2 |
| 16 | `deepseek-v4-flash` | 通用 | DeepSeek V4 轻量 |
| 17 | `deepseek-v4-pro` | 通用 | DeepSeek V4 旗舰 |
| 18 | `deepseek-r1` | 推理 | DeepSeek R1 |
| 19 | `glm-4.7` | 通用 | 智谱 GLM-4.7 |
| 20 | `glm-5.1` | 通用 | 智谱 GLM-5.1 |
| 21 | `kimi-k2.5` | 通用 | 月之暗面 Kimi K2.5 |
| 22 | `kimi-k2.6` | 通用 | 月之暗面 Kimi K2.6 |
| 23 | `kimi-k2-thinking` | 推理 | Kimi K2 thinking |
| 24 | `qwen-omni-turbo` | 多模态 | qwen omni |
| 25 | `qvq-plus` | 视觉推理 | 视觉问答 |

### 1.2 窄任务(能响应但不调通用 tool) — 10 个

| 模型 | 类别 | 用途 |
|------|------|------|
| `qwen-math-turbo` | 数学 | 数学计算/证明 |
| `qwen-math-plus` | 数学 | 数学 plus |
| `qwen-math-plus-0919` | 数学 | 数学 plus 旧版 |
| `qwen-mt-lite` | 翻译 | 轻量翻译 |
| `qwen-mt-turbo` | 翻译 | 翻译 turbo |
| `qwen-mt-plus` | 翻译 | 翻译 plus |
| `qwen-mt-flash` | 翻译 | 翻译 flash |
| `qwen-vl-plus` | 视觉 | 视觉理解 plus |
| `qwen-vl-max` | 视觉 | 视觉理解 max |
| `qvq-plus` | 视觉推理 | (也列在 1.1,但 tool 触发率低) |

## 2. 不可用 — 30+ 个

### 2.1 free tier 耗尽 (6)

- `qwen-turbo`, `qwen-plus`, `qwen-coder-plus`, `qwen3-coder-plus`, `qwen3-coder-next`, `glm-5`
- 错误: `The free tier of the model has been exhausted.`

### 2.2 模型下架 / not_found (18)

- qwen-1.8b-chat, qwen-1.8b-longcontext-chat, qwen-7b-chat, qwen-14b-chat, qwen-72b-chat
- qwen1.5-0.5b/1.8b/7b/14b/32b/72b/110b-chat
- qwen2-0.5b/1.5b/7b/57b-a14b-instruct
- qwen-turbo-0919, qwen-max-0107
- 错误: `The model <name> does not exist.`

### 2.3 权限/付费 (10+)

- qwen2.5-0.5b-instruct, qwen2.5-1.5b-instruct, qwen-turbo-2024-11-01
- qwen3-8b, qwen3-14b, qwen3-32b, qwen3-30b-a3b (thinking 模式需 enable_thinking=false)
- qwen-vl-ocr, qwen3-asr-flash-realtime
- qvq-max, ZHIPU/GLM-5, ZHIPU/GLM-5.1
- 错误: `Access denied` / `product is not activated` / `parameter.enable_thinking must be set`

## 3. 配置入口

- 代码: `backend/ai/config.py::load_config()`
- 环境变量: `LLM_OPENAI_MODEL` (默认 `qwen-max`),`LLM_OPENAI_API_KEY`,`LLM_OPENAI_BASE_URL`
- 运行时切换:`POST /api/v1/ai/config { "model": "<name>" }`(若路由暴露)

## 4. 验证脚本

- `tests/backend/test_ai_*.py` — 76/76 pass,全功能 SSE 流式 + tool call + chip 链接
- 临时诊断脚本(`/tmp/rea/test_bailian_models.py`):
  - 列出 211 个阿里模型
  - 自动分类 ok / free_exhausted / not_found / error
  - 从最老 qwen-1.8b/7b/14b/72b 开始,直到找到可用的

## 5. 故障切换策略

```
生产默认: qwen-max
↓ 失败/超时
降级 1: qwen-long  (长上下文场景优先)
↓ 失败/超时
降级 2: qwen-coder-turbo  (代码/分析场景优先)
↓ 失败/超时
降级 3: deepseek-v3  (第三方兜底)
↓ 失败/超时
降级 4: kimi-k2.5  (第三个第三方)
```

由 v7.2 (前端 route + chart 嵌入) 之后,在 `backend/ai/llm_client.py` 加 fallback 链。
