# 👨‍💻 开发者指南

本指南面向希望深入了解或贡献本项目的开发者。

## 目录

1. [开发环境](#开发环境)
2. [项目结构](#项目结构)
3. [代码规范](#代码规范)
4. [模块开发](#模块开发)
5. [测试指南](#测试指南)
6. [提交规范](#提交规范)

---

## 开发环境

### 1.1 推荐配置

- **Python**: 3.10+ (推荐 3.11)
- **IDE**: VS Code / PyCharm
- **版本控制**: Git

### 1.2 开发依赖

```bash
# 克隆项目
git clone https://github.com/your-project/national-stats-analyzer.git
cd national-stats-analyzer

# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy

# 设置预提交钩子
pre-commit install
```

### 1.3 开发工具配置

**VS Code 配置 (.vscode/settings.json):**

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "files.trimTrailingWhitespace": true
}
```

---

## 项目结构

### 2.1 模块职责

```
backend/
├── api/                    # API层
│   ├── main.py            # FastAPI应用
│   └── routes/            # 路由模块
│       ├── data.py        # 数据接口
│       ├── analysis.py    # 分析接口
│       └── inference.py   # 推演接口
│
├── data_collection/        # 数据采集
│   ├── base_collector.py  # 采集器基类
│   └── nbs_collector.py   # 国统局采集器
│
├── data_processing/        # 数据处理
│   └── cleaner.py         # 数据清洗器
│
├── analysis/               # 分析模块
│   ├── base_analyzer.py   # 分析器基类
│   ├── enterprise_analyzer.py  # 企业端分析
│   ├── government_analyzer.py  # 政府端分析
│   └── economic_models.py     # 经济模型
│
└── utils/                 # 工具模块
    └── visualizer.py     # 可视化工具

config/                     # 配置模块
├── settings.py            # 基础配置
├── analysis_config.py     # 分析配置
├── loader.py             # 配置加载器
├── regions/             # 地区配置
│   ├── template.py
│   └── shenzhen.py
└── industries/           # 产业配置
    ├── template.py
    └── semiconductor.py
```

### 2.2 依赖关系

```
main.py
  ↓
backend.api.main
  ↓
routes → analysis → data_collection
         ↓              ↓
    enterprise_     nbs_collector
    analyzer           ↓
         ↓         data_processing
    government         ↓
     analyzer       cleaner
```

---

## 代码规范

### 3.1 命名规范

**类名：** UpperCamelCase
```python
class EnterpriseAnalyzer: ...
class ShenzhenConfig: ...
```

**函数名：** snake_case
```python
def analyze_business_cost(): ...
def generate_report(): ...
```

**常量：** UPPER_SNAKE_CASE
```python
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

**变量：** snake_case
```python
total_cost = 1000
business_report = {}
```

### 3.2 文档字符串

**模块级文档：**
```python
"""
模块名称

模块功能说明，包括主要类和函数的概述。
"""

__author__ = "Your Name"
__version__ = "1.0.0"
```

**类文档：**
```python
class EnterpriseAnalyzer(BaseAnalyzer):
    """
    企业端分析器
    
    提供企业视角的区域产业经济分析功能，包括：
    - 营商成本分析
    - 供应链配套效率分析
    - 政策红利兑现分析
    
    Attributes:
        name: 分析器名称
        config: 配置对象
    """
```

**函数文档：**
```python
def analyze_business_cost(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析营商成本
    
    对输入数据进行分析，计算土地、人力、能源等成本指标。
    
    Args:
        data: 包含成本数据的字典
        
    Returns:
        成本分析结果字典，包含各维度评分和建议
        
    Raises:
        ValueError: 输入数据格式错误
        KeyError: 缺少必需字段
        
    Example:
        >>> data = {"land_price": 800, "salary": 15000}
        >>> result = analyzer.analyze_business_cost(data)
        >>> print(result["total_score"])
    """
```

### 3.3 类型标注

**函数参数和返回值：**
```python
from typing import Dict, List, Any, Optional, Union

def process_data(
    data: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """处理数据"""
    pass

def get_indicator(
    indicator_type: str
) -> Union[float, int, None]:
    """获取指标"""
    pass
```

### 3.4 代码格式化

使用 Black 进行格式化：

```bash
# 格式化所有Python文件
black .

# 检查格式（不修改）
black --check .

# 格式化单个文件
black backend/analysis/enterprise_analyzer.py
```

### 3.5 代码检查

使用 Flake8 进行检查：

```bash
# 检查所有文件
flake8 .

# 检查单个文件
flake8 backend/analysis/enterprise_analyzer.py

# 忽略特定规则
flake8 --ignore=E501,W503 .
```

---

## 模块开发

### 4.1 添加新的数据采集器

```python
# backend/data_collection/custom_collector.py
from backend.data_collection.base_collector import BaseCollector
from typing import List, Dict, Any

class CustomCollector(BaseCollector):
    """自定义数据采集器"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "custom"
    
    def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取数据"""
        # 实现采集逻辑
        pass
    
    def validate_data(self, data: List[Dict]) -> bool:
        """验证数据"""
        # 实现验证逻辑
        pass
```

### 4.2 添加新的分析器

```python
# backend/analysis/custom_analyzer.py
from backend.analysis.base_analyzer import BaseAnalyzer
from typing import Dict, Any

class CustomAnalyzer(BaseAnalyzer):
    """自定义分析器"""
    
    def __init__(self):
        super().__init__()
        self.name = "CustomAnalyzer"
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析"""
        # 实现分析逻辑
        pass
```

### 4.3 添加新的经济学模型

```python
# backend/analysis/custom_model.py
from typing import Dict, Any, Tuple

class CustomModel:
    """自定义经济模型"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def calculate(self, inputs: Dict[str, float]) -> Tuple[float, Dict[str, Any]]:
        """
        计算模型结果
        
        Args:
            inputs: 输入参数
            
        Returns:
            (结果值, 详细信息)
        """
        # 实现计算逻辑
        pass
    
    def validate_inputs(self, inputs: Dict[str, float]) -> bool:
        """验证输入参数"""
        pass
```

### 4.4 添加新的可视化图表

```python
# backend/utils/custom_charts.py
from backend.utils.visualizer import Visualizer

class CustomVisualizer(Visualizer):
    """自定义可视化"""
    
    def plot_custom_chart(self, data: Dict[str, Any]) -> str:
        """绘制自定义图表"""
        import plotly.graph_objects as go
        
        fig = go.Figure()
        # 实现图表逻辑
        
        return fig.to_html()
```

---

## 测试指南

### 5.1 测试结构

```
tests/
├── __init__.py
├── conftest.py           # pytest配置
├── test_collectors/     # 采集器测试
│   ├── __init__.py
│   └── test_nbs_collector.py
├── test_analyzers/      # 分析器测试
│   ├── __init__.py
│   ├── test_enterprise_analyzer.py
│   └── test_government_analyzer.py
├── test_models/         # 模型测试
│   ├── __init__.py
│   └── test_economic_models.py
└── test_api/            # API测试
    ├── __init__.py
    └── test_routes.py
```

### 5.2 编写测试

```python
# tests/test_analyzers/test_enterprise_analyzer.py
import pytest
from backend.analysis.enterprise_analyzer import EnterpriseAnalyzer

class TestEnterpriseAnalyzer:
    """企业分析器测试"""
    
    @pytest.fixture
    def analyzer(self):
        """测试夹具"""
        return EnterpriseAnalyzer()
    
    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return {
            "land_price": 800.0,
            "salary_level": 15000.0,
            "gdp": 35000.0
        }
    
    def test_analyzer_initialization(self, analyzer):
        """测试分析器初始化"""
        assert analyzer.name == "EnterpriseAnalyzer"
    
    def test_analyze_business_cost(self, analyzer, sample_data):
        """测试营商成本分析"""
        result = analyzer.analyze_business_cost(sample_data)
        
        assert "total_cost_score" in result
        assert isinstance(result["total_cost_score"], (int, float))
        assert 0 <= result["total_cost_score"] <= 100
    
    def test_generate_report(self, analyzer, sample_data):
        """测试报告生成"""
        report = analyzer.generate_comprehensive_report(sample_data)
        
        assert "overall_score" in report
        assert "region" in report
        assert "industry" in report
```

### 5.3 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_analyzers/test_enterprise_analyzer.py

# 带覆盖率报告
pytest tests/ --cov=backend --cov-report=html

# 详细输出
pytest tests/ -v --tb=short
```

---

## 提交规范

### 6.1 Git提交信息

遵循 Angular 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型：**
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例：**

```
feat(analyzer): 添加企业端供应链分析功能

- 新增供应链响应速度分析
- 新增本地化配套率计算
- 添加区位熵计算功能

Closes #123
```

### 6.2 Pull Request流程

1. **创建分支**
```bash
git checkout -b feature/supply-chain-analysis
```

2. **开发并提交**
```bash
git add .
git commit -m "feat(analyzer): 添加供应链分析功能"
```

3. **推送并创建PR**
```bash
git push origin feature/supply-chain-analysis
```

4. **代码审查**
- 确保所有测试通过
- 确保代码格式化
- 确保文档更新

### 6.3 版本发布

```bash
# 1. 更新版本号
git tag -a v4.0.0 -m "版本4.0.0发布"

# 2. 推送标签
git push origin v4.0.0

# 3. GitHub会自动创建Release
```

---

## 资源链接

- [Python编码规范](https://www.python.org/dev/peps/pep-0008/)
- [Google Python风格指南](https://google.github.io/styleguide/pyguide.html)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Plotly文档](https://plotly.com/python/)

---

## 联系我们

- 📧 技术支持：contact@example.com
- 🐛 问题反馈：https://github.com/your-project/national-stats-analyzer/issues
- 💬 讨论群：https://gitter.im/your-project

---

**感谢您的贡献！** 🙏
