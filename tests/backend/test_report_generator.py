import warnings

warnings.filterwarnings("ignore")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json

import numpy as np
import pandas as pd

from backend.report_generator import ReportGenerator
from backend.utils.report_generator import (
    FlexibleReportGenerator,
    OutputFormat,
    ReportConfig,
    ReportSection,
)


def _make_sample_insights():
    return {
        "best_model": {"name": "random_forest", "r2_score": 0.85},
        "model_comparison": [
            {"model": "linear", "r2": 0.70, "mae": 100.0, "rmse": 150.0},
            {"model": "random_forest", "r2": 0.85, "mae": 60.0, "rmse": 90.0},
        ],
        "feature_importance": {
            "top_features": [("population_1km", 0.35), ("store_area", 0.25)],
            "all_features": [("population_1km", 0.35), ("store_area", 0.25), ("rent_per_sqm", 0.15)],
        },
        "recommendations": ["建议优先选择人口密集区域", "建议优化定价策略"],
    }


def _make_sample_data_quality():
    return {
        "basic_info": {"total_rows": 100, "total_columns": 10, "memory_usage_mb": 0.5},
        "missing_values": {"total_missing_cells": 5, "columns_with_missing": []},
        "duplicates": {"total_duplicates": 0, "duplicate_percent": 0.0},
        "overall_quality": {"quality_score": 95.0, "rating": "Excellent"},
    }


def _make_sample_processed_data():
    np.random.seed(42)
    return pd.DataFrame(
        {
            "feature_a": np.random.randn(20),
            "feature_b": np.random.randn(20),
            "target": np.random.randn(20),
        }
    )


class TestJSONReport:
    def test_generate_json_report(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        full_results = {
            "data_quality": _make_sample_data_quality(),
            "insights": _make_sample_insights(),
        }
        path = rg.generate_json_report(full_results)
        assert Path(path).exists()
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert "data_quality" in loaded
        assert "insights" in loaded

    def test_json_report_content(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        full_results = {"data_quality": _make_sample_data_quality(), "insights": _make_sample_insights()}
        path = rg.generate_json_report(full_results)
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["data_quality"]["overall_quality"]["quality_score"] == 95.0

    def test_json_report_custom_filename(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        path = rg.generate_json_report({"key": "value"}, filename="custom.json")
        assert Path(path).exists()
        assert "custom.json" in path


class TestTextReport:
    def test_generate_text_report(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        path = rg.generate_text_report(_make_sample_data_quality(), _make_sample_insights())
        assert Path(path).exists()

    def test_text_report_contains_key_info(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        path = rg.generate_text_report(_make_sample_data_quality(), _make_sample_insights())
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "数据质量" in content
        assert "最佳模型" in content

    def test_text_report_custom_filename(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        path = rg.generate_text_report(_make_sample_data_quality(), _make_sample_insights(), filename="summary.txt")
        assert Path(path).exists()
        assert "summary.txt" in path


class TestExcelReport:
    def test_generate_excel_report(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        data = _make_sample_processed_data()
        path = rg.generate_excel_report(_make_sample_data_quality(), _make_sample_insights(), data)
        assert Path(path).exists()

    def test_excel_report_readable(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        data = _make_sample_processed_data()
        path = rg.generate_excel_report(_make_sample_data_quality(), _make_sample_insights(), data)
        df = pd.read_excel(path, sheet_name="数据质量")
        assert len(df) > 0

    def test_excel_report_has_model_comparison_sheet(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        data = _make_sample_processed_data()
        path = rg.generate_excel_report(_make_sample_data_quality(), _make_sample_insights(), data)
        xl = pd.ExcelFile(path)
        assert "模型对比" in xl.sheet_names


class TestGenerateAllReports:
    def test_generate_all_reports(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        data = _make_sample_processed_data()
        reports = rg.generate_all_reports(_make_sample_data_quality(), _make_sample_insights(), data)
        assert "json" in reports
        assert "text" in reports
        assert "excel" in reports
        assert reports["json"] is not None
        assert reports["text"] is not None
        assert reports["excel"] is not None

    def test_all_report_files_exist(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        data = _make_sample_processed_data()
        rg.generate_all_reports(_make_sample_data_quality(), _make_sample_insights(), data)
        assert (tmp_path / "analysis_report.json").exists()
        assert (tmp_path / "analysis_summary.txt").exists()
        assert (tmp_path / "analysis_report.xlsx").exists()


class TestFlexibleReportGenerator:
    def test_json_report_generation(self, tmp_path):
        gen = FlexibleReportGenerator()
        section = ReportSection(title="Test", content={"key": "value"}, order=0)
        config = ReportConfig(title="Test Report", format=OutputFormat.JSON)
        content = gen.generate_report([section], config)
        parsed = json.loads(content)
        assert parsed["title"] == "Test Report"

    def test_markdown_report_generation(self, tmp_path):
        gen = FlexibleReportGenerator()
        section = ReportSection(title="Overview", content={"metric": 42}, order=0)
        config = ReportConfig(title="MD Report", format=OutputFormat.MARKDOWN)
        content = gen.generate_report([section], config)
        assert "# MD Report" in content
        assert "Overview" in content

    def test_html_report_generation(self):
        gen = FlexibleReportGenerator()
        section = ReportSection(title="Summary", content={"score": 95}, order=0)
        config = ReportConfig(title="HTML Report", format=OutputFormat.HTML)
        content = gen.generate_report([section], config)
        assert "<html" in content
        assert "Summary" in content

    def test_save_report_to_file(self, tmp_path):
        gen = FlexibleReportGenerator()
        section = ReportSection(title="Data", content={"x": 1}, order=0)
        config = ReportConfig(title="Saved Report", format=OutputFormat.JSON)
        output_path = str(tmp_path / "saved_report.json")
        gen.generate_report([section], config, output_path)
        assert Path(output_path).exists()

    def test_quick_report(self):
        gen = FlexibleReportGenerator()
        content = gen.quick_report("Quick Test", {"a": 1, "b": 2})
        assert "Quick Test" in content
