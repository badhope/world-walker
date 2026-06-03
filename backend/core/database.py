"""
数据库管理
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.settings import settings

# 创建引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class EconomicIndicator(Base):
    """经济指标数据表"""

    __tablename__ = "economic_indicators"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), index=True, nullable=False)  # 指标代码
    name = Column(String(200), nullable=False)  # 指标名称
    value = Column(Float, nullable=False)  # 数值
    unit = Column(String(50))  # 单位
    year = Column(Integer, index=True)  # 年份
    month = Column(Integer, nullable=True)  # 月份
    quarter = Column(Integer, nullable=True)  # 季度
    region = Column(String(100), nullable=True)  # 地区
    category = Column(String(50), index=True)  # 类别
    source = Column(String(50))  # 数据来源
    remark = Column(Text, nullable=True)  # 备注
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    role = Column(String(20), default="user")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)
