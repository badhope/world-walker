# ⚙️ 配置指南

本指南详细说明如何配置区域产业经济分析平台。

## 目录

1. [配置系统概述](#配置系统概述)
2. [基础配置](#基础配置)
3. [地区配置](#地区配置)
4. [产业配置](#产业配置)
5. [分析配置](#分析配置)
6. [环境变量](#环境变量)

---

## 配置系统概述

项目采用多层配置系统：

```
config/
├── settings.py           # 基础配置
├── analysis_config.py   # 分析参数配置
├── loader.py            # 配置加载器
├── regions/            # 地区配置
│   ├── template.py     # 地区配置模板
│   └── shenzhen.py     # 深圳配置
└── industries/         # 产业配置
    ├── template.py     # 产业配置模板
    └── semiconductor.py # 半导体配置
```

---

## 基础配置

编辑 `config/settings.py`：

```python
class Settings(BaseSettings):
    # 项目信息
    PROJECT_NAME: str = "区域产业经济分析平台"
    VERSION: str = "4.0.0"
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # 数据目录
    DATA_DIR: str = "./data"
    EXPORT_DIR: str = "./data/exports"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
```

---

## 地区配置

### 创建地区配置

在 `config/regions/` 下创建新地区配置文件：

```python
# config/regions/my_city.py
from config.regions.template import RegionConfig

class MyCityConfig(RegionConfig):
    name = "我的城市"
    code = "123456"
    province = "某省"
    
    indicator_weights = {
        "gdp": 0.25,
        "fiscal_revenue": 0.2,
        "industrial_output": 0.2,
        "employment": 0.15,
        "innovation": 0.2
    }
    
    economic_characteristics = [
        "科技创新中心",
        "先进制造业基地"
    ]
    
    benchmark_data = {
        "gdp_per_capita": 150000.0,
        "average_wage": 12000.0,
        "industrial_efficiency": 0.8
    }
```

### 配置加载

```python
from config import config_loader

# 获取所有可用地区
regions = config_loader.get_available_regions()
print(regions)  # ['深圳', '我的城市']

# 切换地区
config_loader.set_current_region("我的城市")

# 获取当前地区配置
region_config = config_loader.get_region_config()
```

---

## 产业配置

### 创建产业配置

在 `config/industries/` 下创建新产业配置文件：

```python
# config/industries/my_industry.py
from config.industries.template import IndustryConfig

class MyIndustryConfig(IndustryConfig):
    name = "我的产业"
    code = "X00"
    category = "制造业"
    industry_level = "secondary"
    
    chain_links = [
        "上游：原材料供应",
        "中游：生产制造",
        "下游：应用销售"
    ]
    
    key_indicators = {
        "output_value": {"name": "产值", "unit": "亿元"},
        "employment": {"name": "就业人数", "unit": "万人"}
    }
    
    characteristics = [
        "技术密集型",
        "资本密集型"
    ]
    
    market_data = {
        "market_size": 5000.0,
        "growth_rate": 10.0
    }
```

### 配置加载

```python
from config import config_loader

# 获取所有可用产业
industries = config_loader.get_available_industries()
print(industries)  # ['半导体', '我的产业']

# 切换产业
config_loader.set_current_industry("我的产业")

# 获取当前产业配置
industry_config = config_loader.get_industry_config()
```

---

## 分析配置

编辑 `config/analysis_config.py`：

```python
class AnalysisConfig:
    # 默认分析参数
    DEFAULT_YEAR = 2025
    DEFAULT_REGION = "深圳"
    DEFAULT_INDUSTRY = "半导体"
    
    # 评分权重
    SCORE_WEIGHTS = {
        "business_cost": {
            "land_cost": 0.3,
            "labor_cost": 0.4,
            "energy_cost": 0.2,
            "financing_cost": 0.1
        }
    }
    
    # 阈值配置
    THRESHOLDS = {
        "cost_high": 80.0,
        "cost_medium": 60.0,
        "supply_chain_good": 75.0
    }
    
    # 数据采集指标
    DATA_COLLECTION = {
        "default_indicators": [
            "gdp",
            "cpi",
            "pmi",
            "fiscal_revenue",
            "industrial_output"
        ],
        "years_range": [2020, 2021, 2022, 2023, 2024, 2025]
    }
    
    # 可视化配置
    VISUALIZATION = {
        "theme": "plotly_white",
        "default_width": 1200,
        "default_height": 600,
        "color_palette": [
            "#667eea", "#764ba2", "#f093fb"
        ]
    }
```

---

## 环境变量

使用 `.env` 文件配置：

```bash
# .env 文件示例

# 项目配置
PROJECT_NAME=区域产业经济分析平台
VERSION=4.0.0

# API配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# 日志配置
LOG_LEVEL=INFO

# 分析参数
DEFAULT_YEAR=2025
DEFAULT_REGION=深圳
DEFAULT_INDUSTRY=半导体

# 数据目录
DATA_DIR=./data
EXPORT_DIR=./data/exports

# 安全配置
SECRET_KEY=your-secret-key-here
```

### 从环境变量读取配置

```python
from config import settings

# 读取配置
print(settings.PROJECT_NAME)
print(settings.API_PORT)
print(settings.DEFAULT_REGION)
```

---

## 最佳实践

### 1. 使用环境变量

生产环境应使用环境变量：

```bash
export DATABASE_URL="postgresql://user:pass@localhost/db"
export SECRET_KEY="production-secret-key"
```

### 2. 配置分层

开发和生产配置分离：

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... 基础配置
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

### 3. 配置验证

使用Pydantic验证配置：

```python
from pydantic import validator

class AnalysisConfig:
    @validator('DEFAULT_YEAR')
    def validate_year(cls, v):
        if v < 2000 or v > 2100:
            raise ValueError('年份超出合理范围')
        return v
```

---

## 故障排除

### 配置不生效？

```bash
# 1. 检查.env文件存在
ls -la .env

# 2. 检查环境变量
echo $PROJECT_NAME

# 3. 重新加载配置
python main.py --mode check
```

### 配置加载失败？

```python
# 检查配置加载器
from config import config_loader

# 重新初始化
config_loader._initialized = False
config_loader.__init__()
```

---

## 更多信息

- 📖 查看 [USAGE_GUIDE.md](./USAGE_GUIDE.md) - 使用指南
- 📊 查看 [EXAMPLE_ANALYSIS.md](./EXAMPLE_ANALYSIS.md) - 示例分析
- 🐛 问题反馈：https://github.com/your-org/regional-economic-analysis/issues
