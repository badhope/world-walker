import warnings
warnings.filterwarnings('ignore')

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import pandas as pd
import numpy as np

from backend.analysis.base_analyzer import BaseAnalyzer
from backend.analysis.enterprise_analyzer import EnterpriseAnalyzer
from backend.analysis.government_analyzer import GovernmentAnalyzer
from backend.retail_location.analyzer import RetailLocationAnalyzer
from backend.retail_location.data_adapter import RetailDataAdapter
from backend.sales_forecast.analyzer import SalesForecastAnalyzer
from backend.sales_forecast.data_adapter import SalesDataAdapter
from backend.data.city_data import get_city_data, get_all_cities


ALL_ANALYZER_CLASSES = [EnterpriseAnalyzer, GovernmentAnalyzer, RetailLocationAnalyzer, SalesForecastAnalyzer]


class TestAnalyzerInheritance:

    def test_all_analyzers_inherit_base(self):
        for cls in ALL_ANALYZER_CLASSES:
            assert issubclass(cls, BaseAnalyzer), f"{cls.__name__} does not inherit BaseAnalyzer"

    def test_enterprise_analyzer_inherits_base(self):
        assert issubclass(EnterpriseAnalyzer, BaseAnalyzer)

    def test_government_analyzer_inherits_base(self):
        assert issubclass(GovernmentAnalyzer, BaseAnalyzer)

    def test_retail_location_analyzer_inherits_base(self):
        assert issubclass(RetailLocationAnalyzer, BaseAnalyzer)

    def test_sales_forecast_analyzer_inherits_base(self):
        assert issubclass(SalesForecastAnalyzer, BaseAnalyzer)


class TestAnalyzerInterface:

    def test_all_analyzers_have_run_full_analysis(self):
        for cls in ALL_ANALYZER_CLASSES:
            assert hasattr(cls, 'run_full_analysis'), f"{cls.__name__} missing run_full_analysis"

    def test_all_analyzers_have_predict(self):
        for cls in ALL_ANALYZER_CLASSES:
            assert hasattr(cls, 'predict'), f"{cls.__name__} missing predict"

    def test_run_full_analysis_is_callable(self):
        for cls in ALL_ANALYZER_CLASSES:
            instance = cls()
            assert callable(getattr(instance, 'run_full_analysis'))

    def test_predict_is_callable(self):
        for cls in ALL_ANALYZER_CLASSES:
            instance = cls()
            assert callable(getattr(instance, 'predict'))


class TestEnterpriseAnalyzerRealData:

    def setup_method(self):
        self.analyzer = EnterpriseAnalyzer()

    def test_analyze_city_with_real_data(self):
        result = self.analyzer.analyze_city("深圳")
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert result["overall_score"] > 0

    def test_scores_based_on_real_data_not_hardcoded(self):
        result_sz = self.analyzer.analyze_city("深圳")
        result_sh = self.analyzer.analyze_city("上海")
        assert result_sz["overall_score"] != result_sh["overall_score"]

    def test_business_costs_from_real_data(self):
        result = self.analyzer.analyze_city("深圳")
        costs = result["business_costs"]
        assert costs["total_cost_score"] > 0
        assert "components" in costs
        assert len(costs["components"]) > 0

    def test_supply_chain_from_real_data(self):
        result = self.analyzer.analyze_city("深圳")
        sc = result["supply_chain"]
        assert sc["supply_chain_score"] > 0
        assert "components" in sc

    def test_policy_benefits_from_real_data(self):
        result = self.analyzer.analyze_city("深圳")
        pb = result["policy_benefits"]
        assert pb["policy_benefit_score"] > 0
        assert "components" in pb

    def test_run_full_analysis_with_city_name(self):
        result = self.analyzer.run_full_analysis("深圳")
        assert isinstance(result, dict)
        assert "overall_score" in result

    def test_predict_with_city_name(self):
        result = self.analyzer.predict("深圳")
        assert isinstance(result, dict)
        assert "overall_score" in result

    def test_run_full_analysis_with_dict(self):
        data = get_city_data("深圳")
        result = self.analyzer.run_full_analysis(data)
        assert isinstance(result, dict)
        assert "overall_score" in result


class TestGovernmentAnalyzerRealData:

    def setup_method(self):
        self.analyzer = GovernmentAnalyzer()

    def test_analyze_city_with_real_data(self):
        result = self.analyzer.analyze_city("深圳")
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert result["overall_score"] > 0

    def test_fiscal_leverage_from_real_data(self):
        result = self.analyzer.analyze_city("深圳")
        fl = result["fiscal_leverage"]
        assert fl["fiscal_leverage_score"] > 0
        assert "components" in fl

    def test_industry_driving_from_real_data(self):
        result = self.analyzer.analyze_city("深圳")
        id_ = result["industry_driving"]
        assert id_["driving_score"] > 0
        assert "components" in id_

    def test_industry_chain_from_real_data(self):
        result = self.analyzer.analyze_city("深圳")
        ic = result["industry_chain"]
        assert ic["chain_completeness_score"] > 0

    def test_scores_differ_between_cities(self):
        result_sz = self.analyzer.analyze_city("深圳")
        result_cd = self.analyzer.analyze_city("成都")
        assert result_sz["overall_score"] != result_cd["overall_score"]

    def test_run_full_analysis_with_city_name(self):
        result = self.analyzer.run_full_analysis("深圳")
        assert isinstance(result, dict)
        assert "overall_score" in result

    def test_predict_with_city_name(self):
        result = self.analyzer.predict("深圳")
        assert isinstance(result, dict)
        assert "overall_score" in result


class TestRetailLocationAnalyzerFullFlow:

    def setup_method(self):
        self.analyzer = RetailLocationAnalyzer()

    def test_full_flow_generate_train_predict(self, tmp_path):
        data = RetailDataAdapter.generate_sample_data(num_stores=60, random_seed=42)
        result = self.analyzer.run_full_analysis(
            data,
            save_results=True,
            output_dir=str(tmp_path / "retail_output")
        )
        assert isinstance(result, dict)
        assert "training_result" in result
        assert result["training_result"]["best_score"] > 0

    def test_predict_after_training(self, tmp_path):
        data = RetailDataAdapter.generate_sample_data(num_stores=60, random_seed=42)
        self.analyzer.run_full_analysis(
            data,
            save_results=False,
            output_dir=str(tmp_path / "retail_output")
        )
        new_data = RetailDataAdapter.generate_sample_data(num_stores=5, random_seed=99)
        predictions = self.analyzer.predict(new_data)
        assert isinstance(predictions, pd.DataFrame)
        assert "predicted_sales" in predictions.columns
        assert len(predictions) == 5


class TestSalesForecastAnalyzerFullFlow:

    def setup_method(self):
        self.analyzer = SalesForecastAnalyzer()

    def test_full_flow_generate_train_predict(self, tmp_path):
        adapter = SalesDataAdapter()
        data = adapter.generate_sample_data(num_records=200, num_products=5)
        result = self.analyzer.run_full_analysis(
            data,
            save_results=True,
            output_dir=str(tmp_path / "sales_output")
        )
        assert isinstance(result, dict)
        assert "training_result" in result
        assert result["training_result"]["best_score"] is not None

    def test_predict_after_training(self, tmp_path):
        adapter = SalesDataAdapter()
        data = adapter.generate_sample_data(num_records=200, num_products=5)
        self.analyzer.run_full_analysis(
            data,
            save_results=False,
            output_dir=str(tmp_path / "sales_output")
        )
        new_data = adapter.generate_sample_data(num_records=10, num_products=3)
        predictions = self.analyzer.predict(new_data)
        assert isinstance(predictions, pd.DataFrame)
        assert "predicted_sales" in predictions.columns


class TestDifferentCitiesDifferentScores:

    def test_enterprise_different_cities(self):
        analyzer = EnterpriseAnalyzer()
        cities = get_all_cities()
        scores = {}
        for city in cities:
            result = analyzer.analyze_city(city)
            scores[city] = result["overall_score"]
        assert len(set(scores.values())) > 1, "All cities have the same enterprise score"

    def test_government_different_cities(self):
        analyzer = GovernmentAnalyzer()
        cities = get_all_cities()
        scores = {}
        for city in cities:
            result = analyzer.analyze_city(city)
            scores[city] = result["overall_score"]
        assert len(set(scores.values())) > 1, "All cities have the same government score"

    def test_enterprise_compare_cities(self):
        analyzer = EnterpriseAnalyzer()
        comparison = analyzer.compare_cities()
        assert len(comparison) > 1
        scores = [c["overall_score"] for c in comparison]
        assert len(set(scores)) > 1

    def test_government_compare_cities(self):
        analyzer = GovernmentAnalyzer()
        comparison = analyzer.compare_cities()
        assert len(comparison) > 1
        scores = [c["overall_score"] for c in comparison]
        assert len(set(scores)) > 1
