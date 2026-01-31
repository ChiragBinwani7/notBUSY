"""GST report routes."""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from services.gst_service import GSTService
from datetime import datetime

router = APIRouter(prefix="/gst", tags=["gst"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def gst_reports(request: Request, db: Session = Depends(get_db)):
    """GST reports page."""
    now = datetime.now()
    return templates.TemplateResponse("gst/reports.html", {
        "request": request,
        "current_year": now.year,
        "current_month": now.month
    })

@router.get("/gstr1/{year}/{month}", response_class=HTMLResponse)
async def gstr1_report(request: Request, year: int, month: int, db: Session = Depends(get_db)):
    """GSTR-1 sales report."""
    transactions = GSTService.get_monthly_sales_gst(db, year, month)
    return templates.TemplateResponse("gst/gstr1.html", {
        "request": request,
        "year": year,
        "month": month,
        "transactions": transactions
    })

@router.get("/purchases/{year}/{month}", response_class=HTMLResponse)
async def purchase_gst_report(request: Request, year: int, month: int, db: Session = Depends(get_db)):
    """Purchase GST report with separate sections."""
    purchases = GSTService.get_monthly_purchase_gst(db, year, month)
    return templates.TemplateResponse("gst/purchases.html", {
        "request": request,
        "year": year,
        "month": month,
        "grey_purchases": purchases["grey_purchases"],
        "mill_jobs": purchases["mill_jobs"]
    })

@router.get("/gstr3b/{year}/{month}", response_class=HTMLResponse)
async def gstr3b_report(request: Request, year: int, month: int, db: Session = Depends(get_db)):
    """GSTR-3B summary report."""
    summary = GSTService.get_gstr3b_summary(db, year, month)
    return templates.TemplateResponse("gst/gstr3b.html", {
        "request": request,
        "year": year,
        "month": month,
        "summary": summary
    })

@router.get("/export/{year}/{month}")
async def export_gst_excel(year: int, month: int, db: Session = Depends(get_db)):
    """Export GST reports to Excel."""
    filepath = GSTService.export_to_excel(db, year, month)
    return FileResponse(
        path=filepath,
        filename=f"GST_Report_{year}_{month:02d}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
