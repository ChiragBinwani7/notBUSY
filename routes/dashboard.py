"""Dashboard routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from services.dashboard_service import DashboardService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard home page."""
    data = DashboardService.get_dashboard_data(db)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "data": data
    })
