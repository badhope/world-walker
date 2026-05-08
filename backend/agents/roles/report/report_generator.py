"""
自动报告生成模块 - 生成完整的分析报告
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EconomicReportGenerator:
    """经济分析报告自动生成器"""

    def __init__(self):
        self.report_data = {}

    def gather_data(self) -> Dict[str, Any]:
        """收集所有经济数据"""
        data = {}

        try:
            df = ak.macro_china_gdp()
            data['gdp'] = df.dropna().tail(4).to_dict('records')
            data['gdp_latest'] = df['国内生产总值-绝对值'].dropna().iloc[-1]
            data['gdp_growth'] = df['国内生产总值-同比增长'].dropna().iloc[-1]
        except Exception as e:
            logger.error(f"GDP数据获取失败: {e}")

        try:
            df = ak.macro_china_cpi_yearly()
            data['cpi'] = df.dropna(subset=['今值']).tail(12).to_dict('records')
            data['cpi_latest'] = float(df['今值'].dropna().iloc[-1])
        except Exception as e:
            logger.error(f"CPI数据获取失败: {e}")

        try:
            df = ak.macro_china_ppi_yearly()
            data['ppi'] = df.dropna(subset=['今值']).tail(12).to_dict('records')
            data['ppi_latest'] = float(df['今值'].dropna().iloc[-1])
        except Exception as e:
            logger.error(f"PPI数据获取失败: {e}")

        try:
            df = ak.macro_china_m2_yearly()
            data['m2'] = df.dropna(subset=['今值']).tail(12).to_dict('records')
            data['m2_latest'] = float(df['今值'].dropna().iloc[-1])
        except Exception as e:
            logger.error(f"M2数据获取失败: {e}")

        try:
            df = ak.macro_china_pmi_yearly()
            data['pmi'] = df.dropna(subset=['今值']).tail(12).to_dict('records')
            data['pmi_latest'] = float(df['今值'].dropna().iloc[-1])
        except Exception as e:
            logger.error(f"PMI数据获取失败: {e}")

        try:
            df = ak.macro_china_lpr()
            data['lpr'] = {
                '1y': float(df['LPR1Y'].iloc[-1]),
                '5y': float(df['LPR5Y'].iloc[-1])
            }
        except Exception as e:
            logger.error(f"LPR数据获取失败: {e}")

        try:
            df = ak.macro_china_urban_unemployment()
            data['unemployment'] = float(df['value'].dropna().iloc[-1])
        except Exception as e:
            logger.error(f"失业率数据获取失败: {e}")

        self.report_data = data
        return data

    def generate_summary(self) -> str:
        """生成摘要"""
        data = self.report_data
        insights = []

        cpi = data.get('cpi_latest', 0)
        ppi = data.get('ppi_latest', 0)
        pmi = data.get('pmi_latest', 50)
        m2 = data.get('m2_latest', 0)
        unemp = data.get('unemployment', 0)

        if cpi < 0.5:
            insights.append("⚠️ CPI处于低位，存在通缩风险")
        elif cpi > 3:
            insights.append("⚠️ CPI偏高，通胀压力较大")
        else:
            insights.append("✅ CPI处于温和区间")

        if ppi < -2:
            insights.append("🔴 PPI持续负增长，工业领域面临通缩压力")
        elif ppi < 0:
            insights.append("⚠️ PPI为负，工业品价格承压")

        if pmi < 50:
            insights.append(f"🔴 PMI={pmi:.1f}，低于荣枯线，制造业收缩")
        elif pmi < 52:
            insights.append(f"⚠️ PMI={pmi:.1f}，制造业扩张放缓")

        if unemp > 5.5:
            insights.append(f"⚠️ 失业率={unemp:.1f}%，就业压力较大")
        elif unemp > 5:
            insights.append(f"⚠️ 失业率={unemp:.1f}%，需关注就业形势")

        if insights:
            return "\n".join(insights)
        return "✅ 主要经济指标运行平稳"

    def generate_indicators_table(self) -> str:
        """生成指标表格"""
        data = self.report_data
        rows = [
            "| 指标 | 最新值 | 状态 | 说明 |",
            "|------|--------|------|------|"
        ]

        indicators = [
            ('GDP增速', data.get('gdp_growth'), '%', lambda v: '✅' if v > 4 else '⚠️' if v > 3 else '🔴'),
            ('CPI', data.get('cpi_latest'), '%', lambda v: '✅' if 0 < v < 3 else '⚠️'),
            ('PPI', data.get('ppi_latest'), '%', lambda v: '🔴' if v < -2 else '⚠️' if v < 0 else '✅'),
            ('M2', data.get('m2_latest'), '%', lambda v: '✅' if 7 < v < 12 else '⚠️'),
            ('PMI', data.get('pmi_latest'), '', lambda v: '✅' if v > 50 else '🔴'),
            ('失业率', data.get('unemployment'), '%', lambda v: '✅' if v < 5 else '⚠️' if v < 6 else '🔴'),
        ]

        for name, value, unit, status_fn in indicators:
            if value is not None:
                status = status_fn(value)
                rows.append(f"| {name} | {value:.1f}{unit} | {status} | |")

        return "\n".join(rows)

    def generate_province_analysis(self) -> str:
        """生成省份分析"""
        try:
            from backend.agents.roles.comparison import PROVINCE_DATA

            province_gdp = PROVINCE_DATA.get('gdp_2024', {})
            sorted_provinces = sorted(province_gdp.items(), key=lambda x: x[1], reverse=True)

            total = sum(province_gdp.values())
            top3_share = sum(p[1] for p in sorted_provinces[:3]) / total * 100

            rows = [
                "| 排名 | 省份 | GDP(亿元) | 占比 |",
                "|------|------|----------|------|"
            ]

            for i, (province, gdp) in enumerate(sorted_provinces[:10], 1):
                share = gdp / total * 100
                rows.append(f"| {i} | {province} | {gdp:,} | {share:.1f}% |")

            rows.append("")
            rows.append(f"**分析**: 前三省(广东、江苏、山东)GDP合计占比 {top3_share:.1f}%，经济集中度较高。")

            return "\n".join(rows)
        except Exception as e:
            return f"省份分析生成失败: {e}"

    def generate_trend_analysis(self) -> str:
        """生成趋势分析"""
        data = self.report_data
        trends = []

        cpi_history = data.get('cpi', [])
        if len(cpi_history) >= 3:
            cpi_values = [r['今值'] for r in cpi_history[-3:] if '今值' in r]
            if len(cpi_values) >= 2:
                cpi_trend = "下降" if cpi_values[-1] < cpi_values[0] else "上升"
                trends.append(f"• CPI近3期{cpi_trend}，最新值{cpi_values[-1]:.1f}%")

        ppi_history = data.get('ppi', [])
        if len(ppi_history) >= 3:
            ppi_values = [r['今值'] for r in ppi_history[-3:] if '今值' in r]
            if len(ppi_values) >= 2:
                ppi_trend = "下降" if ppi_values[-1] < ppi_values[0] else "上升"
                trends.append(f"• PPI近3期{ppi_trend}，最新值{ppi_values[-1]:.1f}%")

        pmi_history = data.get('pmi', [])
        if len(pmi_history) >= 3:
            pmi_values = [r['今值'] for r in pmi_history[-3:] if '今值' in r]
            if len(pmi_values) >= 2:
                pmi_trend = "回升" if pmi_values[-1] > pmi_values[0] else "回落"
                trends.append(f"• PMI近3期{pmi_trend}，最新值{pmi_values[-1]:.1f}")

        if trends:
            return "\n".join(trends)
        return "趋势数据不足"

    def generate_full_report(self) -> str:
        """生成完整报告"""
        self.gather_data()

        report = f"""
# 📊 中国宏观经济形势分析报告

**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}  
**数据来源**: 国家统计局、人民银行 (via AKShare)

---

## 一、执行摘要

{self.generate_summary()}

---

## 二、核心指标监测

{self.generate_indicators_table()}

---

## 三、趋势分析

{self.generate_trend_analysis()}

---

## 四、省份经济对比

{self.generate_province_analysis()}

---

## 五、风险预警

### 5.1 通胀风险评估

| 指标 | 状态 | 说明 |
|------|------|------|
| CPI | {"⚠️ 关注" if self.report_data.get('cpi_latest', 0) < 1 else "✅ 正常"} | {"存在通缩风险" if self.report_data.get('cpi_latest', 0) < 1 else "通胀温和"} |
| PPI | {"🔴 预警" if self.report_data.get('ppi_latest', 0) < -2 else "⚠️ 关注" if self.report_data.get('ppi_latest', 0) < 0 else "✅ 正常"} | {"工业品价格持续下降" if self.report_data.get('ppi_latest', 0) < -2 else "工业品价格承压"} |

### 5.2 制造业景气评估

| 指标 | 状态 | 说明 |
|------|------|------|
| PMI | {"🔴 收缩" if self.report_data.get('pmi_latest', 50) < 50 else "⚠️ 放缓" if self.report_data.get('pmi_latest', 50) < 52 else "✅ 扩张"} | {f"PMI={self.report_data.get('pmi_latest', 0):.1f}" if self.report_data.get('pmi_latest') else "数据获取中"} |

---

## 六、政策建议

1. **货币政策**: 保持流动性合理充裕，适时降准降息
2. **财政政策**: 加大逆周期调节力度，扩大有效投资
3. **产业政策**: 支持制造业转型升级，推动高质量发展
4. **就业政策**: 重点关注青年就业，稳就业保民生

---

## 七、附录

### 7.1 指标说明

- **GDP**: 国内生产总值，衡量经济规模的核心指标
- **CPI**: 居民消费价格指数，反映通货膨胀水平
- **PPI**: 工业生产者出厂价格指数，反映工业品价格变化
- **M2**: 广义货币供应量，反映货币政策松紧程度
- **PMI**: 采购经理指数，反映制造业景气程度，50为荣枯线
- **LPR**: 贷款市场报价利率，央行政策利率

### 7.2 数据说明

本报告数据来源于国家统计局、人民银行等官方渠道，通过AKShare数据接口实时获取。数据截止时间为报告生成时间。

---

*本报告由 NEDAP AI 智能分析系统自动生成*  
*免责声明: 本报告仅供参考，不构成投资建议*
"""

        return report

    def save_report(self, filename: str = None) -> str:
        """保存报告到文件"""
        if filename is None:
            filename = f"/workspace/economic_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"

        report = self.generate_full_report()

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        return filename


def generate_economic_report() -> str:
    """
    快速生成经济报告
    """
    generator = EconomicReportGenerator()
    return generator.generate_full_report()


def generate_and_save_report(filename: str = None) -> str:
    """
    生成并保存报告
    """
    generator = EconomicReportGenerator()
    return generator.save_report(filename)
