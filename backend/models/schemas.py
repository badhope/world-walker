"""
Pydantic 数据模型
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DataSourceEnum(StrEnum):
    MOF = "mof"  # 财政部
    NBS = "nbs"  # 国家统计局
    CUSTOMS = "customs"  # 海关
    PBC = "pbc"  # 央行
    AKSHARE = "akshare"  # AKShare数据源
    USER = "user"  # 用户输入


class IndicatorCategoryEnum(StrEnum):
    FISCAL = "fiscal"  # 财政
    GDP = "gdp"  # GDP
    PRICE = "price"  # 价格
    EMPLOYMENT = "employment"  # 就业
    POPULATION = "population"  # 人口
    REGIONAL = "regional"  # 区域
    FINANCIAL = "financial"  # 金融
    TRADE = "trade"  # 贸易
    INCOME = "income"  # 收入
    INDUSTRY = "industry"  # 产业


# Indicator models
class IndicatorBase(BaseModel):
    code: str = Field(..., description="指标代码")
    name: str = Field(..., description="指标名称")
    value: float = Field(..., description="数值")
    unit: str | None = Field(None, description="单位")
    year: int = Field(..., description="年份")
    month: int | None = Field(None, description="月份")
    quarter: int | None = Field(None, description="季度")
    region: str | None = Field(None, description="地区")
    category: str = Field(..., description="类别")
    source: str = Field(..., description="数据来源")


class IndicatorCreate(IndicatorBase):
    pass


class Indicator(IndicatorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IndicatorBatchCreate(BaseModel):
    indicators: list[IndicatorCreate]


class IndicatorResponse(BaseModel):
    data: list[Indicator]
    total: int
    page: int
    page_size: int


# Inference models
class InferenceMethod(StrEnum):
    LINEAR = "linear"  # 线性推演
    REGRESSION = "regression"  # 回归分析
    TIME_SERIES = "time_series"  # 时间序列
    MONTE_CARLO = "monte_carlo"  # 蒙特卡洛


class InferenceRequest(BaseModel):
    input_indicators: dict[str, float] = Field(..., description="输入指标及数值")
    target_indicator: str = Field(..., description="目标推算指标")
    method: InferenceMethod = Field(InferenceMethod.LINEAR, description="推算方法")
    confidence_level: float = Field(0.95, description="置信水平", ge=0.8, le=0.99)


class InferenceResponse(BaseModel):
    predicted_value: float = Field(..., description="预测值")
    predicted_unit: str = Field(..., description="单位")
    confidence_interval: tuple[float, float] = Field(..., description="置信区间")
    method_used: str = Field(..., description="使用的方法")
    r_squared: float | None = Field(None, description="R²拟合优度")
    input_indicators: dict[str, float] = Field(..., description="输入指标")
    target_indicator: str = Field(..., description="目标指标")
    timestamp: datetime = Field(default_factory=datetime.now)


class BatchInferenceItem(BaseModel):
    input_indicators: dict[str, float]
    target_indicator: str
    method: InferenceMethod = InferenceMethod.LINEAR


class BatchInferenceRequest(BaseModel):
    items: list[BatchInferenceItem]


# Data collection models


class ScrapeRequest(BaseModel):
    source: DataSourceEnum = Field(..., description="数据源")
    indicator_codes: list[str] | None = Field(None, description="指标代码列表，为空则采集全部")
    start_year: int | None = Field(None, description="起始年份")
    end_year: int | None = Field(None, description="结束年份")


class ScrapeResponse(BaseModel):
    status: str = Field(..., description="状态")
    source: str = Field(..., description="数据源")
    records_fetched: int = Field(..., description="获取记录数")
    indicators: list[str] = Field(default=[], description="采集的指标列表")
    errors: list[str] = Field(default=[], description="错误列表")
    timestamp: datetime = Field(default_factory=datetime.now)


# User models
class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    role: str
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


# Generic responses


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    cache: str
    timestamp: datetime


class MessageResponse(BaseModel):
    message: str
    detail: str | None = None
