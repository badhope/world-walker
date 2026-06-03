"""
网络爬虫数据采集器 - 使用 requests + BeautifulSoup 获取真实经济数据
"""

import json
import logging
import re
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from backend.data_collection.base_collector import BaseCollector
from config import config_loader

logger = logging.getLogger(__name__)


class WebCrawler(BaseCollector):
    """网络爬虫数据采集器"""

    def __init__(self):
        super().__init__()
        self.source_name = "web_crawler"
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.ua.random,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )

        self.analysis_config = config_loader.get_analysis_config()
        self.default_years = self.analysis_config.DATA_COLLECTION["years_range"]

    def fetch_data(self, **kwargs) -> list[dict[str, Any]]:
        """
        采集数据

        Args:
            **kwargs: indicator - 指标名称

        Returns:
            数据列表
        """
        indicator = kwargs.get("indicator", "gdp")

        fetch_methods = {
            "gdp": self.crawl_gdp_data,
            "cpi": self.crawl_cpi_data,
            "fiscal": self.crawl_fiscal_data,
            "industry": self.crawl_industry_data,
            "labor": self.crawl_labor_data,
            "semiconductor": self.crawl_semiconductor_data,
        }

        if indicator in fetch_methods:
            return fetch_methods[indicator]()

        logger.warning(f"未知指标: {indicator}")
        return []

    def crawl_gdp_data(self) -> list[dict[str, Any]]:
        """爬取 GDP 数据"""
        results = []
        try:
            sources = [
                self._crawl_gdp_from_nbs,
                self._crawl_gdp_from_wiki,
                self._crawl_gdp_from_statista,
            ]

            for source_func in sources:
                try:
                    data = source_func()
                    results.extend(data)
                except Exception as e:
                    logger.warning(f"数据源失败: {source_func.__name__}, 错误: {e}")

            if not results:
                results = self._generate_simulated_gdp_data()

            logger.info(f"爬取 GDP 数据: {len(results)} 条")
            return results

        except Exception as e:
            logger.error(f"爬取 GDP 失败: {e}")
            return self._generate_simulated_gdp_data()

    def _crawl_gdp_from_nbs(self) -> list[dict[str, Any]]:
        """从国家统计局网站爬取GDP数据"""
        results = []
        try:
            url = "http://www.stats.gov.cn/tjsj/zxfb/202501/t20250117_1922560.html"
            response = self.session.get(url, timeout=15)
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            tables = soup.find_all("table")

            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        try:
                            year_str = cols[0].get_text(strip=True)
                            if year_str and year_str.isdigit():
                                year = int(year_str)
                                if year >= 2020:
                                    value = float(cols[1].get_text(strip=True).replace(",", ""))
                                    results.append(
                                        {
                                            "code": "gdp",
                                            "name": "国内生产总值",
                                            "value": value,
                                            "unit": "亿元",
                                            "year": year,
                                            "source": "nbs",
                                            "timestamp": datetime.now().isoformat(),
                                        }
                                    )
                        except Exception as e:
                            logger.debug(f"解析NBS表格行失败: {e}")
                            continue
        except Exception as e:
            logger.debug(f"NBS GDP爬取失败: {e}")
        return results

    def _crawl_gdp_from_wiki(self) -> list[dict[str, Any]]:
        """从维基百科爬取GDP数据"""
        results = []
        try:
            url = "https://zh.wikipedia.org/zh-cn/%E4%B8%AD%E5%9B%BD%E5%9B%BD%E5%86%85%E7%94%9F%E4%BA%A7%E6%80%BB%E5%80%BC"
            response = self.session.get(url, timeout=15)
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            tables = soup.find_all("table", class_="wikitable")

            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        try:
                            year_str = cols[0].get_text(strip=True)
                            if year_str and year_str.isdigit():
                                year = int(year_str)
                                if year >= 2020:
                                    value_str = cols[1].get_text(strip=True).replace(",", "")
                                    if value_str and value_str.replace(".", "").isdigit():
                                        value = float(value_str)
                                        results.append(
                                            {
                                                "code": "gdp",
                                                "name": "国内生产总值",
                                                "value": value,
                                                "unit": "亿元",
                                                "year": year,
                                                "source": "wikipedia",
                                                "timestamp": datetime.now().isoformat(),
                                            }
                                        )
                        except Exception as e:
                            logger.debug(f"解析wiki表格行失败: {e}")
                            continue
        except Exception as e:
            logger.debug(f"wiki GDP爬取失败: {e}")
        return results

    def _crawl_gdp_from_statista(self) -> list[dict[str, Any]]:
        """从Statista爬取GDP数据"""
        results = []
        try:
            url = "https://www.statista.com/statistics/263630/gross-domestic-product-gdp-china/"
            response = self.session.get(url, timeout=15)

            soup = BeautifulSoup(response.text, "html.parser")
            script_tags = soup.find_all("script", type="application/json")

            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if "chartData" in data:
                        for entry in data["chartData"]:
                            year = entry.get("year")
                            value = entry.get("value")
                            if year and value and year >= 2020:
                                results.append(
                                    {
                                        "code": "gdp",
                                        "name": "国内生产总值",
                                        "value": value,
                                        "unit": "亿元",
                                        "year": year,
                                        "source": "statista",
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )
                except Exception as e:
                    logger.debug(f"解析statista JSON失败: {e}")
                    continue
        except Exception as e:
            logger.debug(f"statista GDP爬取失败: {e}")
        return results

    def _generate_simulated_gdp_data(self) -> list[dict[str, Any]]:
        """生成模拟GDP数据"""
        results = []
        gdp_values = {2020: 1015986, 2021: 1149237, 2022: 1210207, 2023: 1260582, 2024: 1340000, 2025: 1420000}

        for year in self.default_years:
            if year in gdp_values:
                results.append(
                    {
                        "code": "gdp",
                        "name": "国内生产总值",
                        "value": gdp_values[year],
                        "unit": "亿元",
                        "year": year,
                        "source": "simulated",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results

    def crawl_cpi_data(self) -> list[dict[str, Any]]:
        """爬取 CPI 数据"""
        results = []
        try:
            url = "https://data.stats.gov.cn/easyquery.htm?cn=C01"
            response = self.session.get(url, timeout=15)
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            tables = soup.find_all("table")

            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        try:
                            date_str = cols[0].get_text(strip=True)
                            match = re.match(r"(\d{4})年(\d{1,2})月", date_str)
                            if match:
                                year = int(match.group(1))
                                month = int(match.group(2))
                                if year >= 2023:
                                    value = float(cols[1].get_text(strip=True))
                                    results.append(
                                        {
                                            "code": "cpi",
                                            "name": "居民消费价格指数",
                                            "value": value,
                                            "unit": "%",
                                            "year": year,
                                            "month": month,
                                            "source": "nbs",
                                            "timestamp": datetime.now().isoformat(),
                                        }
                                    )
                        except Exception as e:
                            logger.debug(f"解析CPI表格行失败: {e}")
                            continue

            if not results:
                results = self._generate_simulated_cpi_data()

            logger.info(f"爬取 CPI 数据: {len(results)} 条")
            return results

        except Exception as e:
            logger.error(f"爬取 CPI 失败: {e}")
            return self._generate_simulated_cpi_data()

    def _generate_simulated_cpi_data(self) -> list[dict[str, Any]]:
        """生成模拟CPI数据"""
        results = []
        monthly_cpi = {
            2024: [100.2, 100.8, 100.4, 100.1, 99.8, 100.1, 100.3, 100.5, 100.7, 100.9, 101.1, 101.3],
            2025: [101.5, 101.2, 101.0, 100.8, 100.6, 100.5, 100.7, 100.9, 101.1, 101.3, 101.5, 101.7],
        }

        for year, values in monthly_cpi.items():
            for month, value in enumerate(values, 1):
                results.append(
                    {
                        "code": "cpi",
                        "name": "居民消费价格指数",
                        "value": value,
                        "unit": "%",
                        "year": year,
                        "month": month,
                        "source": "simulated",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results

    def crawl_fiscal_data(self) -> list[dict[str, Any]]:
        """爬取财政数据"""
        results = []
        try:
            url = "http://yss.mof.gov.cn/zhuantilanmu/czjs/"
            response = self.session.get(url, timeout=15)
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a", href=True)

            for link in links:
                if "财政收支情况" in link.get_text():
                    try:
                        detail_url = "http://yss.mof.gov.cn" + link["href"]
                        detail_response = self.session.get(detail_url, timeout=10)
                        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

                        text = detail_soup.get_text()
                        fiscal_matches = re.findall(r"(\d{4})年.*财政收入.*?(\d+(?:\.\d+)?)\s*(亿元|万亿元)", text)
                        for year_str, value_str, unit in fiscal_matches:
                            try:
                                year = int(year_str)
                                value = float(value_str)
                                if unit == "万亿元":
                                    value *= 10000
                                if year >= 2020:
                                    results.append(
                                        {
                                            "code": "fiscal_revenue",
                                            "name": "财政收入",
                                            "value": value,
                                            "unit": "亿元",
                                            "year": year,
                                            "source": "mof",
                                            "timestamp": datetime.now().isoformat(),
                                        }
                                    )
                            except Exception as e:
                                logger.debug(f"解析MOF财政数据失败: {e}")
                                continue
                    except Exception as e:
                        logger.debug(f"MOF页面爬取失败: {e}")
                        continue

            if not results:
                results = self._generate_simulated_fiscal_data()

            logger.info(f"爬取财政数据: {len(results)} 条")
            return results

        except Exception as e:
            logger.error(f"爬取财政数据失败: {e}")
            return self._generate_simulated_fiscal_data()

    def _generate_simulated_fiscal_data(self) -> list[dict[str, Any]]:
        """生成模拟财政数据"""
        results = []
        fiscal_values = {2020: 182895, 2021: 202539, 2022: 203703, 2023: 218498, 2024: 235000, 2025: 252000}

        for year in self.default_years:
            if year in fiscal_values:
                results.append(
                    {
                        "code": "fiscal_revenue",
                        "name": "财政收入",
                        "value": fiscal_values[year],
                        "unit": "亿元",
                        "year": year,
                        "source": "simulated",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results

    def crawl_industry_data(self) -> list[dict[str, Any]]:
        """爬取工业数据"""
        results = []
        try:
            url = "https://www.miit.gov.cn/"
            response = self.session.get(url, timeout=15)
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            news_items = soup.find_all("a", href=True)

            for item in news_items:
                if "工业" in item.get_text() or "制造业" in item.get_text():
                    try:
                        detail_url = item["href"]
                        if not detail_url.startswith("http"):
                            detail_url = "https://www.miit.gov.cn" + detail_url

                        detail_response = self.session.get(detail_url, timeout=10)
                        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

                        text = detail_soup.get_text()
                        industry_matches = re.findall(r"(\d{4})年.*工业增加值.*?(\d+(?:\.\d+)?)\s*(%)", text)
                        for year_str, value_str in industry_matches:
                            try:
                                year = int(year_str)
                                value = float(value_str)
                                if year >= 2020:
                                    results.append(
                                        {
                                            "code": "industrial_value_added",
                                            "name": "工业增加值增速",
                                            "value": value,
                                            "unit": "%",
                                            "year": year,
                                            "source": "miit",
                                            "timestamp": datetime.now().isoformat(),
                                        }
                                    )
                            except Exception as e:
                                logger.debug(f"解析MIIT工业数据失败: {e}")
                                continue
                    except Exception as e:
                        logger.debug(f"MIIT页面爬取失败: {e}")
                        continue

            if not results:
                results = self._generate_simulated_industry_data()

            logger.info(f"爬取工业数据: {len(results)} 条")
            return results

        except Exception as e:
            logger.error(f"爬取工业数据失败: {e}")
            return self._generate_simulated_industry_data()

    def _generate_simulated_industry_data(self) -> list[dict[str, Any]]:
        """生成模拟工业数据"""
        results = []
        industry_values = {2020: 2.8, 2021: 9.6, 2022: 3.6, 2023: 4.6, 2024: 5.2, 2025: 5.5}

        for year in self.default_years:
            if year in industry_values:
                results.append(
                    {
                        "code": "industrial_value_added",
                        "name": "工业增加值增速",
                        "value": industry_values[year],
                        "unit": "%",
                        "year": year,
                        "source": "simulated",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results

    def crawl_labor_data(self) -> list[dict[str, Any]]:
        """爬取劳动力数据"""
        results = []
        try:
            url = "https://www.stats.gov.cn/tjsj/tjgb/ndtjgb/"
            response = self.session.get(url, timeout=15)
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a", href=True)

            for link in links:
                if "国民经济和社会发展统计公报" in link.get_text():
                    try:
                        detail_url = link["href"]
                        if not detail_url.startswith("http"):
                            detail_url = "https://www.stats.gov.cn" + detail_url

                        detail_response = self.session.get(detail_url, timeout=10)
                        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

                        text = detail_soup.get_text()
                        labor_matches = re.findall(r"城镇新增就业.*?(\d+(?:\.\d+)?)\s*万人", text)
                        for value_str in labor_matches:
                            try:
                                year_match = re.search(r"(\d{4})年", text)
                                year = int(year_match.group(1)) if year_match else 2024
                                value = float(value_str)
                                results.append(
                                    {
                                        "code": "urban_employment",
                                        "name": "城镇新增就业",
                                        "value": value,
                                        "unit": "万人",
                                        "year": year,
                                        "source": "nbs",
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )
                            except Exception as e:
                                logger.debug(f"解析NBS劳动力数据失败: {e}")
                                continue
                    except Exception as e:
                        logger.debug(f"NBS页面爬取失败: {e}")
                        continue

            if not results:
                results = self._generate_simulated_labor_data()

            logger.info(f"爬取劳动力数据: {len(results)} 条")
            return results

        except Exception as e:
            logger.error(f"爬取劳动力数据失败: {e}")
            return self._generate_simulated_labor_data()

    def _generate_simulated_labor_data(self) -> list[dict[str, Any]]:
        """生成模拟劳动力数据"""
        results = []
        labor_values = {2020: 1186, 2021: 1269, 2022: 1206, 2023: 1225, 2024: 1230, 2025: 1240}

        for year in self.default_years:
            if year in labor_values:
                results.append(
                    {
                        "code": "urban_employment",
                        "name": "城镇新增就业",
                        "value": labor_values[year],
                        "unit": "万人",
                        "year": year,
                        "source": "simulated",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results

    def crawl_semiconductor_data(self) -> list[dict[str, Any]]:
        """爬取半导体产业数据"""
        results = []
        try:
            urls = [
                "https://www.caam.org.cn/",
                "https://www.semiconductor.org.cn/",
                "https://www.ccidconsulting.com/",
            ]

            for url in urls:
                try:
                    response = self.session.get(url, timeout=15)
                    response.encoding = "utf-8"
                    soup = BeautifulSoup(response.text, "html.parser")

                    text = soup.get_text()
                    semi_matches = re.findall(r"半导体.*?产值.*?(\d+(?:\.\d+)?)\s*(亿元|万亿元)", text)
                    for value_str, unit in semi_matches:
                        try:
                            value = float(value_str)
                            if unit == "万亿元":
                                value *= 10000
                            results.append(
                                {
                                    "code": "semiconductor_output",
                                    "name": "半导体产业产值",
                                    "value": value,
                                    "unit": "亿元",
                                    "year": 2025,
                                    "source": url.split("/")[2],
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                        except Exception as e:
                            logger.debug(f"解析半导体数据失败: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"半导体页面爬取失败: {e}")
                    continue

            if not results:
                results = self._generate_simulated_semiconductor_data()

            logger.info(f"爬取半导体数据: {len(results)} 条")
            return results

        except Exception as e:
            logger.error(f"爬取半导体数据失败: {e}")
            return self._generate_simulated_semiconductor_data()

    def _generate_simulated_semiconductor_data(self) -> list[dict[str, Any]]:
        """生成模拟半导体数据"""
        results = []
        semi_values = {2020: 8400, 2021: 10458, 2022: 12490, 2023: 14500, 2024: 16800, 2025: 19500}

        for year in self.default_years:
            if year in semi_values:
                results.append(
                    {
                        "code": "semiconductor_output",
                        "name": "半导体产业产值",
                        "value": semi_values[year],
                        "unit": "亿元",
                        "year": year,
                        "source": "simulated",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results

    def fetch_all(self, indicators: list[str] | None = None) -> dict[str, list[dict]]:
        """
        批量采集所有数据

        Args:
            indicators: 指定采集的指标列表，None表示全部

        Returns:
            指标名到数据列表的映射
        """
        logger.info(f"批量采集数据，指标列表: {indicators}")

        all_indicators = ["gdp", "cpi", "fiscal", "industry", "labor", "semiconductor"]

        if indicators is None:
            indicators = all_indicators

        results = {}
        for indicator in indicators:
            if indicator in all_indicators:
                try:
                    data = self.fetch_data(indicator=indicator)
                    results[indicator] = data
                    logger.info(f"成功采集 {indicator}: {len(data)} 条")
                except Exception as e:
                    logger.error(f"采集 {indicator} 失败: {e}")
                    results[indicator] = []

        return results
