from pathlib import Path
from typing import Optional
import asyncio
import json
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
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

    # 그래프 생성
    region_chart_html = None
    price_chart_html = None
    type_chart_html = None
    histogram_chart_html = None
    boxplot_chart_html = None
    type_price_chart_html = None
    region_pyeong_chart_html = None
    heatmap_chart_html = None
    missing_chart_html = None
    statistics = None
    outliers = None
    
    if "지역" in df.columns:
        region_chart_html = analysis.create_region_chart(df)
        price_chart_html = analysis.create_price_by_region_chart(df)
        region_pyeong_chart_html = analysis.create_region_pyeong_comparison(df)
    
    if "물건유형" in df.columns:
        type_chart_html = analysis.create_type_pie_chart(df)
        type_price_chart_html = analysis.create_type_price_comparison(df)
    
    # 수치 데이터 분석
    histogram_chart_html = analysis.create_histogram_chart(df)
    boxplot_chart_html = analysis.create_boxplot_chart(df)
    heatmap_chart_html = analysis.create_heatmap_chart(df)
    missing_chart_html = analysis.create_missing_data_chart(df)
    
    # 통계 요약 및 이상치 탐지
    statistics = analysis.get_statistics_summary(df)
    outliers = analysis.detect_outliers(df)

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
            "region_chart": region_chart_html,
            "price_chart": price_chart_html,
            "type_chart": type_chart_html,
            "histogram_chart": histogram_chart_html,
            "boxplot_chart": boxplot_chart_html,
            "type_price_chart": type_price_chart_html,
            "region_pyeong_chart": region_pyeong_chart_html,
            "heatmap_chart": heatmap_chart_html,
            "missing_chart": missing_chart_html,
            "statistics": statistics,
            "outliers": outliers,
        },
    )


@router.post("/export-excel")
async def export_excel(request: Request):
    """분석 결과를 엑셀로 내보내기"""
    body = await request.json()
    
    filename = body.get("filename", "report")
    summary_by_type = body.get("summary_by_type")
    summary_by_region = body.get("summary_by_region")
    auction_info = body.get("auction_info")
    
    # 엑셀 파일 생성
    with BytesIO() as output:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 경매현황
            if auction_info:
                auction_df = pd.DataFrame(auction_info)
                auction_df.to_excel(writer, sheet_name='경매현황', index=False)
            
            # 물건유형별 요약
            if summary_by_type:
                type_df = pd.DataFrame(summary_by_type)
                type_df.to_excel(writer, sheet_name='물건유형별', index=False)
            
            # 지역별 요약
            if summary_by_region:
                region_df = pd.DataFrame(summary_by_region)
                region_df.to_excel(writer, sheet_name='지역별', index=False)
        
        output.seek(0)
        excel_data = output.getvalue()
    
    return FileResponse(
        BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"분석결과_{filename.replace('.xlsx', '')}.xlsx"
    )

