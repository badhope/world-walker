"""
报告生成模块 - 支持PDF/Excel/Text/JSON
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_excel_report(
        self, data_quality: dict, insights: dict, processed_data: pd.DataFrame, filename: str = "analysis_report.xlsx"
    ):
        """生成Excel报告"""
        excel_path = self.output_dir / filename

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            # 1. 数据质量
            dq_data = [
                ["指标", "值"],
                ["总行数", data_quality.get("basic_info", {}).get("total_rows", "N/A")],
                ["总列数", data_quality.get("basic_info", {}).get("total_columns", "N/A")],
                ["内存使用(MB)", f"{data_quality.get('basic_info', {}).get('memory_usage_mb', 0):.2f}"],
                ["缺失单元格总数", data_quality.get("missing_values", {}).get("total_missing_cells", 0)],
                ["重复行数", data_quality.get("duplicates", {}).get("total_duplicates", 0)],
                ["数据质量评分", f"{data_quality.get('overall_quality', {}).get('quality_score', 0):.1f}/100"],
                ["质量等级", data_quality.get("overall_quality", {}).get("rating", "N/A")],
            ]
            pd.DataFrame(dq_data[1:], columns=dq_data[0]).to_excel(writer, sheet_name="数据质量", index=False)

            # 2. 最佳模型
            best_model = insights.get("best_model", {})
            model_summary = [
                ["最佳模型", best_model.get("name", "N/A")],
                ["R² Score", f"{best_model.get('r2_score', 0):.4f}"],
            ]
            pd.DataFrame(model_summary).to_excel(writer, sheet_name="最佳模型", index=False, header=False)

            # 3. 模型对比
            if "model_comparison" in insights:
                model_comp_df = pd.DataFrame(insights["model_comparison"])
                model_comp_df.to_excel(writer, sheet_name="模型对比", index=False)

            # 4. 特征重要性
            if "feature_importance" in insights:
                fi_df = pd.DataFrame(insights["feature_importance"]["all_features"], columns=["特征", "重要性"])
                fi_df.to_excel(writer, sheet_name="特征重要性", index=False)

            # 5. 业务建议
            if "recommendations" in insights:
                rec_df = pd.DataFrame(enumerate(insights["recommendations"], 1), columns=["序号", "建议"])
                rec_df.to_excel(writer, sheet_name="业务建议", index=False)

            # 6. 数据预览
            processed_data.head(50).to_excel(writer, sheet_name="数据预览", index=False)

        logger.info(f"Excel报告已保存到: {excel_path}")
        return str(excel_path)

    def generate_text_report(self, data_quality: dict, insights: dict, filename: str = "analysis_summary.txt"):
        """生成人类可读的文本报告"""
        txt_path = self.output_dir / filename

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("通用数据分析框架 - 分析报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            # 1. 数据质量
            f.write("【数据质量报告】\n")
            f.write(f"数据质量评分: {data_quality.get('overall_quality', {}).get('quality_score', 0):.1f}/100\n")
            f.write(f"质量等级: {data_quality.get('overall_quality', {}).get('rating', 'N/A')}\n")
            f.write(f"总行数: {data_quality.get('basic_info', {}).get('total_rows', 'N/A')}\n")
            f.write(f"总列数: {data_quality.get('basic_info', {}).get('total_columns', 'N/A')}\n")
            f.write(f"缺失单元格: {data_quality.get('missing_values', {}).get('total_missing_cells', 0)}\n\n")

            # 2. 最佳模型
            best_model = insights.get("best_model", {})
            f.write("【最佳模型】\n")
            f.write(f"模型: {best_model.get('name', 'N/A')}\n")
            f.write(f"R² Score: {best_model.get('r2_score', 0):.4f}\n\n")

            # 3. 模型对比
            if "model_comparison" in insights:
                f.write("【模型对比】\n")
                for item in insights["model_comparison"]:
                    f.write(f"  - {item['model']}: R²={item['r2']:.4f}, MAE={item['mae']:.2f}\n")
                f.write("\n")

            # 4. 特征重要性
            if "feature_importance" in insights:
                f.write("【Top 10 重要特征】\n")
                for i, (feature, importance) in enumerate(insights["feature_importance"]["top_features"][:10], 1):
                    f.write(f"{i}. {feature}: {importance:.4f}\n")
                f.write("\n")

            # 5. 业务建议
            f.write("【业务建议】\n")
            for i, rec in enumerate(insights.get("recommendations", []), 1):
                f.write(f"{i}. {rec}\n")

        logger.info(f"文本报告已保存到: {txt_path}")
        return str(txt_path)

    def generate_json_report(self, full_results: dict, filename: str = "analysis_report.json"):
        """生成JSON报告"""
        json_path = self.output_dir / filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(full_results, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"JSON报告已保存到: {json_path}")
        return str(json_path)

    def generate_pdf_report(
        self, data_quality: dict, insights: dict, visualizations: dict = None, filename: str = "analysis_report.pdf"
    ):
        """
        生成PDF报告

        注意：为了避免依赖问题，我们先用纯Python实现一个简化版PDF
        如果有reportlab可以用reportlab，否则用文本方式
        """
        try:
            # 尝试用reportlab生成真正的PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

            pdf_path = self.output_dir / filename
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            styles = getSampleStyleSheet()

            story = []

            # 标题
            title_style = styles["Title"]
            story.append(Paragraph("通用数据分析框架 - 分析报告", title_style))
            story.append(Spacer(1, 12))

            story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
            story.append(Spacer(1, 12))

            # 数据质量
            story.append(Paragraph("1. 数据质量报告", styles["Heading2"]))
            dq_data = [
                ["指标", "值"],
                ["数据质量评分", f"{data_quality.get('overall_quality', {}).get('quality_score', 0):.1f}/100"],
                ["质量等级", data_quality.get("overall_quality", {}).get("rating", "N/A")],
                ["总行数", str(data_quality.get("basic_info", {}).get("total_rows", "N/A"))],
                ["总列数", str(data_quality.get("basic_info", {}).get("total_columns", "N/A"))],
            ]

            dq_table = Table(dq_data, colWidths=[3 * inch, 3 * inch])
            dq_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(dq_table)
            story.append(Spacer(1, 12))

            # 最佳模型
            story.append(Paragraph("2. 最佳模型", styles["Heading2"]))
            best_model = insights.get("best_model", {})
            story.append(Paragraph(f"模型: {best_model.get('name', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(f"R² Score: {best_model.get('r2_score', 0):.4f}", styles["Normal"]))
            story.append(Spacer(1, 12))

            # 业务建议
            if "recommendations" in insights:
                story.append(Paragraph("3. 业务建议", styles["Heading2"]))
                for i, rec in enumerate(insights.get("recommendations", []), 1):
                    story.append(Paragraph(f"{i}. {rec}", styles["Normal"]))

            # 生成
            doc.build(story)
            logger.info(f"PDF报告已保存到: {pdf_path}")
            return str(pdf_path)

        except ImportError:
            # 如果没有reportlab，先生成文本提示，同时也保存文本版
            logger.warning("reportlab未安装，无法生成PDF报告。已生成文本报告替代。")
            self.generate_text_report(data_quality, insights)
            return None

    def generate_all_reports(
        self, data_quality: dict, insights: dict, processed_data: pd.DataFrame = None, visualizations: dict = None
    ) -> dict:
        """生成所有报告"""
        reports = {}

        # JSON报告
        reports["json"] = self.generate_json_report({"data_quality": data_quality, "insights": insights})

        # Excel报告
        if processed_data is not None:
            reports["excel"] = self.generate_excel_report(data_quality, insights, processed_data)

        # 文本报告
        reports["text"] = self.generate_text_report(data_quality, insights)

        # PDF报告（如果可能）
        reports["pdf"] = self.generate_pdf_report(data_quality, insights, visualizations)

        return reports
