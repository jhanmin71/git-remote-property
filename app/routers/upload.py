from pathlib import Path
from typing import Optional
import asyncio

import pandas as pd
from fastapi import APIRouter, File, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services import data_loader, analysis, auction_finder

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

router = APIRouter()


@router.post("/excel", response_class=HTMLResponse)
async def upload_excel(
    request: Request,
    file: UploadFile = File(..., description="부동산 물건 엑셀 파일"),
):
    upload_dir = BASE_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_path = upload_dir / file.filename
    content = await file.read()
    saved_path.write_bytes(content)

    df = data_loader.load_excel(saved_path)

    # 물건유형 기준 요약
    summary_by_type = analysis.basic_groupby(df, "물건유형")

    # 지역 = 주소1 + 주소2 결합 컬럼 생성 후 지역 기준 요약
    summary_by_region: Optional[pd.DataFrame] = None
    if "주소1" in df.columns and "주소2" in df.columns:
        df = df.copy()
        df["지역"] = df["주소1"].astype(str).str.strip() + " " + df["주소2"].astype(str).str.strip()
        summary_by_region = analysis.basic_groupby(df, "지역")

    # 경매현황 조회 (비동기)
    auction_info: Optional[pd.DataFrame] = None
    try:
        auction_info = await auction_finder.get_auction_info(df)
    except Exception as e:
        print(f"경매현황 조회 중 오류: {str(e)}")
        auction_info = None

    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "filename": file.filename,
            "summary_by_type": summary_by_type.to_dict(orient="records")
            if summary_by_type is not None
            else None,
            "summary_by_region": summary_by_region.to_dict(orient="records")
            if summary_by_region is not None
            else None,
            "auction_info": auction_info.to_dict(orient="records")
            if auction_info is not None
            else None,
        },
    )

