"""Payment routes with invoice-based allocation (Phase 2)."""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from services.payment_service import PaymentService
from services.invoice_service import InvoiceService
import json

router = APIRouter(prefix="/payments", tags=["payments"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def payment_dashboard(request: Request, db: Session = Depends(get_db)):
    """Show payment dashboard with all balances."""
    balances = PaymentService.get_all_balances(db)
    return templates.TemplateResponse("payments/dashboard.html", {
        "request": request,
        "balances": balances
    })

@router.get("/record", response_class=HTMLResponse)
async def record_payment_form(
    request: Request,
    party_type: str = None,
    party_name: str = None,
    db: Session = Depends(get_db)
):
    """Show payment recording form, optionally pre-filled from query params."""
    return templates.TemplateResponse("payments/form.html", {
        "request": request,
        "prefill_party_type": party_type or "",
        "prefill_party_name": party_name or "",
    })

@router.post("/record")
async def record_payment(
    party_type: str = Form(...),
    party_name: str = Form(...),
    amount: float = Form(...),
    payment_method: str = Form(None),
    notes: str = Form(None),
    invoice_allocations_json: str = Form(None),
    db: Session = Depends(get_db)
):
    """Record a payment with optional invoice allocations."""
    invoice_allocations = None
    if invoice_allocations_json:
        invoice_allocations = json.loads(invoice_allocations_json)
    
    PaymentService.record_payment(
        db=db,
        party_type=party_type,
        party_name=party_name,
        amount=amount,
        payment_method=payment_method,
        notes=notes,
        invoice_allocations=invoice_allocations
    )
    return RedirectResponse(url="/payments", status_code=303)

@router.get("/ledger/{party_type}/{party_name}", response_class=HTMLResponse)
async def view_ledger(request: Request, party_type: str, party_name: str, db: Session = Depends(get_db)):
    """View transaction ledger for a party."""
    if party_type == "CUSTOMER":
        ledger = PaymentService.get_customer_balance(db, party_name)
    elif party_type == "VENDOR":
        ledger = PaymentService.get_vendor_balance(db, party_name)
    elif party_type == "MILL":
        ledger = PaymentService.get_mill_balance(db, party_name)
    else:
        return RedirectResponse(url="/payments", status_code=303)

    return templates.TemplateResponse("payments/ledger.html", {
        "request": request,
        "party_type": party_type,
        "party_name": party_name,
        "ledger": ledger
    })


@router.get("/customer/{customer_name}/invoices")
async def get_customer_invoices(customer_name: str, db: Session = Depends(get_db)):
    """Get unpaid invoices for a customer (AJAX endpoint)."""
    from fastapi.responses import JSONResponse
    
    invoices = InvoiceService.get_unpaid_invoices(db, customer_name)
    
    invoice_data = []
    for inv in invoices:
        invoice_data.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "date": inv.invoice_date.strftime("%Y-%m-%d"),
            "grand_total": inv.grand_total,
            "remaining_due": inv.remaining_due
        })
    
    return JSONResponse(content=invoice_data)
