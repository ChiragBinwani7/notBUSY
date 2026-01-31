"""Mill job work routes."""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from services.mill_service import MillService
from services.inventory_service import InventoryService
from models.product import Product
from core.config import InventoryState

router = APIRouter(prefix="/mill", tags=["mill"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def list_mill_jobs(request: Request, db: Session = Depends(get_db)):
    """List all mill jobs."""
    mill_jobs = MillService.get_all_mill_jobs(db)
    return templates.TemplateResponse("mill/list.html", {
        "request": request,
        "mill_jobs": mill_jobs
    })

@router.get("/send", response_class=HTMLResponse)
async def send_to_mill_form(request: Request, db: Session = Depends(get_db)):
    """Show form to send grey to mill."""
    products = db.query(Product).all()
    # Get available grey inventory
    stock = InventoryService.get_stock_summary(db)
    return templates.TemplateResponse("mill/send_form.html", {
        "request": request,
        "products": products,
        "stock": stock
    })

@router.post("/send")
async def send_to_mill(
    mill_name: str = Form(...),
    product_id: int = Form(...),
    raw_category: str = Form(...),
    finished_variant: str = Form(...),
    grey_quantity: float = Form(...),
    db: Session = Depends(get_db)
):
    """Send grey to mill."""
    # Get grey batches for this product
    from models.inventory import InventoryBatch
    batches = db.query(InventoryBatch).filter(
        InventoryBatch.product_id == product_id,
        InventoryBatch.location_state == InventoryState.GREY_PURCHASED.value
    ).all()
    
    batch_ids = [b.id for b in batches]
    
    MillService.send_to_mill(
        db=db,
        mill_name=mill_name,
        product_id=product_id,
        raw_category=raw_category,
        finished_variant=finished_variant,
        grey_quantity=grey_quantity,
        batch_ids=batch_ids
    )
    return RedirectResponse(url="/mill", status_code=303)

@router.get("/receive/{mill_job_id}", response_class=HTMLResponse)
async def receive_from_mill_form(request: Request, mill_job_id: int, db: Session = Depends(get_db)):
    """Show form to receive from mill."""
    from models.mill import MillJob
    mill_job = db.query(MillJob).filter(MillJob.id == mill_job_id).first()
    return templates.TemplateResponse("mill/receive_form.html", {
        "request": request,
        "mill_job": mill_job
    })

@router.post("/receive/{mill_job_id}")
async def receive_from_mill(
    mill_job_id: int,
    processed_takas: int = Form(...),
    meters_per_taka: float = Form(...),
    shortage_meters: float = Form(0.0),
    job_work_charges: float = Form(...),
    gst_amount: float = Form(...),
    finished_variant: str = Form(None),
    db: Session = Depends(get_db)
):
    """Receive processed cloth from mill."""
    MillService.receive_from_mill(
        db=db,
        mill_job_id=mill_job_id,
        processed_takas=processed_takas,
        meters_per_taka=meters_per_taka,
        shortage_meters=shortage_meters,
        job_work_charges=job_work_charges,
        gst_amount=gst_amount,
        finished_variant=finished_variant
    )
    return RedirectResponse(url="/mill", status_code=303)
