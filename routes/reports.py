"""Reports routes: Day Book, Outstanding Receivables, P&L Summary."""

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from services.reports_service import ReportsService
from datetime import datetime, timedelta

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def reports_index(request: Request):
    """Reports landing page."""
    now = datetime.utcnow()
    return templates.TemplateResponse("reports/index.html", {
        "request": request,
        "current_year": now.year,
        "current_month": now.month,
        "today": now.strftime("%Y-%m-%d"),
        "month_start": now.replace(day=1).strftime("%Y-%m-%d"),
    })


@router.get("/daybook", response_class=HTMLResponse)
async def day_book(
    request: Request,
    from_date: str = Query(default=None),
    to_date: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """Day Book – all transactions in a date range."""
    now = datetime.utcnow()
    if from_date:
        fd = datetime.strptime(from_date, "%Y-%m-%d")
    else:
        fd = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if to_date:
        td = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    else:
        td = now

    data = ReportsService.get_day_book(db, fd, td)
    return templates.TemplateResponse("reports/daybook.html", {
        "request": request,
        "data": data,
        "from_date": fd.strftime("%Y-%m-%d"),
        "to_date": td.strftime("%Y-%m-%d"),
    })


@router.get("/outstanding", response_class=HTMLResponse)
async def outstanding_receivables(request: Request, db: Session = Depends(get_db)):
    """Outstanding Receivables with aging analysis."""
    data = ReportsService.get_outstanding_receivables(db)
    return templates.TemplateResponse("reports/outstanding.html", {
        "request": request,
        "data": data,
    })


@router.get("/pnl", response_class=HTMLResponse)
async def pnl_report(
    request: Request,
    from_date: str = Query(default=None),
    to_date: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """Profit & Loss summary for a date range."""
    now = datetime.utcnow()
    if from_date:
        fd = datetime.strptime(from_date, "%Y-%m-%d")
    else:
        fd = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    if to_date:
        td = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    else:
        td = now

    data = ReportsService.get_pnl_summary(db, fd, td)
    return templates.TemplateResponse("reports/pnl.html", {
        "request": request,
        "data": data,
        "from_date": fd.strftime("%Y-%m-%d"),
        "to_date": td.strftime("%Y-%m-%d"),
    })
