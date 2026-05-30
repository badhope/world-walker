# Notebooks - 数据探索与分析

## 📓 说明

这个文件夹存放数据探索性分析（EDA）的脚本和 notebook。

### 可用脚本

#### 1. `eda_real_data.py`
完整的真实数据探索性分析脚本，包括：
- ✅ 从 AKShare 获取真实宏观经济数据
- ✅ 数据清洗与质量检查
- ✅ 描述性统计
- ✅ 相关性分析
- ✅ 可视化图表生成（GDP趋势、CPI趋势、产业结构）
- ✅ 企业端分析演示
- ✅ 智能洞察生成

**运行方式**：
```bash
python notebooks/eda_real_data.py
```

### 输出

脚本运行后会在 `data/charts/` 目录下生成可视化图表：
- `gdp_trend.png` - GDP及三次产业增长趋势
- `cpi_trend.png` - CPI同比增长率趋势
- `industry_structure.png` - 三次产业结构饼图

## 📊 如何转换为 .ipynb

如果你想创建真正的 Jupyter Notebook，可以：

1. 使用 Jupyter 手动创建，复制代码到 cell
2. 使用 `jupytext` 工具转换：
```bash
pip install jupytext
jupytext --to notebook notebooks/eda_real_data.py
```

## 🔬 建议后续分析方向

1. **时间序列预测**
   - 使用 ARIMA 或 Prophet 预测 GDP 和 CPI
   
2. **城市对比分析**
   - 获取更多城市的经济数据，做横向对比
   
3. **产业细分分析**
   - 深入分析半导体行业的上下游数据
   
4. **地理可视化**
   - 使用 GeoPandas 绘制区域经济热力图
