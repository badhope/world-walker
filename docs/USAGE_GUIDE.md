# 📖 使用指南

本指南将帮助您快速上手区域产业经济分析平台。

## 目录

1. [环境要求](#环境要求)
2. [安装步骤](#安装步骤)
3. [快速开始](#快速开始)
4. [运行模式](#运行模式)
5. [常见问题](#常见问题)

---

## 环境要求

### Python版本
- Python 3.9 或更高版本
- 推荐 Python 3.10/3.11

### 操作系统
- Linux (Ubuntu 20.04+)
- macOS 10.14+
- Windows 10+ (建议使用 WSL2)

### 依赖软件
- Git
- pip (Python包管理器)

---

## 安装步骤

### 方式一：自动化安装（推荐）

```bash
# 克隆项目
git clone https://github.com/your-project/national-stats-analyzer.git
cd national-stats-analyzer

# 一键安装
bash scripts/setup.sh --venv
```

### 方式二：手动安装

```bash
# 1. 克隆项目
git clone https://github.com/your-project/national-stats-analyzer.git
cd national-stats-analyzer

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或: venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env

# 5. 初始化目录
mkdir -p data/{raw,processed,cache,exports}
```

---

## 快速开始

### 1. 检查环境

```bash
python main.py --mode check
```

### 2. 运行示例分析

```bash
# 运行所有示例
python main.py --mode example

# 仅企业端分析
python main.py --mode example --type enterprise

# 仅政府端分析
python main.py --mode example --type government
```

### 3. 启动API服务

```bash
python main.py --mode api --port 8001
```

访问 http://localhost:8001/docs 查看API文档。

---

## 运行模式

### API模式

启动FastAPI Web服务：

```bash
python main.py --mode api [选项]

# 选项：
#   --port 8001      API服务端口
#   --host 0.0.0.0   服务地址
#   --reload         启用代码热重载（开发模式）
```

### 示例模式

运行分析示例脚本：

```bash
python main.py --mode example [选项]

# 选项：
#   --type enterprise    仅运行企业端分析
#   --type government    仅运行政府端分析
#   --type comprehensive 生成综合报告
```

### 检查模式

检查系统环境：

```bash
python main.py --mode check
```

### 分析模式

运行自定义分析（开发中）：

```bash
python main.py --mode analysis --config my_config.json
```

---

## 使用示例

### 企业端分析

```python
from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner

# 初始化分析器
runner = EnterpriseAnalysisRunner()

# 生成报告
report = runner.generate_report()

# 保存报告
runner.save_report(report)
```

### 政府端分析

```python
from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner

# 初始化分析器
runner = GovernmentAnalysisRunner()

# 生成报告
report = runner.generate_report()

# 可视化
runner.visualize_results(report)
```

### API调用

```bash
# 健康检查
curl http://localhost:8001/api/v1/health

# 企业端分析
curl -X POST http://localhost:8001/api/v1/analysis/enterprise \
  -H "Content-Type: application/json" \
  -d '{"region": "深圳", "industry": "半导体", "year": 2025}'

# 政府端分析
curl -X POST http://localhost:8001/api/v1/analysis/government \
  -H "Content-Type: application/json" \
  -d '{"region": "深圳", "industry": "半导体", "year": 2025}'
```

---

## 常见问题

### Q1: 安装依赖失败？

**解决方案：**

```bash
# 升级pip
pip install --upgrade pip

# 单独安装失败的包
pip install <package_name>

# 使用豆瓣源（国内加速）
pip install -r requirements.txt -i https://pypi.doubanio.com/simple/
```

### Q2: Python版本不兼容？

**解决方案：**

```bash
# 检查Python版本
python3 --version

# 如果版本过低，使用pyenv升级
pyenv install 3.11.0
pyenv global 3.11.0
```

### Q3: 端口被占用？

**解决方案：**

```bash
# 查找占用端口的进程
lsof -ti:8001

# 关闭进程
kill <PID>

# 或使用其他端口
python main.py --mode api --port 8002
```

### Q4: 数据文件不存在？

**解决方案：**

```bash
# 检查数据目录
ls -la examples/shenzhen_semiconductor_2025/data/

# 如果缺失，运行setup初始化
python main.py --mode check
```

### Q5: API文档无法访问？

**解决方案：**

```bash
# 确保API服务正在运行
ps aux | grep uvicorn

# 检查端口
netstat -tuln | grep 8001

# 查看日志
tail -f logs/app.log
```

---

## 获取帮助

- 📖 查看 [README.md](../README.md) - 项目主页
- ⚙️ 查看 [CONFIG_GUIDE.md](./CONFIG_GUIDE.md) - 配置详解
- 📊 查看 [EXAMPLE_ANALYSIS.md](./EXAMPLE_ANALYSIS.md) - 示例分析
- 🐛 问题反馈：https://github.com/your-project/national-stats-analyzer/issues
