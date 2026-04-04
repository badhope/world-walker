"""
数据采集 API 路由
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List
from datetime import datetime
import logging

from backend.models.schemas import ScrapeRequest, ScrapeResponse
from backend.services.data_fetcher import fetcher
from backend.core.database import SessionLocal, EconomicIndicator, init_db

router = APIRouter(prefix="/scrape", tags=["数据采集"])
logger = logging.getLogger(__name__)


# 采集状态缓存
_scrape_status = {
    "last_run": None,
    "is_running": False,
    "last_result": None
}


@router.post("/", response_model=ScrapeResponse, summary="采集数据")
def scrape_data(request: ScrapeRequest):
    """
    从指定数据源采集经济数据
    
    支持的数据源:
    - nbs: 国家统计局 (GDP, CPI, PPI, PMI等)
    - pbc: 人民银行 (M0, M1, M2等)
    - customs: 海关总署 (进出口数据)
    - mof: 财政部 (财政收入支出)
    """
    if _scrape_status["is_running"]:
        raise HTTPException(status_code=409, detail="已有采集任务在运行")
    
    _scrape_status["is_running"] = True
    
    try:
        # 确保数据库表存在
        init_db()
        
        # 获取数据
        data = fetcher.fetch_all()
        
        # 统计
        total_records = 0
        all_indicators = []
        errors = []
        
        # 保存到数据库
        db = SessionLocal()
        try:
            for category, records in data.items():
                total_records += len(records)
                
                for record in records:
                    all_indicators.append(record["code"])
                    
                    # 检查是否已存在
                    existing = db.query(EconomicIndicator).filter(
                        EconomicIndicator.code == record["code"],
                        EconomicIndicator.year == record["year"],
                        EconomicIndicator.month == record.get("month"),
                        EconomicIndicator.quarter == record.get("quarter")
                    ).first()
                    
                    if not existing:
                        db_indicator = EconomicIndicator(
                            code=record["code"],
                            name=record["name"],
                            value=record["value"],
                            unit=record.get("unit"),
                            year=record["year"],
                            month=record.get("month"),
                            quarter=record.get("quarter"),
                            region=record.get("region"),
                            category=record.get("category"),
                            source=record.get("source")
                        )
                        db.add(db_indicator)
            
            db.commit()
            logger.info(f"保存 {total_records} 条记录到数据库")
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            errors.append(str(e))
            db.rollback()
        finally:
            db.close()
        
        _scrape_status["last_run"] = datetime.now()
        _scrape_status["last_result"] = {
            "records": total_records,
            "indicators": list(set(all_indicators))
        }
        
        return ScrapeResponse(
            status="success",
            source=request.source.value,
            records_fetched=total_records,
            indicators=list(set(all_indicators)),
            errors=errors
        )
    
    except Exception as e:
        logger.error(f"采集失败: {e}")
        return ScrapeResponse(
            status="error",
            source=request.source.value,
            records_fetched=0,
            errors=[str(e)]
        )
    
    finally:
        _scrape_status["is_running"] = False


@router.get("/status", summary="获取采集状态")
def get_scrape_status():
    """获取数据采集状态"""
    return {
        "is_running": _scrape_status["is_running"],
        "last_run": _scrape_status["last_run"],
        "last_result": _scrape_status["last_result"]
    }


@router.get("/sources", summary="获取可用数据源")
def list_sources():
    """获取所有可用的数据源"""
    return {
        "sources": [
            {
                "code": "nbs",
                "name": "国家统计局",
                "indicators": ["GDP", "CPI", "PPI", "PMI", "就业", "人口"],
                "url": "https://data.stats.gov.cn"
            },
            {
                "code": "pbc",
                "name": "中国人民银行",
                "indicators": ["M0", "M1", "M2", "社会融资规模", "利率"],
                "url": "http://www.pbc.gov.cn"
            },
            {
                "code": "customs",
                "name": "海关总署",
                "indicators": ["进出口总额", "贸易顺差"],
                "url": "http://www.customs.gov.cn"
            },
            {
                "code": "mof",
                "name": "财政部",
                "indicators": ["财政收入", "财政支出", "赤字"],
                "url": "http://www.mof.gov.cn"
            }
        ]
    }
