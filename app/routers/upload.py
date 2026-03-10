from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, File, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services import data_loader, analysis

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

    summary_by_type = analysis.basic_groupby(df, "물건유형")
    summary_by_region: Optional[pd.DataFrame] = None
    for col in ["지역", "물건지 주소"]:
        if col in df.columns:
            summary_by_region = analysis.basic_groupby(df, col)
            break

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
        },
    )

