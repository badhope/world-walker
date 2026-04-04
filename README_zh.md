<div align="center">

# 📊 国家经济数据分析平台 (NEDAP)

[![版本](https://img.shields.io/badge/版本-3.0.0-blue.svg?style=for-the-badge)](https://github.com/badhope/national_stats/releases)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg?style=for-the-badge)](https://www.python.org/)
[![许可证](https://img.shields.io/badge/许可证-GPL%20v3-red.svg?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/badhope/national_stats?style=for-the-badge)](https://github.com/badhope/national_stats/stargazers)
[![Issues](https://img.shields.io/github/issues/badhope/national_stats?style=for-the-badge)](https://github.com/badhope/national_stats/issues)

**面向研究人员、企业和政府机构的综合经济数据评估与预测系统**

[🚀 快速开始](#-快速开始) · [📖 使用文档](#-使用文档) · [🎯 功能特性](#-功能特性) · [📊 在线演示](#-在线演示) · [🤝 参与贡献](#-参与贡献)

[English](README.md) · [简体中文](README_zh.md)

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#-功能特性)
- [快速开始](#-快速开始)
- [使用文档](#-使用文档)
  - [企业用户指南](#-企业用户指南)
  - [政府用户指南](#-政府用户指南)
  - [个人研究者指南](#-个人研究者指南)
- [系统架构](#-系统架构)
- [API 接口](#-api-接口)
- [经济学模型](#-经济学模型)
- [数据来源](#-数据来源)
- [发展规划](#-发展规划)
- [参与贡献](#-参与贡献)
- [许可证](#-许可证)
- [引用说明](#引用说明)

---

## 项目简介

**NEDAP**（国家经济数据分析平台）是一个开源平台，专为以下用户设计：

- 🏢 **企业用户**：金融分析、市场研究、投资决策支持
- 🏛️ **政府机构**：政策评估、经济监测、区域分析
- 🔬 **研究人员**：学术研究、教学演示、模型验证

### 为什么选择 NEDAP？

| 特性 | 说明 |
|------|------|
| **真实数据** | 直接对接中国政府官方数据源（统计局、央行、海关、财政部） |
| **14个指标** | 基于经济学公式自动推演关联经济指标 |
| **4个模型** | 经典经济学模型：菲利普斯曲线、奥肯定律、柯布-道格拉斯、索洛增长 |
| **一键启动** | 双击批处理文件即可启动前后端服务 |
| **API优先** | RESTful API 设计，便于与现有系统集成 |
| **跨平台** | 支持 Windows、macOS、Linux |

---

## 功能特性

### 📥 数据采集

- **官方数据源**：自动从国家统计局、人民银行、海关总署、财政部获取数据
- **实时更新**：支持定时数据同步
- **历史数据**：可获取数十年经济时间序列数据
- **数据验证**：自动质量检查和异常检测

### 📈 指标推演

| 指标 | 公式 | 说明 |
|------|------|------|
| 财政赤字 | 支出 - 收入 | 政府预算缺口 |
| 赤字率 | 赤字 / GDP × 100% | 国际警戒线：3% |
| 宏观税负 | 税收收入 / GDP × 100% | 税收负担水平 |
| 城乡差距 | 城镇收入 / 农村收入 | 收入分配不平等程度 |
| 消费率 | 消费支出 / 可支配收入 × 100% | 居民消费倾向 |
| 储蓄率 | 100% - 消费率 | 居民储蓄倾向 |
| 贸易顺差 | 出口 - 进口 | 对外贸易余额 |
| 贸易依存度 | (出口 + 进口) / GDP | 对外开放程度 |
| R&D强度 | 研发支出 / GDP × 100% | 创新投入水平 |
| 第一产业占比 | 第一产业增加值 / GDP × 100% | 产业结构 |
| 第二产业占比 | 第二产业增加值 / GDP × 100% | 工业化程度 |
| 第三产业占比 | 第三产业增加值 / GDP × 100% | 服务业发展水平 |
| M2效率 | GDP增速 / M2增速 | 货币使用效率 |
| 财政自给率 | 收入 / 支出 × 100% | 地方财政健康度 |

### 🔮 经济学模型

#### 1. 菲利普斯曲线
```
π = πₑ - β(u - u*)
```
描述失业率与通胀率之间的短期替代关系。

**应用场景**：央行政策分析、通胀预测

#### 2. 奥肯定律
```
(Y - Y*)/Y* = -β(u - u*)
```
描述 GDP 增速与失业率变化的关系。

**应用场景**：劳动力市场分析、增长预测

#### 3. 柯布-道格拉斯生产函数
```
Y = A × K^α × L^(1-α)
```
描述产出与资本、劳动投入的关系。

**应用场景**：生产率分析、增长核算

#### 4. 索洛增长模型
计算稳态人均资本和人均产出。

**应用场景**：长期增长分析、发展经济学

### 📊 数据可视化

- **交互式图表**：基于 Plotly 的交互式可视化
- **实时仪表盘**：经济指标实时监控面板
- **多格式导出**：支持 PNG、SVG、PDF、Excel 格式
- **自动报告**：自动生成分析报告

---

## 🚀 快速开始

### 环境要求

- Python 3.12 或更高版本
- pip 包管理器
- （可选）Git 用于克隆仓库

### 安装方式

#### 方式一：从 GitHub 克隆

```bash
git clone https://github.com/badhope/national_stats.git
cd national_stats
pip install -r requirements.txt
```

#### 方式二：下载压缩包

从 [GitHub Releases](https://github.com/badhope/national_stats/releases) 下载并解压。

### 启动服务

#### Windows 用户

双击 `启动.bat` 即可

#### macOS / Linux 用户

```bash
# 终端 1：启动后端
uvicorn backend.main:app --host 127.0.0.1 --port 8001

# 终端 2：启动前端
streamlit run app/streamlit_app.py
```

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:8501 | Streamlit 网页界面 |
| API 文档 | http://localhost:8001/docs | Swagger 交互式文档 |
| ReDoc | http://localhost:8001/redoc | 备选 API 文档 |

---

## 使用文档

### 🏢 企业用户指南

#### 典型应用场景

1. **市场研究**
   - 分析各地区 GDP 增长趋势
   - 监控 CPI/PPI 辅助定价决策
   - 追踪贸易数据规划供应链

2. **金融分析**
   - 计算财政指标评估信用风险
   - 使用经济模型进行宏观预测
   - 自动生成分析报告

3. **投资决策**
   - 监控 PMI 把握制造业景气度
   - 分析 M2 判断流动性环境
   - 追踪失业率预测消费前景

#### API 集成示例

```python
import requests

# API 地址
BASE_URL = "http://your-server:8001/api/v1"

# 获取指标数据
response = requests.get(f"{BASE_URL}/indicators/?category=gdp")
data = response.json()

# 计算推演指标
payload = {
    "input_indicators": {"revenue": 200000, "expenditure": 250000, "gdp": 1200000},
    "target_indicator": "deficit_rate",
    "method": "linear"
}
result = requests.post(f"{BASE_URL}/inference/calculate", json=payload)
print(result.json())
```

#### 企业级部署

详见 [docs/deployment/enterprise.md](docs/deployment/enterprise.md)：
- Docker 容器化部署
- Kubernetes 集群配置
- 负载均衡设置
- 安全加固指南

---

### 🏛️ 政府用户指南

#### 政策分析功能

1. **财政健康监测**
   - 自动计算赤字率、债务率
   - 与国际警戒线对比
   - 历史趋势分析

2. **区域经济比较**
   - 南北经济分化分析
   - 省级 GDP 对比
   - 城乡收入差距追踪

3. **经济预警**
   - 领先指标（PMI、M2增速）
   - 一致指标（GDP、工业增加值）
   - 滞后指标（失业率、CPI）

#### 数据安全

- 所有数据本地存储（不依赖云服务）
- 支持离线环境部署
- 完整的操作审计日志
- 基于角色的访问控制（RBAC）

#### 合规性

- 符合《数据安全法》要求
- 不收集个人数据
- 支持数据分类分级

---

### 🔬 个人研究者指南

#### 学术用途

1. **教学演示**
   - 经济模型交互式可视化
   - 分步公式计算过程
   - 真实数据案例

2. **科研支持**
   - 导出 CSV、Excel 格式数据
   - API 自动化数据采集
   - 可复现的分析流程

3. **模型验证**
   - 用真实数据检验经济理论
   - 参数敏感性分析
   - 蒙特卡洛模拟

#### 引用格式

```bibtex
@software{nedap2026,
  author = {NEDAP Contributors},
  title = {国家经济数据分析平台 (NEDAP)},
  year = {2026},
  version = {3.0.0},
  url = {https://github.com/badhope/national_stats}
}
```

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit 前端界面                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │ 仪表盘  │ │ 指标推演│ │ 数据管理│ │ 经济模型│ │ API文档 ││
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘│
└───────┼──────────┼──────────┼──────────┼──────────┼────────┘
        │          │          │          │          │
        └──────────┴──────────┴──────────┴──────────┘
                              │
                    ┌─────────┴─────────┐
                    │   FastAPI 后端    │
                    │  ┌─────────────┐  │
                    │  │  API 路由   │  │
                    │  └──────┬──────┘  │
                    │         │         │
                    │  ┌──────┴──────┐  │
                    │  │  业务逻辑   │  │
                    │  │ ┌─────────┐ │  │
                    │  │ │数据采集 │ │  │
                    │  │ │推演引擎 │ │  │
                    │  │ │经济模型 │ │  │
                    │  │ └─────────┘ │  │
                    │  └─────────────┘  │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │   SQLite / CSV    │
                    └───────────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Streamlit, Plotly, Pandas |
| 后端 | FastAPI, SQLAlchemy, Pydantic |
| 数据 | AKShare, Requests |
| 模型 | SciPy, Statsmodels, NumPy |
| 存储 | SQLite, CSV, Excel |

---

## 📡 API 接口

### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/v1/indicators/` | GET | 查询指标列表 |
| `/api/v1/indicators/{id}` | GET | 获取指标详情 |
| `/api/v1/indicators/` | POST | 创建指标记录 |
| `/api/v1/inference/available` | GET | 获取可推演指标列表 |
| `/api/v1/inference/calculate` | POST | 计算单个推演指标 |
| `/api/v1/inference/infer_all` | POST | 推演所有可计算指标 |
| `/api/v1/inference/models/phillips` | GET | 菲利普斯曲线模型 |
| `/api/v1/inference/models/okun` | GET | 奥肯定律模型 |
| `/api/v1/inference/models/cobb_douglas` | GET | 柯布-道格拉斯模型 |
| `/api/v1/inference/models/solow` | GET | 索洛增长模型 |
| `/api/v1/scrape/` | POST | 触发数据采集 |
| `/api/v1/scrape/status` | GET | 获取采集状态 |
| `/api/v1/scrape/sources` | GET | 获取数据源列表 |

### 请求示例

#### 计算赤字率

```bash
curl -X POST "http://localhost:8001/api/v1/inference/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "input_indicators": {
      "revenue": 200000,
      "expenditure": 250000,
      "gdp": 1200000
    },
    "target_indicator": "deficit_rate",
    "method": "linear"
  }'
```

#### 运行菲利普斯曲线模型

```bash
curl "http://localhost:8001/api/v1/inference/models/phillips?unemployment=5.5&natural_unemployment=5.0&expected_inflation=2.0&beta=0.5"
```

---

## 📊 数据来源

所有数据均来自中国政府官方公开数据门户：

| 来源 | 机构 | 指标 | 网址 |
|------|------|------|------|
| NBS | 国家统计局 | GDP、CPI、PPI、PMI、就业、人口 | [data.stats.gov.cn](https://data.stats.gov.cn) |
| PBC | 人民银行 | M0、M1、M2、利率、社融 | [pbc.gov.cn](http://www.pbc.gov.cn) |
| Customs | 海关总署 | 进出口、贸易顺差 | [customs.gov.cn](http://www.customs.gov.cn) |
| MOF | 财政部 | 财政收支、赤字 | [mof.gov.cn](http://www.mof.gov.cn) |

### 数据更新频率

| 指标 | 频率 | 典型滞后 |
|------|------|----------|
| GDP | 季度 | 15天 |
| CPI/PPI | 月度 | 10天 |
| PMI | 月度 | 1天 |
| M2 | 月度 | 10天 |
| 贸易数据 | 月度 | 7天 |
| 财政数据 | 月度 | 15天 |

---

## 🗺️ 发展规划

### 版本 3.1（计划中）

- [ ] **数据清洗模块**
  - 自动缺失值检测
  - 异常值识别与处理
  - 数据插值方法（线性、样条、机器学习）

- [ ] **增强可视化**
  - 时间序列分解图
  - 相关性热力图
  - 区域对比地图
  - 带筛选器的交互式仪表盘

- [ ] **模拟分析模块**
  - 蒙特卡洛风险分析
  - 情景分析（乐观、基准、悲观）
  - 政策影响模拟

### 版本 3.2（计划中）

- [ ] **扩展模型**
  - VAR 向量自回归
  - ARIMA 时间序列预测
  - 机器学习预测模型

- [ ] **报告生成**
  - 自动 PDF 报告
  - PowerPoint 演示文稿生成
  - 邮件报告定时发送

- [ ] **多语言支持**
  - 完整英文界面
  - 日文界面
  - 自定义语言包

### 版本 4.0（未来）

- [ ] **云端部署**
  - Docker 镜像
  - Kubernetes Helm Charts
  - AWS/Azure 部署指南

- [ ] **企业级功能**
  - 多租户支持
  - 单点登录集成
  - 高级权限控制

---

## 🤝 参与贡献

欢迎贡献代码！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/badhope/national_stats.git
cd national_stats

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8

# 运行测试
pytest tests/

# 格式化代码
black .
```

---

## 📄 许可证

本项目基于 **GNU General Public License v3.0** 许可证开源 - 详见 [LICENSE](LICENSE) 文件。

### 这意味着：

- ✅ 您可以自由使用、学习和修改本软件
- ✅ 您可以分发本软件
- ✅ 您可以分发修改后的版本
- ⚠️ 您必须保留原始许可证
- ⚠️ 您必须说明对源代码的修改
- ⚠️ 衍生作品必须同样采用 GPL-3.0 许可证

---

## ⚠️ 免责声明

本平台仅供**教育和研究目的**使用。分析结果不构成投资建议或政策建议。数据来源于官方公开渠道，如有侵权请联系删除。

---

## 📞 技术支持

- **问题反馈**：[GitHub Issues](https://github.com/badhope/national_stats/issues)
- **讨论交流**：[GitHub Discussions](https://github.com/badhope/national_stats/discussions)
- **邮件联系**：nedap@example.com

---

## 🙏 致谢

- [AKShare](https://github.com/akfamily/akshare) - 经济数据接口
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Web 框架
- [Streamlit](https://streamlit.io/) - 数据应用框架
- 所有贡献者和用户

---

<div align="center">

**由 NEDAP 团队用 ❤️ 构建**

[⬆ 返回顶部](#-国家经济数据分析平台-nedap)

</div>
