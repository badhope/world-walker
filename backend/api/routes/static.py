"""
静态文件和图表服务API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os

router = APIRouter(prefix="/api/v1/static", tags=["静态文件"])

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CHARTS_DIR = PROJECT_ROOT / "data" / "charts"

@router.get("/charts/{filename}")
async def get_chart(filename: str):
    """获取分析图表"""
    try:
        file_path = CHARTS_DIR / filename
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="图表未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表失败: {str(e)}")

@router.get("/charts/list")
async def list_charts():
    """列出所有可用图表"""
    try:
        charts = []
        if CHARTS_DIR.exists():
            for file in CHARTS_DIR.glob("*.png"):
                charts.append({
                    "filename": file.name,
                    "url": f"/api/v1/static/charts/{file.name}"
                })
        return {"status": "success", "charts": charts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表列表失败: {str(e)}")
