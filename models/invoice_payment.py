"""Invoice payment allocation model for tracking partial payments."""

from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class InvoicePayment(Base):
    """Tracks payment allocation to specific invoices."""
    __tablename__ = "invoice_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Links
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Amount applied from this payment to this invoice
    applied_amount = Column(Float, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    payment = relationship("Payment", back_populates="invoice_allocations")
    invoice = relationship("Invoice", back_populates="payment_allocations")
    
    def __repr__(self):
        return f"<InvoicePayment payment={self.payment_id} invoice={self.invoice_id} amount=₹{self.applied_amount}>"
