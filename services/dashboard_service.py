"""Dashboard service for aggregating data."""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from services.inventory_service import InventoryService
from services.payment_service import PaymentService
from services.gst_service import GSTService
from models.invoice import Invoice
from models.payment import Payment
from datetime import datetime, date

class DashboardService:
    """Service for dashboard data aggregation."""
    
    @staticmethod
    def get_dashboard_data(db: Session):
        """Get all dashboard data."""
        # Stock summary
        stock_summary = InventoryService.get_stock_summary(db)
        
        # Money summary
        balances = PaymentService.get_all_balances(db)
        
        # Today's activity
        today = date.today()
        today_invoices = db.query(Invoice).filter(
            func.date(Invoice.invoice_date) == today
        ).all()
        
        today_payments = db.query(Payment).filter(
            func.date(Payment.payment_date) == today
        ).all()
        
        # Current month GST summary
        now = datetime.now()
        gst_summary = GSTService.get_gstr3b_summary(db, now.year, now.month)
        
        return {
            "stock": stock_summary,
            "money": {
                "total_receivable": balances["total_receivable"],
                "total_payable": balances["total_payable"]
            },
            "today": {
                "bills": len(today_invoices),  # Phase 2: Bills/Invoices unified
                "payments": len(today_payments),
                "invoice_list": today_invoices,
                "payment_list": today_payments
            },
            "gst_current_month": gst_summary
        }
