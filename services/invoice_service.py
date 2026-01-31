"""Invoice service for unified bill/challan workflow (Phase 2)."""

from sqlalchemy.orm import Session
from models.invoice import Invoice
from models.product import Product
from models.payment import CustomerLedger
from models.gst import GSTTransaction
from services.inventory_service import InventoryService
from core.config import GSTTransactionType, GUJARAT_STATE, GST_RATE_CGST, GST_RATE_SGST, GST_RATE_IGST, FREIGHT_PER_PARCEL
from datetime import datetime
import json

class InvoiceService:
    """Service for managing invoices with unified bill/challan workflow."""
    
    @staticmethod
    def generate_invoice_number(db: Session) -> str:
        """Generate next invoice number in format INV-YYYYMMDD-001."""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"INV-{today}-"
        
        # Find last invoice for today
        last_invoice = db.query(Invoice).filter(
            Invoice.invoice_number.like(f"{prefix}%")
        ).order_by(Invoice.invoice_number.desc()).first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:03d}"
    
    @staticmethod
    def create_invoice(
        db: Session,
        customer_name: str,
        customer_state: str,
        transport_name: str,
        line_items: list
    ) -> Invoice:
        """
        Create invoice with unified bill/challan data.
        
        line_items format: [
            {
                "product_id": 1,
                "finished_variant": "Bright Lycra 26G",
                "parcel_count": 2,
                "taka_meters": [25.5, 26.0, 25.8, 26.2],  # Individual taka meters
                "fold_percent": 10,
                "rate_per_meter": 60
            },
            ...
        ]
        """
        # Validate and process line items
        processed_items = []
        total_parcels = 0
        product_value = 0.0
        
        for item in line_items:
            product = db.query(Product).filter(Product.id == item["product_id"]).first()
            if not product:
                raise ValueError(f"Product {item['product_id']} not found")
            
            finished_variant = item["finished_variant"]
            
            # CRITICAL: Reject TBD variants
            if finished_variant == "TBD":
                raise ValueError("Cannot bill TBD variants. Please finalize the variant first.")
            
            # Calculate meters
            taka_meters = item["taka_meters"]
            raw_meters = sum(taka_meters)
            fold_percent = item.get("fold_percent", 0)
            net_meters = raw_meters - (raw_meters * fold_percent / 100)
            
            # Check inventory availability
            available_variants = InventoryService.get_available_variants(db, product.id)
            if finished_variant not in available_variants:
                raise ValueError(f"Variant '{finished_variant}' not available in stock")
            
            # Calculate value
            rate_per_meter = item["rate_per_meter"]
            item_value = net_meters * rate_per_meter
            
            processed_item = {
                "product_id": product.id,
                "product_name": product.name,
                "finished_variant": finished_variant,
                "parcel_count": item["parcel_count"],
                "taka_meters": taka_meters,
                "raw_meters": round(raw_meters, 2),
                "fold_percent": fold_percent,
                "net_meters": round(net_meters, 2),
                "rate_per_meter": rate_per_meter,
                "item_value": round(item_value, 2)
            }
            
            processed_items.append(processed_item)
            total_parcels += item["parcel_count"]
            product_value += item_value
            
            # Reduce inventory using FIFO with variant filtering
            InventoryService.reduce_inventory_fifo(
                db=db,
                product_id=product.id,
                finished_variant=finished_variant,
                meters_to_reduce=net_meters
            )
        
        # Calculate freight
        freight_charges = total_parcels * FREIGHT_PER_PARCEL
        
        # Calculate GST
        taxable_amount = product_value + freight_charges
        
        if customer_state == GUJARAT_STATE:
            cgst_amount = taxable_amount * GST_RATE_CGST / 100
            sgst_amount = taxable_amount * GST_RATE_SGST / 100
            igst_amount = 0.0
        else:
            cgst_amount = 0.0
            sgst_amount = 0.0
            igst_amount = taxable_amount * GST_RATE_IGST / 100
        
        total_gst = cgst_amount + sgst_amount + igst_amount
        grand_total = taxable_amount + total_gst
        
        # Generate invoice number
        invoice_number = InvoiceService.generate_invoice_number(db)
        
        # Create invoice
        invoice = Invoice(
            customer_name=customer_name,
            customer_state=customer_state,
            transport_name=transport_name,
            invoice_number=invoice_number,
            invoice_date=datetime.utcnow(),
            line_items_json=json.dumps(processed_items),
            total_parcels=total_parcels,
            product_value=round(product_value, 2),
            freight_charges=round(freight_charges, 2),
            cgst_amount=round(cgst_amount, 2),
            sgst_amount=round(sgst_amount, 2),
            igst_amount=round(igst_amount, 2),
            total_gst=round(total_gst, 2),
            grand_total=round(grand_total, 2),
            remaining_due=round(grand_total, 2),
            payment_status="UNPAID"
        )
        db.add(invoice)
        db.flush()
        
        # Record customer receivable
        customer_ledger = CustomerLedger(
            customer_name=customer_name,
            transaction_type="INVOICE",
            reference_id=invoice.id,
            debit=grand_total,
            description=f"Invoice {invoice_number}"
        )
        db.add(customer_ledger)
        
        # Record GST transaction
        gst_transaction = GSTTransaction(
            transaction_type=GSTTransactionType.SALE.value,
            reference_id=invoice.id,
            party_name=customer_name,
            party_state=customer_state,
            taxable_amount=round(taxable_amount, 2),
            cgst_amount=round(cgst_amount, 2),
            sgst_amount=round(sgst_amount, 2),
            igst_amount=round(igst_amount, 2),
            total_gst=round(total_gst, 2)
        )
        db.add(gst_transaction)
        
        db.commit()
        db.refresh(invoice)
        return invoice
    
    @staticmethod
    def get_all_invoices(db: Session):
        """Get all invoices."""
        return db.query(Invoice).order_by(Invoice.invoice_date.desc()).all()
    
    @staticmethod
    def get_invoice_by_id(db: Session, invoice_id: int):
        """Get invoice by ID."""
        return db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    @staticmethod
    def get_challan_print_data(db: Session, invoice_id: int):
        """
        Get invoice data formatted for challan print.
        Shows raw meters, no pricing.
        """
        invoice = InvoiceService.get_invoice_by_id(db, invoice_id)
        if not invoice:
            return None
        
        return {
            "invoice": invoice,
            "line_items": invoice.line_items,
            "show_pricing": False
        }
    
    @staticmethod
    def get_invoice_print_data(db: Session, invoice_id: int):
        """
        Get invoice data formatted for invoice print.
        Shows net meters and pricing.
        """
        invoice = InvoiceService.get_invoice_by_id(db, invoice_id)
        if not invoice:
            return None
        
        return {
            "invoice": invoice,
            "line_items": invoice.line_items,
            "show_pricing": True
        }
    
    @staticmethod
    def get_unpaid_invoices(db: Session, customer_name: str):
        """Get unpaid/partially paid invoices for a customer."""
        return db.query(Invoice).filter(
            Invoice.customer_name == customer_name,
            Invoice.remaining_due > 0
        ).order_by(Invoice.invoice_date.asc()).all()
