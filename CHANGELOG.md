# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-03-23

### Added
- **Internationalization (i18n) Support**
  - English/Chinese language toggle in sidebar
  - Complete translation dictionary in `app/i18n.py`
  - Language preference persisted in session state

- **Batch Calculation API Endpoint**
  - `POST /api/v1/inference/batch_calculate` for bulk indicator calculations
  - Support for multiple indicators in single request
  - Confidence intervals for Monte Carlo method

- **Enhanced UI/UX**
  - Gradient background styling
  - Card-based layout for feature sections
  - Animated metric displays
  - Responsive design improvements

### Fixed
- **Syntax Error in Streamlit App**
  - Fixed `legend=dict orientation="h"` missing parentheses in `update_layout()`
  - File: `app/streamlit_app.py` line 417

### Improved
- **Code Quality**
  - All 68 unit tests passing
  - Syntax validation for all Python modules
  - Backend import validation successful

- **API Documentation**
  - Enhanced OpenAPI schema
  - Better error messages for missing fields

## [2.0.0] - 2026-03-22

### Added
- **Core Economic Models**
  - `FiscalAnalyzer` - Government revenue, expenditure, deficit analysis
  - `RegionalAnalyzer` - Regional economic disparity and convergence testing
  - `IncomeDistributionAnalyzer` - Income distribution and inequality metrics
  - `IndustrialAnalyzer` - Industrial structure and upgrading analysis
  - `InnovationAnalyzer` - R&D and innovation capability assessment

- **Backend API (FastAPI)**
  - `GET /api/v1/indicators/` - List all economic indicators
  - `POST /api/v1/inference/calculate` - Single indicator calculation
  - `POST /api/v1/inference/infer_all` - Calculate all possible indicators
  - `GET /api/v1/inference/available_indicators` - Get available indicators
  - `POST /api/v1/data/` - Create economic indicator records
  - `GET /api/v1/data/` - Query indicator records
  - `GET /health` - Health check endpoint

- **Data Scraping Infrastructure**
  - `MinistryOfFinanceScraper` - Official fiscal data
  - `NationalBureauOfStatisticsScraper` - GDP, CPI, population
  - `CustomsScraper` - Import/export data
  - `CentralBankScraper` - Monetary data

- **Teaching Models**
  - Phillips Curve analysis
  - Okun's Law calculations
  - Cobb-Douglas production function
  - Harrod-Domar growth model

- **Frontend (Streamlit)**
  - Multi-module dashboard
  - Interactive Plotly visualizations
  - API status monitoring
  - Economic trends display

- **Documentation**
  - `README.md` - English documentation
  - `README_zh.md` - Chinese documentation
  - `CONTRIBUTING.md` - Contribution guidelines
  - `LICENSE` - GPL v3.0 license

### Changed
- Improved indicator calculation formulas
- Enhanced convergence testing algorithms
- Better error handling in API endpoints

## [1.0.0] - 2026-03-20

### Added
- Initial project structure
- Basic fiscal analysis module
- Regional economic data models
