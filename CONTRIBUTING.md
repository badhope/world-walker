# 贡献指南

感谢您考虑为国家经济数据分析平台 (NEDAP) 做出贡献！

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [问题报告](#问题报告)
- [功能请求](#功能请求)

---

## 行为准则

本项目采用贡献者公约作为行为准则。参与本项目即表示您同意遵守其条款。请阅读 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 了解详情。

### 我们的承诺

- 使用包容、友好的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

---

## 如何贡献

### 报告 Bug

如果您发现了 Bug，请创建一个 [Issue](https://github.com/badhope/national_stats/issues)，包含：

1. **清晰的标题**：简明扼要地描述问题
2. **复现步骤**：详细的步骤让他人能复现问题
3. **预期行为**：您期望发生什么
4. **实际行为**：实际发生了什么
5. **环境信息**：
   - 操作系统和版本
   - Python 版本
   - 项目版本
6. **截图**：如果适用，添加截图帮助解释问题
7. **日志**：相关的错误日志或堆栈跟踪

### 功能请求

如果您有功能建议，请创建一个 [Issue](https://github.com/badhope/national_stats/issues)，包含：

1. **清晰的标题**：简明扼要地描述功能
2. **详细描述**：功能的详细说明
3. **用例**：为什么需要这个功能
4. **替代方案**：您考虑过的替代方案
5. **优先级**：对您来说这个功能有多重要

### 提交代码

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 进行更改
4. 确保通过所有测试 (`pytest tests/`)
5. 确保代码符合规范 (`black .` 和 `flake8 .`)
6. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
7. 推送到分支 (`git push origin feature/AmazingFeature`)
8. 创建 Pull Request

---

## 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/badhope/national_stats.git
cd national_stats
```

### 2. 创建虚拟环境

```bash
# 使用 venv
python -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. 安装预提交钩子

```bash
pre-commit install
```

---

## 代码规范

### Python 代码风格

我们使用以下工具确保代码质量：

- **Black**：代码格式化
- **Flake8**：代码检查
- **isort**：导入排序
- **mypy**：类型检查

### 格式化代码

```bash
# 格式化所有 Python 文件
black .

# 排序导入
isort .

# 检查代码质量
flake8 .

# 类型检查
mypy backend/
```

### 代码风格指南

#### 命名约定

- **变量和函数**：使用 snake_case
  ```python
  def calculate_deficit_rate(revenue, expenditure):
      deficit = expenditure - revenue
      return deficit
  ```

- **类**：使用 PascalCase
  ```python
  class EconomicModel:
      pass
  ```

- **常量**：使用全大写 SNAKE_CASE
  ```python
  MAX_RETRIES = 3
  DEFAULT_TIMEOUT = 30
  ```

#### 文档字符串

使用 Google 风格的文档字符串：

```python
def calculate_indicator(data: pd.DataFrame, method: str = "linear") -> Dict[str, float]:
    """计算经济指标。
    
    Args:
        data: 包含经济数据的 DataFrame。
        method: 计算方法，可选 "linear" 或 "monte_carlo"。
    
    Returns:
        包含计算结果的字典，键为指标名，值为计算结果。
    
    Raises:
        ValueError: 如果数据为空或方法无效。
    
    Example:
        >>> df = pd.DataFrame({"gdp": [100, 200, 300]})
        >>> result = calculate_indicator(df, "linear")
    """
    pass
```

#### 类型注解

所有公共函数都应使用类型注解：

```python
from typing import List, Dict, Optional

def process_data(
    indicators: List[str],
    config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    pass
```

---

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (type)

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行的变动）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 范围 (scope)

- `api`: API 相关
- `models`: 经济模型
- `data`: 数据采集
- `ui`: 前端界面
- `docs`: 文档

### 示例

```
feat(api): 添加批量计算接口

- 支持一次请求计算多个指标
- 返回详细计算结果和置信区间

Closes #123
```

```
fix(data): 修复 CPI 数据采集失败的问题

AKShare 接口返回格式变更导致解析失败，
已更新解析逻辑适配新格式。

Fixes #456
```

---

## Pull Request 流程

### 提交前检查清单

- [ ] 代码通过所有测试
- [ ] 代码通过 Black 格式化
- [ ] 代码通过 Flake8 检查
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 提交消息符合规范

### PR 标题

PR 标题应遵循与提交消息相同的格式：

```
<type>(<scope>): <subject>
```

### PR 描述模板

```markdown
## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新
- [ ] 其他

## 描述
清晰描述您的变更...

## 相关 Issue
Closes #

## 测试
描述您如何测试这些变更...

## 截图
如果适用，添加截图...

## 检查清单
- [ ] 代码通过所有测试
- [ ] 添加了必要的文档
- [ ] 遵循代码规范
```

### 审查流程

1. 至少需要 1 位维护者批准
2. 所有 CI 检查必须通过
3. 解决所有审查意见
4. 合并前确保分支是最新的

---

## 问题报告

### Bug 报告模板

```markdown
## 描述
清晰简洁地描述 Bug...

## 复现步骤
1. 进入 '...'
2. 点击 '...'
3. 滚动到 '...'
4. 看到错误

## 预期行为
描述您期望发生什么...

## 实际行为
描述实际发生了什么...

## 截图
如果适用，添加截图...

## 环境
- 操作系统：[如 Windows 11]
- Python 版本：[如 3.12.0]
- 项目版本：[如 3.0.0]

## 其他信息
添加任何其他相关信息...
```

---

## 功能请求

### 功能请求模板

```markdown
## 功能描述
清晰简洁地描述您希望的功能...

## 问题背景
这个功能解决了什么问题...

## 建议方案
描述您建议的解决方案...

## 替代方案
描述您考虑过的替代方案...

## 附加信息
添加任何其他相关信息或截图...
```

---

## 获取帮助

如果您有任何问题，可以：

- 在 [GitHub Discussions](https://github.com/badhope/national_stats/discussions) 提问
- 加入我们的社区聊天群组
- 发送邮件至 nedap@example.com

---

## 许可证

通过贡献代码，您同意您的贡献将根据 GNU General Public License v3.0 许可证进行许可。

---

感谢您的贡献！🎉
