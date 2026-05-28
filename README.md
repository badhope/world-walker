# national_stats - 区域产业经济分析平台

## 项目简介

面向地方政府和企业的**区域细分产业可复用经济分析工具**，以2025年深圳半导体产业为示例，展示完整的经济数据分析能力。

### 项目特色

- **企业端分析**：营商成本、供应链配套效率、政策红利兑现率
- **政府端分析**：财政杠杆率、产业带动系数、产业链补全度
- **经济学模型**：菲利普斯曲线、奥肯定律、柯布-道格拉斯生产函数
- **模块化设计**：更换配置即可分析任意地区/产业

## 技术栈

- **后端**: FastAPI + SQLAlchemy
- **数据分析**: Pandas + NumPy + SciPy
- **经济学模型**: statsmodels
- **可视化**: Plotly

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动API服务
python -m backend.api.main

# 访问文档
# http://localhost:8001/docs
```

## 项目结构

```
national_stats/
├── config/                    # 配置模块
│   ├── settings.py           # 主配置
│   ├── analysis_config.py     # 分析配置
│   ├── regions/              # 地区配置
│   └── industries/           # 产业配置
├── backend/                  # 后端代码
│   ├── api/                  # API接口
│   ├── data_collection/      # 数据采集
│   ├── data_processing/      # 数据处理
│   ├── analysis/             # 分析模块
│   └── utils/                # 工具模块
└── data/                     # 数据目录
```

## API文档

访问 `http://localhost:8001/docs` 查看完整API文档。

### 核心接口

- `POST /api/v1/analysis/enterprise` - 企业端分析
- `POST /api/v1/analysis/government` - 政府端分析
- `GET /api/v1/inference/models/cobb_douglas` - 经济学模型

## 许可证

MIT License
