import warnings

warnings.filterwarnings("ignore")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd

from backend.data.city_data import (
    compare_cities,
    get_all_cities,
    get_city_data,
    get_historical_data,
    get_score_benchmarks,
    get_score_weights,
)


class TestGetCityData:
    def test_returns_dict_for_valid_city(self):
        result = get_city_data("深圳")
        assert isinstance(result, dict)

    def test_returns_none_for_invalid_city(self):
        result = get_city_data("不存在的城市")
        assert result is None

    def test_contains_key_fields(self):
        result = get_city_data("深圳")
        assert "land_price" in result
        assert "salary_level" in result
        assert "gdp" in result
        assert "year" in result

    def test_data_values_are_numeric(self):
        result = get_city_data("深圳")
        for key in ["land_price", "salary_level", "energy_cost", "gdp"]:
            assert isinstance(result[key], (int, float))

    def test_all_cities_have_data(self):
        for city in get_all_cities():
            data = get_city_data(city)
            assert data is not None, f"No data for city: {city}"
            assert len(data) > 0

    def test_shanghai_data(self):
        result = get_city_data("上海")
        assert result is not None
        assert result["gdp"] > 0

    def test_chengdu_data(self):
        result = get_city_data("成都")
        assert result is not None
        assert result["gdp"] > 0


class TestGetAllCities:
    def test_returns_list(self):
        result = get_all_cities()
        assert isinstance(result, list)

    def test_contains_expected_cities(self):
        result = get_all_cities()
        assert "深圳" in result
        assert "上海" in result
        assert "成都" in result

    def test_at_least_three_cities(self):
        result = get_all_cities()
        assert len(result) >= 3

    def test_no_duplicates(self):
        result = get_all_cities()
        assert len(result) == len(set(result))


class TestGetHistoricalData:
    def test_returns_dataframe(self):
        result = get_historical_data("深圳")
        assert isinstance(result, pd.DataFrame)

    def test_dataframe_not_empty(self):
        result = get_historical_data("深圳")
        assert len(result) > 0

    def test_has_year_column(self):
        result = get_historical_data("深圳")
        assert "year" in result.columns

    def test_has_gdp_column(self):
        result = get_historical_data("深圳")
        assert "gdp" in result.columns

    def test_multiple_years(self):
        result = get_historical_data("深圳")
        assert len(result) >= 5

    def test_invalid_city_returns_empty(self):
        result = get_historical_data("不存在的城市")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_all_cities_have_historical_data(self):
        for city in get_all_cities():
            result = get_historical_data(city)
            assert len(result) > 0, f"No historical data for {city}"


class TestCompareCities:
    def test_returns_dataframe(self):
        result = compare_cities(["深圳", "上海"])
        assert isinstance(result, pd.DataFrame)

    def test_correct_number_of_rows(self):
        result = compare_cities(["深圳", "上海", "成都"])
        assert len(result) == 3

    def test_has_city_column(self):
        result = compare_cities(["深圳", "上海"])
        assert "name" in result.columns

    def test_has_key_metrics(self):
        result = compare_cities(["深圳", "上海"])
        assert "gdp" in result.columns
        assert "land_price" in result.columns

    def test_empty_list_returns_empty_df(self):
        result = compare_cities([])
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_invalid_city_skipped(self):
        result = compare_cities(["深圳", "不存在的城市"])
        assert len(result) == 1

    def test_all_cities_comparison(self):
        result = compare_cities(get_all_cities())
        assert len(result) == len(get_all_cities())


class TestGetScoreBenchmarks:
    def test_returns_dict(self):
        result = get_score_benchmarks()
        assert isinstance(result, dict)

    def test_benchmarks_have_low_medium_high(self):
        result = get_score_benchmarks()
        for metric, bench in result.items():
            assert "low" in bench, f"Missing 'low' in {metric}"
            assert "medium" in bench, f"Missing 'medium' in {metric}"
            assert "high" in bench, f"Missing 'high' in {metric}"

    def test_benchmarks_ordering(self):
        result = get_score_benchmarks()
        for metric, bench in result.items():
            assert bench["low"] <= bench["medium"], f"low > medium for {metric}"
            assert bench["medium"] <= bench["high"], f"medium > high for {metric}"

    def test_benchmarks_computed_from_real_data(self):
        result = get_score_benchmarks()
        assert len(result) > 0
        assert "land_price" in result
        assert "salary_level" in result

    def test_benchmark_values_are_floats(self):
        result = get_score_benchmarks()
        for metric, bench in result.items():
            for key in ["low", "medium", "high"]:
                assert isinstance(bench[key], float), f"{metric}.{key} is not float"


class TestGetScoreWeights:
    def test_returns_dict(self):
        result = get_score_weights()
        assert isinstance(result, dict)

    def test_has_expected_keys(self):
        result = get_score_weights()
        assert "business_cost" in result
        assert "supply_chain" in result
        assert "policy_benefit" in result

    def test_weights_sum_to_one(self):
        result = get_score_weights()
        total = sum(result.values())
        assert abs(total - 1.0) < 1e-6, f"Weights sum to {total}, not 1.0"

    def test_weights_are_positive(self):
        result = get_score_weights()
        for key, val in result.items():
            assert val > 0, f"Weight for {key} is not positive"

    def test_weights_are_numeric(self):
        result = get_score_weights()
        for key, val in result.items():
            assert isinstance(val, (int, float))
