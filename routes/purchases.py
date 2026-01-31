"""Purchase routes."""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from services.purchase_service import PurchaseService
from models.product import Product

router = APIRouter(prefix="/purchases", tags=["purchases"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def list_purchases(request: Request, db: Session = Depends(get_db)):
    """List all purchases."""
    purchases = PurchaseService.get_all_purchases(db)
    return templates.TemplateResponse("purchases/list.html", {
        "request": request,
        "purchases": purchases
    })

@router.get("/new", response_class=HTMLResponse)
async def new_purchase_form(request: Request, db: Session = Depends(get_db)):
    """Show purchase creation form."""
    products = db.query(Product).all()
    return templates.TemplateResponse("purchases/form.html", {
        "request": request,
        "products": products
    })

@router.post("/create")
async def create_purchase(
    vendor_name: str = Form(...),
    vendor_state: str = Form(...),
    product_id: int = Form(...),
    quantity: float = Form(...),
    purchase_value: float = Form(...),
    gst_amount: float = Form(...),
    send_to_mill: bool = Form(False),
    mill_name: str = Form(None),
    expected_finished_variant: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a new purchase with optional direct-to-mill."""
    PurchaseService.create_purchase(
        db=db,
        vendor_name=vendor_name,
        vendor_state=vendor_state,
        product_id=product_id,
        quantity=quantity,
        purchase_value=purchase_value,
        gst_amount=gst_amount,
        send_to_mill=send_to_mill,
        mill_name=mill_name if send_to_mill else None,
        expected_finished_variant=expected_finished_variant if send_to_mill else None
    )
    return RedirectResponse(url="/purchases", status_code=303)
