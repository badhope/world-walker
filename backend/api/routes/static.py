"""
静态文件和图表服务API
"""

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1/static", tags=["静态文件"])

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CHARTS_DIR = PROJECT_ROOT / "data" / "charts"

# 仅允许常见图片扩展名 + 单层子目录字母数字
_ALLOWED_FILENAME = re.compile(r"^[A-Za-z0-9_./-]+$")


def safe_chart_path(filename: str) -> Path:
    """把用户传入的 chart 文件名解析到 CHARTS_DIR 内的安全绝对路径。

    防御路径穿越: 拒绝 .., 绝对路径, 反斜杠, 空名, 隐藏文件, 不在白名单的字符。
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("filename must be a non-empty string")
    if "\\" in filename:
        raise ValueError("backslash is not allowed in filename")
    if filename.startswith("/") or filename.startswith("~"):
        raise ValueError("absolute paths are not allowed")
    if not _ALLOWED_FILENAME.match(filename):
        raise ValueError("filename contains disallowed characters")
    # 取 basename 拒隐藏文件, 但允许合法子目录
    parts = filename.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise ValueError("invalid path segment")
    if any(p.startswith(".") for p in parts):
        raise ValueError("hidden file names are not allowed")

    charts_root = CHARTS_DIR.resolve()
    candidate = (CHARTS_DIR / filename).resolve()
    # 严格沙箱:解析后必须仍在 CHARTS_DIR 之内(防 symlink 等绕过)
    try:
        candidate.relative_to(charts_root)
    except ValueError as exc:
        raise ValueError("resolved path escapes CHARTS_DIR") from exc
    return candidate


@router.get("/charts/{filename}")
async def get_chart(filename: str):
    """获取分析图表"""
    try:
        file_path = safe_chart_path(filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="图表未找到")
    return FileResponse(file_path, media_type="image/png")


@router.get("/charts/list")
async def list_charts():
    """列出所有可用图表"""
    try:
        charts = []
        if CHARTS_DIR.exists():
            for file in CHARTS_DIR.glob("*.png"):
                charts.append({"filename": file.name, "url": f"/api/v1/static/charts/{file.name}"})
        return {"status": "success", "charts": charts}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
