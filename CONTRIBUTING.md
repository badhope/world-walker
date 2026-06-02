# 贡献指南

感谢您对 **Regional Economic Analysis** 项目的关注！我们欢迎任何形式的贡献（功能、缺陷修复、文档、测试、翻译）。

## 行为准则

请阅读并遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。参与本项目即表示您同意其中条款。

## 如何贡献

### 报告 Bug

1. 在 [Issues](https://github.com/your-org/regional-economic-analysis/issues) 中搜索，确认问题未被报告
2. 使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.md) 创建新 Issue
3. 附上：
   - 操作系统与 Python 版本
   - 复现步骤
   - 期望行为 vs 实际行为
   - 截图 / 日志 / 堆栈追踪

### 提出新功能

使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.md)，说明：
- 解决的痛点 / 业务价值
- 期望的 API / UI 形态
- 备选方案

### 提交代码（Pull Request）

1. Fork 仓库 → 创建分支：`git checkout -b feat/your-feature`
2. 提交前自检：
   ```bash
   pip install -r requirements.txt
   ruff check .
   python -m pytest tests/ -v
   python full_diagnose.py
   ```
3. 保持单一职责：每个 PR 只解决一个问题
4. 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：
   - `feat: 新增 XX 功能`
   - `fix: 修复 XX 缺陷`
   - `docs: 更新 XX 文档`
   - `refactor: 重构 XX 模块`
   - `test: 增加 XX 测试`
   - `chore: 升级 XX 依赖`
5. 推送到 fork → 提交 PR → 等待 CI + Review

### 改进文档

- 错别字、示例代码、API 描述都可直接 PR
- 重大修改请先在 Issue 中讨论

## 开发环境

```bash
# 1. 克隆
git clone https://github.com/your-org/regional-economic-analysis.git
cd regional-economic-analysis

# 2. 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动后端
uvicorn backend.api.main:app --reload --port 8000

# 5. 启动前端 (新终端)
cd frontend && python3 -m http.server 8080
```

## 代码规范

- **Python**: PEP 8 + [Ruff](https://github.com/astral-sh/ruff)（`ruff check .`）
- **命名**: 模块/函数 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE_CASE`
- **类型注解**: 公共函数必须有类型提示
- **注释**: 中文 / 英文均可，但保持一致；解释 *为什么* 而非 *做什么*
- **测试**: 新功能必须附带单元测试

## 项目结构

```
backend/api/        # FastAPI 路由
backend/core/       # 业务核心逻辑
backend/data/       # 数据访问
backend/analysis/   # 分析器实现
frontend/           # 纯 HTML 单页应用
config/             # 全局配置
docs/               # 详细文档
tests/backend/      # 单元测试
```

## 许可证

提交代码即表示您同意以 [GPL-3.0-or-later License](LICENSE) 授权。
