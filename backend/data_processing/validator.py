"""
数据验证模块
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器"""

    def __init__(self):
        pass

    def validate_required_columns(self, df: pd.DataFrame, required_columns: list[str]) -> dict[str, any]:
        """验证必需列"""
        missing_columns = [col for col in required_columns if col not in df.columns]
        return {
            "valid": len(missing_columns) == 0,
            "missing_columns": missing_columns,
            "existing_columns": list(df.columns),
        }

    def validate_data_types(self, df: pd.DataFrame, expected_types: dict[str, type]) -> dict[str, any]:
        """验证数据类型"""
        mismatches = {}
        for col, expected_type in expected_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if not self._check_type_match(actual_type, expected_type):
                    mismatches[col] = {"expected": expected_type.__name__, "actual": actual_type}
        return {"valid": len(mismatches) == 0, "mismatches": mismatches}

    def _check_type_match(self, actual: str, expected: type) -> bool:
        """检查类型是否匹配"""
        if expected is int:
            return "int" in actual
        elif expected is float:
            return "float" in actual or "int" in actual
        elif expected is str:
            return "object" in actual or "string" in actual
        return False

    def validate_value_ranges(self, df: pd.DataFrame, value_ranges: dict[str, tuple]) -> dict[str, any]:
        """验证值范围"""
        range_violations = {}
        for col, (min_val, max_val) in value_ranges.items():
            if col in df.columns:
                out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
                if len(out_of_range) > 0:
                    range_violations[col] = {
                        "min_expected": min_val,
                        "max_expected": max_val,
                        "count": len(out_of_range),
                    }
        return {"valid": len(range_violations) == 0, "violations": range_violations}

    def validate_unique_values(self, df: pd.DataFrame, unique_columns: list[str]) -> dict[str, any]:
        """验证唯一性"""
        duplicates = {}
        for col in unique_columns:
            if col in df.columns:
                duplicate_count = df.duplicated(subset=[col]).sum()
                if duplicate_count > 0:
                    duplicates[col] = {"duplicate_count": int(duplicate_count)}
        return {"valid": len(duplicates) == 0, "duplicates": duplicates}

    def validate_not_null(self, df: pd.DataFrame, not_null_columns: list[str]) -> dict[str, any]:
        """验证非空"""
        null_columns = {}
        for col in not_null_columns:
            if col in df.columns:
                null_count = df[col].isna().sum()
                if null_count > 0:
                    null_columns[col] = {"null_count": int(null_count)}
        return {"valid": len(null_columns) == 0, "null_columns": null_columns}

    def generate_full_validation_report(
        self,
        df: pd.DataFrame,
        required_columns: list[str] | None = None,
        expected_types: dict[str, type] | None = None,
        value_ranges: dict[str, tuple] | None = None,
        unique_columns: list[str] | None = None,
        not_null_columns: list[str] | None = None,
    ) -> dict[str, any]:
        """生成完整验证报告"""
        report = {}

        if required_columns:
            report["required_columns"] = self.validate_required_columns(df, required_columns)

        if expected_types:
            report["data_types"] = self.validate_data_types(df, expected_types)

        if value_ranges:
            report["value_ranges"] = self.validate_value_ranges(df, value_ranges)

        if unique_columns:
            report["unique_values"] = self.validate_unique_values(df, unique_columns)

        if not_null_columns:
            report["not_null"] = self.validate_not_null(df, not_null_columns)

        report["overall_valid"] = all(result.get("valid", True) for result in report.values())

        return report


# 单例
data_validator = DataValidator()
