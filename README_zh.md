# 国家经济数据分析平台 (NEDAP)

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue" alt="版本">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-GPL--3.0-orange" alt="许可证">
  <img src="https://img.shields.io/badge/FastAPI-0.109-green" alt="FastAPI">
  <img src="https://img.shields.io/badge/Streamlit-1.28-red" alt="Streamlit">
</p>

> 为研究人员、经济学家和政策制定者打造的综合经济数据评估与预测系统。

<p align="center">
  <a href="#-功能特点">功能特点</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-系统架构">系统架构</a> •
  <a href="#-api接口">API接口</a> •
  <a href="#-贡献指南">贡献指南</a> •
  <a href="#-许可证">许可证</a>
</p>

---

## 🌐 Language | 语言

> [English](README.md) | 中文

---

## 📊 功能特点

### 核心功能

| 功能 | 说明 |
|------|------|
| 📈 **指标推演** | 输入经济指标，自动推算相关联指标（如财政赤字率、债务率） |
| 🔮 **教学模型** | 预设经济模型（菲利普斯曲线、奥肯定律、柯布-道格拉斯）用于教学 |
| 🗺️ **区域分析** | 南北方、东西部经济对比及收敛性检验 |
| 📥 **数据采集** | 从官方数据源自动化爬取（财政部、统计局、海关、央行） |
| 📊 **可视化** | 基于Plotly的交互式图表和仪表盘 |

### 数据来源

| 来源 | 代码 | 说明 |
|------|------|------|
| 财政部 | `mof` | 财政收入、支出、债务数据 |
| 国家统计局 | `nbs` | GDP、CPI、就业、人口 |
| 海关总署 | `customs` | 进出口贸易数据 |
| 中国人民银行 | `pbc` | 货币供应量、利率 |

### 推演指标

- **财政**: `fiscal_deficit`, `deficit_rate`, `debt_ratio`, `tax_revenue`
- **区域**: `gini_coefficient`, `theil_index`, `convergence_coefficient`
- **收入**: `urban_rural_ratio`, `gini_urban`, `labor_share`
- **产业**: `industrial_upgrading_index`, `hoffmann_coefficient`
- **创新**: `rd_intensity`, `patent_output`, `innovation_efficiency`

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Git

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/your-repo/national_stats.git
cd national_stats

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行程序

```bash
# 启动后端 (终端 1)
uvicorn backend.main:app --reload --port 8001

# 启动前端 (终端 2)
streamlit run app/streamlit_app.py
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:8501 |
| API文档 | http://localhost:8001/docs |
| ReDoc | http://localhost:8001/redoc |
| 健康检查 | http://localhost:8001/health |

---

## 🏗️ 系统架构

```
national_stats/
├── app/                        # Streamlit 前端
│   ├── streamlit_app.py        # 主应用程序
│   └── i18n.py                 # 国际化支持
│
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 应用程序入口
│   ├── core/
│   │   └── config.py           # 配置管理
│   ├── models/
│   │   ├── database.py         # SQLAlchemy 模型
│   │   └── schemas.py         # Pydantic 模型
│   ├── api/routes/
│   │   ├── data.py             # 数据管理
│   │   ├── inference.py        # 指标推演
│   │   └── scrape.py          # 数据爬取
│   └── services/
│       └── scraper/            # 爬虫实现
│
├── core/                       # 核心分析模型
│   └── models/
│       ├── fiscal.py          # 财政分析
│       ├── regional.py        # 区域分析
│       ├── income.py          # 收入分配
│       ├── industrial.py      # 产业结构
│       └── innovation.py     # 创新指标
│
├── tests/                      # 测试套件
├── docs/                       # 文档
└── scripts/                   # 工具脚本
```

---

## 📡 API接口

### 主要端点

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/v1/indicators/` | 获取指标列表 |
| `POST` | `/api/v1/inference/calculate` | 计算指标推演 |
| `GET` | `/api/v1/inference/available_indicators` | 获取可用指标 |
| `POST` | `/api/v1/scrape/` | 从数据源爬取 |
| `GET` | `/api/v1/scrape/status` | 获取爬虫状态 |
| `GET` | `/health` | 健康检查 |

### 请求示例

```bash
curl -X POST http://localhost:8001/api/v1/inference/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "input_indicators": {
      "expenditure": 250000,
      "revenue": 200000,
      "gdp": 1200000
    },
    "target_indicator": "deficit_rate",
    "method": "linear"
  }'
```

### 响应示例

```json
{
  "predicted_value": 4.1667,
  "predicted_unit": "%",
  "confidence_interval": [3.9583, 4.375],
  "method_used": "linear",
  "input_indicators": {
    "expenditure": 250000.0,
    "revenue": 200000.0,
    "gdp": 1200000.0
  },
  "target_indicator": "deficit_rate"
}
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行带覆盖率
pytest tests/ --cov=backend --cov-report=html

# 运行指定测试文件
pytest tests/test_fiscal.py -v
```

---

## 🔧 配置

可选环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///./national_stats.db` | 数据库连接 |
| `API_PORT` | `8001` | 后端端口 |
| `CORS_ORIGINS` | `*` | CORS允许来源 |

---

## 👥 贡献指南

欢迎贡献！请在提交PR前阅读我们的 [贡献指南](CONTRIBUTING.md)。

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# 运行代码格式化
black backend/ app/ tests/

# 运行测试
pytest tests/ -v
```

---

## 📄 许可证

本项目采用 GNU General Public License v3.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- 官方数据来源：财政部、国家统计局、海关总署、中国人民银行
- 技术栈：FastAPI、Streamlit、Plotly、SQLAlchemy、Pandas、NumPy

---

## 📬 联系方式

- **问题追踪**: https://github.com/your-repo/national_stats/issues
- **电子邮件**: contact@example.com

---

<p align="center">
  <strong>国家经济数据分析平台</strong><br>
  <sub>为经济学家、研究人员和政策制定者打造</sub>
</p>
