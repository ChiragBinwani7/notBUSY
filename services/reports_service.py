"""Reports service: Day Book, Outstanding, Aging, P&L summary."""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.invoice import Invoice
# InvoicePayment must be imported to resolve the Invoice.payment_allocations relationship
from models.invoice_payment import InvoicePayment  # noqa: F401
from models.payment import Payment, VendorLedger, MillLedger, CustomerLedger
from models.purchase import Purchase
from models.mill import MillJob
from datetime import datetime, timedelta


class ReportsService:
    """Service for business accounting reports."""

    # ------------------------------------------------------------------ #
    #  Day Book                                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def get_day_book(db: Session, from_date: datetime, to_date: datetime):
        """
        Return all transactions between from_date and to_date, ordered by date.
        Each entry has: date, type, party, debit, credit, description, ref_id
        """
        entries = []

        # Invoices (sales)
        invoices = db.query(Invoice).filter(
            Invoice.invoice_date >= from_date,
            Invoice.invoice_date <= to_date
        ).all()
        for inv in invoices:
            entries.append({
                "date": inv.invoice_date,
                "type": "Sales Invoice",
                "party": inv.customer_name,
                "description": f"Invoice {inv.invoice_number} – {inv.customer_state}",
                "debit": inv.grand_total,
                "credit": 0.0,
                "ref": inv.invoice_number,
                "url": f"/invoices/{inv.id}/print"
            })

        # Purchases
        purchases = db.query(Purchase).filter(
            Purchase.purchase_date >= from_date,
            Purchase.purchase_date <= to_date
        ).all()
        for pur in purchases:
            entries.append({
                "date": pur.purchase_date,
                "type": "Purchase",
                "party": pur.vendor_name,
                "description": f"Grey purchase from {pur.vendor_name} – {pur.product.name if pur.product else ''}",
                "debit": 0.0,
                "credit": pur.total_amount,
                "ref": f"PUR-{pur.id}",
                "url": None
            })

        # Payments received (customer)
        customer_payments = db.query(Payment).filter(
            Payment.party_type == "CUSTOMER",
            Payment.payment_date >= from_date,
            Payment.payment_date <= to_date
        ).all()
        for pmt in customer_payments:
            entries.append({
                "date": pmt.payment_date,
                "type": "Receipt",
                "party": pmt.party_name,
                "description": f"Payment received from {pmt.party_name} via {pmt.payment_method or 'N/A'}",
                "debit": 0.0,
                "credit": pmt.amount,
                "ref": f"PMT-{pmt.id}",
                "url": None
            })

        # Payments made (vendor / mill)
        out_payments = db.query(Payment).filter(
            Payment.party_type.in_(["VENDOR", "MILL"]),
            Payment.payment_date >= from_date,
            Payment.payment_date <= to_date
        ).all()
        for pmt in out_payments:
            entries.append({
                "date": pmt.payment_date,
                "type": "Payment",
                "party": pmt.party_name,
                "description": f"Payment to {pmt.party_name} ({pmt.party_type}) via {pmt.payment_method or 'N/A'}",
                "debit": pmt.amount,
                "credit": 0.0,
                "ref": f"PMT-{pmt.id}",
                "url": None
            })

        # Sort chronologically
        entries.sort(key=lambda x: x["date"])

        total_debit = sum(e["debit"] for e in entries)
        total_credit = sum(e["credit"] for e in entries)

        return {
            "entries": entries,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "from_date": from_date,
            "to_date": to_date
        }

    # ------------------------------------------------------------------ #
    #  Outstanding Receivables with Aging                                  #
    # ------------------------------------------------------------------ #
    @staticmethod
    def get_outstanding_receivables(db: Session):
        """
        Return customer-wise outstanding with aging buckets.
        Aging: Current (not yet due), 1-30, 31-60, 61-90, >90 days overdue.
        """
        today = datetime.utcnow()
        unpaid = db.query(Invoice).filter(
            Invoice.payment_status.in_(["UNPAID", "PARTIAL"])
        ).order_by(Invoice.due_date).all()

        # Group by customer
        by_customer: dict = {}
        for inv in unpaid:
            c = inv.customer_name
            if c not in by_customer:
                by_customer[c] = {
                    "customer": c,
                    "invoices": [],
                    "total": 0.0,
                    "current": 0.0,
                    "overdue_1_30": 0.0,
                    "overdue_31_60": 0.0,
                    "overdue_61_90": 0.0,
                    "overdue_90_plus": 0.0,
                }
            due = inv.due_date or (inv.invoice_date + timedelta(days=30))
            days_over = max(0, (today - due).days)
            by_customer[c]["invoices"].append({
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date,
                "due_date": due,
                "grand_total": inv.grand_total,
                "remaining_due": inv.remaining_due,
                "days_overdue": days_over,
                "id": inv.id
            })
            by_customer[c]["total"] += inv.remaining_due
            if days_over == 0:
                by_customer[c]["current"] += inv.remaining_due
            elif days_over <= 30:
                by_customer[c]["overdue_1_30"] += inv.remaining_due
            elif days_over <= 60:
                by_customer[c]["overdue_31_60"] += inv.remaining_due
            elif days_over <= 90:
                by_customer[c]["overdue_61_90"] += inv.remaining_due
            else:
                by_customer[c]["overdue_90_plus"] += inv.remaining_due

        customers = sorted(by_customer.values(), key=lambda x: -x["total"])

        grand_total = sum(c["total"] for c in customers)
        grand_current = sum(c["current"] for c in customers)
        grand_1_30 = sum(c["overdue_1_30"] for c in customers)
        grand_31_60 = sum(c["overdue_31_60"] for c in customers)
        grand_61_90 = sum(c["overdue_61_90"] for c in customers)
        grand_90_plus = sum(c["overdue_90_plus"] for c in customers)

        return {
            "customers": customers,
            "grand_total": grand_total,
            "grand_current": grand_current,
            "grand_1_30": grand_1_30,
            "grand_31_60": grand_31_60,
            "grand_61_90": grand_61_90,
            "grand_90_plus": grand_90_plus,
            "as_of": today
        }

    # ------------------------------------------------------------------ #
    #  P&L Summary                                                         #
    # ------------------------------------------------------------------ #
    @staticmethod
    def get_pnl_summary(db: Session, from_date: datetime, to_date: datetime):
        """
        Basic P&L: Sales (billed), Purchase cost, Mill charges.
        Gross Profit = Sales - Purchase Cost - Mill Charges.
        Note: This is a cash-basis approximation.
        """
        # Sales invoiced in period
        invoices = db.query(Invoice).filter(
            Invoice.invoice_date >= from_date,
            Invoice.invoice_date <= to_date
        ).all()
        total_sales = sum(inv.product_value for inv in invoices)
        total_freight_billed = sum(inv.freight_charges for inv in invoices)
        total_gst_collected = sum(inv.total_gst for inv in invoices)
        total_billed = sum(inv.grand_total for inv in invoices)

        # Purchases in period
        purchases = db.query(Purchase).filter(
            Purchase.purchase_date >= from_date,
            Purchase.purchase_date <= to_date
        ).all()
        total_purchase_value = sum(p.purchase_value for p in purchases)
        total_purchase_gst = sum(p.gst_amount for p in purchases)

        # Mill job charges in period
        mill_jobs = db.query(MillJob).filter(
            MillJob.sent_date >= from_date,
            MillJob.sent_date <= to_date,
            MillJob.total_charges.is_not(None)
        ).all()
        total_mill_charges = sum((mj.total_charges or 0.0) for mj in mill_jobs)

        gross_profit = total_sales - total_purchase_value - total_mill_charges

        return {
            "from_date": from_date,
            "to_date": to_date,
            "sales": {
                "product_value": total_sales,
                "freight_billed": total_freight_billed,
                "gst_collected": total_gst_collected,
                "total_billed": total_billed,
                "invoice_count": len(invoices)
            },
            "purchases": {
                "purchase_value": total_purchase_value,
                "gst_paid": total_purchase_gst,
                "count": len(purchases)
            },
            "mill_charges": {
                "total": total_mill_charges,
                "count": len(mill_jobs)
            },
            "gross_profit": gross_profit,
            "gst_net_payable": total_gst_collected - total_purchase_gst
        }
