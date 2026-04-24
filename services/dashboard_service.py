"""Dashboard service for aggregating data."""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from services.inventory_service import InventoryService
from services.payment_service import PaymentService
from services.gst_service import GSTService
from models.invoice import Invoice
from models.payment import Payment
from datetime import datetime, date, timedelta

class DashboardService:
    """Service for dashboard data aggregation."""
    
    @staticmethod
    def get_overdue_invoices(db: Session):
        """Get overdue invoices with aging buckets."""
        today = datetime.utcnow()
        unpaid = db.query(Invoice).filter(
            Invoice.payment_status.in_(["UNPAID", "PARTIAL"]),
            Invoice.due_date != None
        ).all()
        
        overdue = [inv for inv in unpaid if inv.due_date and inv.due_date < today]
        
        # Aging buckets
        bucket_0_30 = [inv for inv in overdue if inv.days_overdue <= 30]
        bucket_31_60 = [inv for inv in overdue if 31 <= inv.days_overdue <= 60]
        bucket_61_90 = [inv for inv in overdue if 61 <= inv.days_overdue <= 90]
        bucket_90_plus = [inv for inv in overdue if inv.days_overdue > 90]
        
        return {
            "total_count": len(overdue),
            "total_amount": sum(inv.remaining_due for inv in overdue),
            "invoices": sorted(overdue, key=lambda x: x.due_date),
            "buckets": {
                "0_30": {"count": len(bucket_0_30), "amount": sum(i.remaining_due for i in bucket_0_30)},
                "31_60": {"count": len(bucket_31_60), "amount": sum(i.remaining_due for i in bucket_31_60)},
                "61_90": {"count": len(bucket_61_90), "amount": sum(i.remaining_due for i in bucket_61_90)},
                "90_plus": {"count": len(bucket_90_plus), "amount": sum(i.remaining_due for i in bucket_90_plus)},
            }
        }
    
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
        
        # Overdue invoices
        overdue = DashboardService.get_overdue_invoices(db)
        
        # Total unpaid/partially paid receivables
        all_unpaid = db.query(Invoice).filter(
            Invoice.payment_status.in_(["UNPAID", "PARTIAL"])
        ).all()
        pending_receivable = sum(inv.remaining_due for inv in all_unpaid)
        
        return {
            "stock": stock_summary,
            "money": {
                "total_receivable": balances["total_receivable"],
                "total_payable": balances["total_payable"],
                "pending_receivable": pending_receivable
            },
            "today": {
                "invoices": len(today_invoices),
                "payments": len(today_payments),
                "invoice_list": today_invoices,
                "payment_list": today_payments
            },
            "gst_current_month": gst_summary,
            "overdue": overdue
        }
