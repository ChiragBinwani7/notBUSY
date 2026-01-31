"""Payment service for managing ledgers and payments."""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.payment import Payment, VendorLedger, MillLedger, CustomerLedger
from datetime import datetime

class PaymentService:
    """Service for managing payments and ledgers."""
    
    @staticmethod
    def record_payment(
        db: Session,
        party_type: str,  # VENDOR, MILL, CUSTOMER
        party_name: str,
        amount: float,
        payment_method: str = None,
        notes: str = None,
        invoice_allocations: list = None  # Phase 2: [{invoice_id, amount}, ...]
    ) -> Payment:
        """
        Record a payment transaction.
        Phase 2: For CUSTOMER payments, allocate to specific invoices.
        """
        payment = Payment(
            party_type=party_type,
            party_name=party_name,
            amount=amount,
            payment_method=payment_method,
            notes=notes,
            payment_date=datetime.utcnow()
        )
        db.add(payment)
        db.flush()
        
        # Update appropriate ledger
        if party_type == "VENDOR":
            ledger_entry = VendorLedger(
                vendor_name=party_name,
                transaction_type="PAYMENT",
                reference_id=payment.id,
                credit=amount,
                description=f"Payment received - {payment_method or 'N/A'}"
            )
            db.add(ledger_entry)
        elif party_type == "MILL":
            ledger_entry = MillLedger(
                mill_name=party_name,
                transaction_type="PAYMENT",
                reference_id=payment.id,
                credit=amount,
                description=f"Payment made - {payment_method or 'N/A'}"
            )
            db.add(ledger_entry)
        elif party_type == "CUSTOMER":
            # Phase 2: Handle invoice allocations
            if invoice_allocations:
                from models.invoice_payment import InvoicePayment
                from models.invoice import Invoice
                
                for allocation in invoice_allocations:
                    invoice_id = allocation["invoice_id"]
                    allocated_amount = allocation["amount"]
                    
                    # Create allocation record
                    inv_payment = InvoicePayment(
                        payment_id=payment.id,
                        invoice_id=invoice_id,
                        applied_amount=allocated_amount
                    )
                    db.add(inv_payment)
                    
                    # Update invoice remaining_due and status
                    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
                    if invoice:
                        invoice.remaining_due -= allocated_amount
                        
                        if invoice.remaining_due <= 0:
                            invoice.payment_status = "PAID"
                            invoice.remaining_due = 0
                        elif invoice.remaining_due < invoice.grand_total:
                            invoice.payment_status = "PARTIAL"
            
            ledger_entry = CustomerLedger(
                customer_name=party_name,
                transaction_type="PAYMENT",
                reference_id=payment.id,
                credit=amount,
                description=f"Payment received - {payment_method or 'N/A'}"
            )
            db.add(ledger_entry)
        
        db.commit()
        db.refresh(payment)
        return payment
    
    @staticmethod
    def get_vendor_balance(db: Session, vendor_name: str):
        """Get vendor balance (payable)."""
        entries = db.query(VendorLedger).filter(
            VendorLedger.vendor_name == vendor_name
        ).all()
        
        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)
        balance = total_debit - total_credit
        
        return {
            "vendor_name": vendor_name,
            "total_payable": total_debit,
            "total_paid": total_credit,
            "balance": balance,
            "entries": entries
        }
    
    @staticmethod
    def get_mill_balance(db: Session, mill_name: str):
        """Get mill balance (payable)."""
        entries = db.query(MillLedger).filter(
            MillLedger.mill_name == mill_name
        ).all()
        
        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)
        balance = total_debit - total_credit
        
        return {
            "mill_name": mill_name,
            "total_payable": total_debit,
            "total_paid": total_credit,
            "balance": balance,
            "entries": entries
        }
    
    @staticmethod
    def get_customer_balance(db: Session, customer_name: str):
        """Get customer balance (receivable)."""
        entries = db.query(CustomerLedger).filter(
            CustomerLedger.customer_name == customer_name
        ).all()
        
        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)
        balance = total_debit - total_credit
        
        return {
            "customer_name": customer_name,
            "total_receivable": total_debit,
            "total_received": total_credit,
            "balance": balance,
            "entries": entries
        }
    
    @staticmethod
    def get_all_balances(db: Session):
        """Get summary of all balances."""
        # Get unique parties
        vendors = db.query(VendorLedger.vendor_name).distinct().all()
        mills = db.query(MillLedger.mill_name).distinct().all()
        customers = db.query(CustomerLedger.customer_name).distinct().all()
        
        vendor_balances = [PaymentService.get_vendor_balance(db, v[0]) for v in vendors]
        mill_balances = [PaymentService.get_mill_balance(db, m[0]) for m in mills]
        customer_balances = [PaymentService.get_customer_balance(db, c[0]) for c in customers]
        
        total_payable = sum(v["balance"] for v in vendor_balances) + sum(m["balance"] for m in mill_balances)
        total_receivable = sum(c["balance"] for c in customer_balances)
        
        return {
            "vendors": vendor_balances,
            "mills": mill_balances,
            "customers": customer_balances,
            "total_payable": total_payable,
            "total_receivable": total_receivable
        }
