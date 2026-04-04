# 国家经济数据分析平台 (NEDAP)

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/badhope/national_stats)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-red.svg)](LICENSE)

**国家经济数据综合分析平台** — 经济数据采集、指标推演、模型验证的一站式解决方案。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| **数据采集** | 自动从国家统计局、央行、海关、财政部获取真实数据 |
| **指标推演** | 基于经济学公式自动推算关联指标（赤字率、债务率、消费率等） |
| **经济模型** | 菲利普斯曲线、奥肯定律、柯布-道格拉斯、索洛增长模型 |
| **可视化** | 交互式图表、仪表盘、数据导出 |

## 🚀 快速开始

### Windows 用户

1. 确保已安装 Python 3.12+
2. 双击 `启动.bat` 即可

### 手动启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
uvicorn backend.main:app --host 127.0.0.1 --port 8001

# 启动前端（新终端）
streamlit run app/streamlit_app.py
```

### 访问地址

- 前端界面: http://localhost:8501
- API 文档: http://localhost:8001/docs

## 📊 可推演指标

| 指标 | 公式 | 说明 |
|------|------|------|
| 财政赤字 | 支出 - 收入 | 财政收支缺口 |
| 赤字率 | 赤字 / GDP × 100% | 国际警戒线 3% |
| 宏观税负 | 税收 / GDP × 100% | 税收负担水平 |
| 城乡差距 | 城镇收入 / 农村收入 | 收入分配差距 |
| 消费率 | 消费 / 收入 × 100% | 居民消费倾向 |
| 贸易顺差 | 出口 - 进口 | 对外贸易余额 |
| 贸易依存度 | (出口+进口) / GDP | 对外开放程度 |

## 🔮 经济模型

### 菲利普斯曲线
```
π = πₑ - β(u - u*)
```
描述失业率与通胀率的短期替代关系。

### 奥肯定律
```
(Y - Y*)/Y* = -β(u - u*)
```
描述 GDP 增速与失业率变化的关系。

### 柯布-道格拉斯生产函数
```
Y = A × K^α × L^(1-α)
```
描述产出与资本、劳动投入的关系。

### 索洛增长模型
计算稳态人均资本和人均产出。

## 📁 项目结构

```
national_stats/
├── backend/           # FastAPI 后端
│   ├── api/routes/    # API 路由
│   ├── core/          # 配置与数据库
│   ├── models/        # 数据模型
│   └── services/      # 业务逻辑
├── app/               # Streamlit 前端
├── data/              # 数据存储
├── 启动.bat           # 一键启动
└── requirements.txt   # 依赖列表
```

## 🛠️ 技术栈

- **后端**: FastAPI + SQLAlchemy + AKShare
- **前端**: Streamlit + Plotly
- **数据**: 国家统计局 / 央行 / 海关 / 财政部
- **建模**: Statsmodels + SciPy

## 📝 数据来源

所有数据均来自中国政府官方公开数据源：

- [国家统计局](https://data.stats.gov.cn)
- [人民银行](http://www.pbc.gov.cn)
- [海关总署](http://www.customs.gov.cn)
- [财政部](http://www.mof.gov.cn)

## 📊 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/indicators/` | GET | 查询指标列表 |
| `/api/v1/inference/calculate` | POST | 指标推演计算 |
| `/api/v1/inference/available` | GET | 获取可推演指标 |
| `/api/v1/inference/models/phillips` | GET | 菲利普斯曲线 |
| `/api/v1/inference/models/okun` | GET | 奥肯定律 |
| `/api/v1/inference/models/cobb_douglas` | GET | 柯布-道格拉斯 |
| `/api/v1/scrape/` | POST | 数据采集 |
| `/health` | GET | 健康检查 |

## ⚠️ 免责声明

本平台仅供学习研究使用，分析结果不构成任何投资建议。数据来源于官方公开渠道，如有侵权请联系删除。

## 📄 许可证

[GNU General Public License v3.0](LICENSE)
