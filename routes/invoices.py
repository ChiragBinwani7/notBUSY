"""Invoice routes for unified bill/challan workflow (Phase 2)."""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from core.config import FREIGHT_PER_PARCEL, GST_RATES
from core.config import (COMPANY_NAME, COMPANY_TYPE, COMPANY_ADDRESS,
                         COMPANY_GSTIN, COMPANY_PHONE,
                         COMPANY_BANK_NAME, COMPANY_BANK_ACCOUNT, COMPANY_BANK_IFSC)
from services.invoice_service import InvoiceService
from services.inventory_service import InventoryService
from models.product import Product
import json

router = APIRouter(prefix="/invoices", tags=["invoices"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def list_invoices(request: Request, db: Session = Depends(get_db)):
    """List all invoices."""
    invoices = InvoiceService.get_all_invoices(db)
    return templates.TemplateResponse("invoices/list.html", {
        "request": request,
        "invoices": invoices
    })

@router.get("/new", response_class=HTMLResponse)
async def new_invoice_form(request: Request, db: Session = Depends(get_db)):
    """Show invoice creation form."""
    products = db.query(Product).all()
    
    # Get available variants for each product
    product_variants = {}
    for product in products:
        variants = InventoryService.get_available_variants(db, product.id)
        product_variants[product.id] = variants
    
    # Serialize products for JavaScript (only needed fields)
    products_json = json.dumps([
        {"id": p.id, "name": p.name} for p in products
    ])
    
    return templates.TemplateResponse("invoices/form.html", {
        "request": request,
        "products": products,
        "products_json": products_json,
        "product_variants": json.dumps(product_variants)
    })

@router.post("/create")
async def create_invoice(
    customer_name: str = Form(...),
    customer_state: str = Form(...),
    transport_name: str = Form(...),
    line_items_json: str = Form(...),
    payment_terms_days: int = Form(30),
    db: Session = Depends(get_db)
):
    """Create a new invoice."""
    line_items = json.loads(line_items_json)
    
    invoice = InvoiceService.create_invoice(
        db=db,
        customer_name=customer_name,
        customer_state=customer_state,
        transport_name=transport_name,
        line_items=line_items,
        payment_terms_days=payment_terms_days
    )
    return RedirectResponse(url=f"/invoices/{invoice.id}/print", status_code=303)

@router.get("/{invoice_id}/challan", response_class=HTMLResponse)
async def print_challan(request: Request, invoice_id: int, db: Session = Depends(get_db)):
    """Print challan format (raw meters, no pricing)."""
    data = InvoiceService.get_challan_print_data(db, invoice_id)
    if not data:
        return RedirectResponse(url="/invoices")
    
    return templates.TemplateResponse("invoices/challan_print.html", {
        "request": request,
        **data
    })

@router.get("/{invoice_id}/print", response_class=HTMLResponse)
async def print_invoice(request: Request, invoice_id: int, db: Session = Depends(get_db)):
    """Print invoice format (net meters, pricing)."""
    data = InvoiceService.get_invoice_print_data(db, invoice_id)
    if not data:
        return RedirectResponse(url="/invoices")
    
    return templates.TemplateResponse("invoices/print.html", {
        "request": request,
        **data,
        "freight_per_parcel": FREIGHT_PER_PARCEL,
        "gst_rates": {
            "cgst": GST_RATES["CGST"] * 100,
            "sgst": GST_RATES["SGST"] * 100,
            "igst": GST_RATES["IGST"] * 100,
        },
        "company_name": COMPANY_NAME,
        "company_type": COMPANY_TYPE,
        "company_address": COMPANY_ADDRESS,
        "company_gstin": COMPANY_GSTIN,
        "company_phone": COMPANY_PHONE,
        "company_bank_name": COMPANY_BANK_NAME,
        "company_bank_account": COMPANY_BANK_ACCOUNT,
        "company_bank_ifsc": COMPANY_BANK_IFSC,
    })
