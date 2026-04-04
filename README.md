<div align="center">

# 📊 National Economic Data Analysis Platform (NEDAP)

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg?style=for-the-badge)](https://github.com/badhope/national_stats/releases)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-red.svg?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/badhope/national_stats?style=for-the-badge)](https://github.com/badhope/national_stats/stargazers)
[![Issues](https://img.shields.io/github/issues/badhope/national_stats?style=for-the-badge)](https://github.com/badhope/national_stats/issues)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.xxxxx-blue.svg?style=for-the-badge)](https://doi.org/)

**A comprehensive economic data assessment and prediction system for researchers, enterprises, and government agencies.**

[🚀 Quick Start](#-quick-start) · [📖 Documentation](#-documentation) · [🎯 Features](#-features) · [📊 Demo](#-demo) · [🤝 Contributing](#-contributing)

[English](README.md) · [简体中文](README_zh.md)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#-quick-start)
- [Documentation](#-documentation)
  - [For Enterprise Users](#-for-enterprise-users)
  - [For Government Users](#-for-government-users)
  - [For Individual Researchers](#-for-individual-researchers)
- [Architecture](#-architecture)
- [API Reference](#-api-reference)
- [Economic Models](#-economic-models)
- [Data Sources](#-data-sources)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#license)
- [Citation](#citation)

---

## Overview

**NEDAP** (National Economic Data Analysis Platform) is an open-source platform designed for:

- 🏢 **Enterprise Users**: Financial analysis, market research, investment decisions
- 🏛️ **Government Agencies**: Policy evaluation, economic monitoring, regional analysis
- 🔬 **Researchers**: Academic research, teaching demonstrations, model validation

### Why NEDAP?

| Feature | Description |
|---------|-------------|
| **Real Data** | Direct integration with official Chinese government data sources (NBS, PBC, Customs, MOF) |
| **14 Indicators** | Automatic inference of economic indicators using economic formulas |
| **4 Models** | Classic economic models: Phillips Curve, Okun's Law, Cobb-Douglas, Solow Growth |
| **One-Click Start** | Single batch file launches both backend and frontend |
| **API-First** | RESTful API design for easy integration with existing systems |
| **Cross-Platform** | Works on Windows, macOS, and Linux |

---

## Features

### 📥 Data Collection

- **Official Sources**: Automatic fetching from National Bureau of Statistics, People's Bank of China, Customs, Ministry of Finance
- **Real-time Updates**: Support scheduled data synchronization
- **Historical Data**: Access decades of economic time series
- **Data Validation**: Automatic quality checks and anomaly detection

### 📈 Indicator Inference

| Indicator | Formula | Description |
|-----------|---------|-------------|
| Fiscal Deficit | Expenditure - Revenue | Government budget gap |
| Deficit Rate | Deficit / GDP × 100% | International warning line: 3% |
| Macro Tax Burden | Tax Revenue / GDP × 100% | Tax burden level |
| Urban-Rural Gap | Urban Income / Rural Income | Income distribution inequality |
| Consumption Rate | Consumption / Income × 100% | Household consumption propensity |
| Savings Rate | 100% - Consumption Rate | Household savings propensity |
| Trade Balance | Export - Import | Foreign trade surplus/deficit |
| Trade Dependence | (Export + Import) / GDP | Openness to trade |
| R&D Intensity | R&D Expenditure / GDP × 100% | Innovation investment |
| Primary Industry Ratio | Primary Industry / GDP × 100% | Economic structure |
| Secondary Industry Ratio | Secondary Industry / GDP × 100% | Industrial structure |
| Tertiary Industry Ratio | Tertiary Industry / GDP × 100% | Service sector share |
| M2 Efficiency | GDP Growth / M2 Growth | Monetary efficiency |
| Fiscal Self-Sufficiency | Revenue / Expenditure × 100% | Local fiscal health |

### 🔮 Economic Models

#### 1. Phillips Curve
```
π = πₑ - β(u - u*)
```
Describes the short-run trade-off between unemployment and inflation.

**Use Case**: Central bank policy analysis, inflation forecasting

#### 2. Okun's Law
```
(Y - Y*)/Y* = -β(u - u*)
```
Relates GDP growth to changes in unemployment rate.

**Use Case**: Labor market analysis, growth forecasting

#### 3. Cobb-Douglas Production Function
```
Y = A × K^α × L^(1-α)
```
Models the relationship between output and inputs (capital, labor).

**Use Case**: Productivity analysis, growth accounting

#### 4. Solow Growth Model
Calculates steady-state capital per worker and output per worker.

**Use Case**: Long-run growth analysis, development economics

### 📊 Visualization

- **Interactive Charts**: Plotly-powered interactive visualizations
- **Dashboard**: Real-time economic indicators dashboard
- **Export**: Support PNG, SVG, PDF, Excel formats
- **Custom Reports**: Generate automated analysis reports

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- pip package manager
- (Optional) Git for cloning the repository

### Installation

#### Option 1: Clone from GitHub

```bash
git clone https://github.com/badhope/national_stats.git
cd national_stats
pip install -r requirements.txt
```

#### Option 2: Download ZIP

Download from [GitHub Releases](https://github.com/badhope/national_stats/releases) and extract.

### Launch

#### Windows

Double-click `启动.bat` (or `start.bat`)

#### macOS / Linux

```bash
# Terminal 1: Start backend
uvicorn backend.main:app --host 127.0.0.1 --port 8001

# Terminal 2: Start frontend
streamlit run app/streamlit_app.py
```

### Access

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:8501 | Streamlit web interface |
| API Docs | http://localhost:8001/docs | Swagger UI |
| ReDoc | http://localhost:8001/redoc | Alternative API documentation |

---

## Documentation

### 🏢 For Enterprise Users

#### Use Cases

1. **Market Research**
   - Analyze GDP growth trends by region
   - Monitor CPI/PPI for pricing decisions
   - Track trade data for supply chain planning

2. **Financial Analysis**
   - Calculate fiscal indicators for credit risk assessment
   - Use economic models for macro forecasting
   - Generate automated reports for stakeholders

3. **Investment Decisions**
   - Monitor PMI for manufacturing sector health
   - Analyze money supply (M2) for liquidity conditions
   - Track unemployment for consumer sector outlook

#### Integration Guide

```python
import requests

# API endpoint
BASE_URL = "http://your-server:8001/api/v1"

# Get indicators
response = requests.get(f"{BASE_URL}/indicators/?category=gdp")
data = response.json()

# Calculate inference
payload = {
    "input_indicators": {"revenue": 200000, "expenditure": 250000, "gdp": 1200000},
    "target_indicator": "deficit_rate",
    "method": "linear"
}
result = requests.post(f"{BASE_URL}/inference/calculate", json=payload)
print(result.json())
```

#### Enterprise Deployment

See [docs/deployment/enterprise.md](docs/deployment/enterprise.md) for:
- Docker deployment
- Kubernetes configuration
- Load balancing setup
- Security hardening

---

### 🏛️ For Government Users

#### Policy Analysis Features

1. **Fiscal Health Monitoring**
   - Automatic calculation of deficit rate, debt ratio
   - Comparison with international warning thresholds
   - Historical trend analysis

2. **Regional Economic Comparison**
   - North-South economic divergence analysis
   - Provincial GDP comparison
   - Urban-rural income gap tracking

3. **Economic Early Warning**
   - Leading indicators (PMI, M2 growth)
   - Coincident indicators (GDP, industrial output)
   - Lagging indicators (unemployment, CPI)

#### Data Security

- All data stored locally (no cloud dependency)
- Support for air-gapped deployment
- Audit logging for all data operations
- Role-based access control (RBAC)

#### Compliance

- GDPR compliant (no personal data collected)
- Chinese Data Security Law compliant
- Supports data classification and labeling

---

### 🔬 For Individual Researchers

#### Academic Use

1. **Teaching Demonstrations**
   - Interactive economic model visualization
   - Step-by-step formula calculations
   - Real-world data examples

2. **Research Support**
   - Export data in CSV, Excel formats
   - API for automated data collection
   - Reproducible analysis workflows

3. **Model Validation**
   - Test economic theories against real data
   - Parameter sensitivity analysis
   - Monte Carlo simulation support

#### Citation

```bibtex
@software{nedap2026,
  author = {NEDAP Contributors},
  title = {National Economic Data Analysis Platform (NEDAP)},
  year = {2026},
  version = {3.0.0},
  url = {https://github.com/badhope/national_stats}
}
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit Frontend                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │Dashboard│ │Inference│ │  Data   │ │ Models  │ │  API    ││
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘│
└───────┼──────────┼──────────┼──────────┼──────────┼────────┘
        │          │          │          │          │
        └──────────┴──────────┴──────────┴──────────┘
                              │
                    ┌─────────┴─────────┐
                    │   FastAPI Backend  │
                    │  ┌─────────────┐  │
                    │  │ API Routes  │  │
                    │  └──────┬──────┘  │
                    │         │         │
                    │  ┌──────┴──────┐  │
                    │  │  Services   │  │
                    │  │ ┌─────────┐ │  │
                    │  │ │Fetcher  │ │  │
                    │  │ │Inference│ │  │
                    │  │ │Models   │ │  │
                    │  │ └─────────┘ │  │
                    │  └─────────────┘  │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │    SQLite / CSV   │
                    └───────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Streamlit, Plotly, Pandas |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Data | AKShare, Requests |
| Models | SciPy, Statsmodels, NumPy |
| Storage | SQLite, CSV, Excel |

---

## 📡 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/indicators/` | GET | List indicators |
| `/api/v1/indicators/{id}` | GET | Get indicator details |
| `/api/v1/indicators/` | POST | Create indicator |
| `/api/v1/inference/available` | GET | List available inference indicators |
| `/api/v1/inference/calculate` | POST | Calculate inference |
| `/api/v1/inference/infer_all` | POST | Infer all possible indicators |
| `/api/v1/inference/models/phillips` | GET | Phillips Curve model |
| `/api/v1/inference/models/okun` | GET | Okun's Law model |
| `/api/v1/inference/models/cobb_douglas` | GET | Cobb-Douglas model |
| `/api/v1/inference/models/solow` | GET | Solow Growth model |
| `/api/v1/scrape/` | POST | Trigger data collection |
| `/api/v1/scrape/status` | GET | Get scrape status |
| `/api/v1/scrape/sources` | GET | List data sources |

### Example Requests

#### Calculate Deficit Rate

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

#### Run Phillips Curve Model

```bash
curl "http://localhost:8001/api/v1/inference/models/phillips?unemployment=5.5&natural_unemployment=5.0&expected_inflation=2.0&beta=0.5"
```

---

## 📊 Data Sources

All data is sourced from official Chinese government public data portals:

| Source | Agency | Indicators | URL |
|--------|--------|------------|-----|
| NBS | National Bureau of Statistics | GDP, CPI, PPI, PMI, Employment, Population | [data.stats.gov.cn](https://data.stats.gov.cn) |
| PBC | People's Bank of China | M0, M1, M2, Interest Rates, Social Financing | [pbc.gov.cn](http://www.pbc.gov.cn) |
| Customs | General Administration of Customs | Import, Export, Trade Balance | [customs.gov.cn](http://www.customs.gov.cn) |
| MOF | Ministry of Finance | Fiscal Revenue, Expenditure, Deficit | [mof.gov.cn](http://www.mof.gov.cn) |

### Data Update Frequency

| Indicator | Frequency | Typical Lag |
|-----------|-----------|-------------|
| GDP | Quarterly | 15 days |
| CPI/PPI | Monthly | 10 days |
| PMI | Monthly | 1 day |
| M2 | Monthly | 10 days |
| Trade Data | Monthly | 7 days |
| Fiscal Data | Monthly | 15 days |

---

## 🗺️ Roadmap

### Version 3.1 (Planned)

- [ ] **Data Cleaning Module**
  - Automatic missing value detection
  - Outlier identification and handling
  - Data imputation methods (linear, spline, ML-based)

- [ ] **Enhanced Visualization**
  - Time series decomposition charts
  - Correlation heatmaps
  - Regional comparison maps
  - Interactive dashboards with filters

- [ ] **Simulation Module**
  - Monte Carlo simulation for risk analysis
  - Scenario analysis (optimistic, baseline, pessimistic)
  - Policy impact simulation

### Version 3.2 (Planned)

- [ ] **Extended Models**
  - VAR (Vector Autoregression)
  - ARIMA time series forecasting
  - Machine learning predictions

- [ ] **Report Generation**
  - Automated PDF reports
  - PowerPoint presentation generation
  - Email report scheduling

- [ ] **Multi-language Support**
  - Full English UI
  - Japanese interface
  - Custom language packs

### Version 4.0 (Future)

- [ ] **Cloud Deployment**
  - Docker images
  - Kubernetes Helm charts
  - AWS/Azure deployment guides

- [ ] **Enterprise Features**
  - Multi-tenant support
  - SSO integration
  - Advanced RBAC

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/badhope/national_stats.git
cd national_stats

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
pytest tests/

# Format code
black .
```

### Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

### What this means:

- ✅ You can use, study, and modify the software
- ✅ You can distribute the software
- ✅ You can distribute modified versions
- ⚠️ You must include the original license
- ⚠️ You must state changes made to the source
- ⚠️ Derivative works must also be GPL-3.0 licensed

---

## ⚠️ Disclaimer

This platform is for **educational and research purposes only**. Analysis results do not constitute investment advice or policy recommendations. Data is sourced from official public channels; please contact us if there are copyright concerns.

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/badhope/national_stats/issues)
- **Discussions**: [GitHub Discussions](https://github.com/badhope/national_stats/discussions)
- **Email**: nedap@example.com

---

## 🙏 Acknowledgments

- [AKShare](https://github.com/akfamily/akshare) - Economic data API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Streamlit](https://streamlit.io/) - Data app framework
- All contributors and users

---

<div align="center">

**Made with ❤️ by the NEDAP Team**

[⬆ Back to Top](#-national-economic-data-analysis-platform-nedap)

</div>
