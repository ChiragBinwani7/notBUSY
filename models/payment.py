"""Payment and ledger models."""

from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class VendorLedger(Base):
    """Vendor ledger for grey purchase payables."""
    __tablename__ = "vendor_ledgers"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String, nullable=False, index=True)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Transaction details
    transaction_type = Column(String, nullable=False)  # PURCHASE, PAYMENT
    reference_id = Column(Integer, nullable=True)  # Purchase ID or Payment ID
    
    # Amounts
    debit = Column(Float, default=0.0)  # Payable increases
    credit = Column(Float, default=0.0)  # Payments
    
    description = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<VendorLedger {self.vendor_name}: Dr {self.debit}, Cr {self.credit}>"

class MillLedger(Base):
    """Mill ledger for job work payables."""
    __tablename__ = "mill_ledgers"
    
    id = Column(Integer, primary_key=True, index=True)
    mill_name = Column(String, nullable=False, index=True)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Transaction details
    transaction_type = Column(String, nullable=False)  # MILL_JOB, PAYMENT
    reference_id = Column(Integer, nullable=True)  # Mill Job ID or Payment ID
    
    # Amounts
    debit = Column(Float, default=0.0)  # Payable increases
    credit = Column(Float, default=0.0)  # Payments
    
    description = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<MillLedger {self.mill_name}: Dr {self.debit}, Cr {self.credit}>"

class CustomerLedger(Base):
    """Customer ledger for sales receivables."""
    __tablename__ = "customer_ledgers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False, index=True)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Transaction details
    transaction_type = Column(String, nullable=False)  # INVOICE, PAYMENT
    reference_id = Column(Integer, nullable=True)  # Invoice ID or Payment ID
    
    # Amounts
    debit = Column(Float, default=0.0)  # Receivable increases
    credit = Column(Float, default=0.0)  # Payments received
    
    description = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<CustomerLedger {self.customer_name}: Dr {self.debit}, Cr {self.credit}>"

class Payment(Base):
    """Payment transactions."""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Party details
    party_type = Column(String, nullable=False)  # VENDOR, MILL, CUSTOMER
    party_name = Column(String, nullable=False)
    
    # Amount
    amount = Column(Float, nullable=False)
    
    # Payment method
    payment_method = Column(String, nullable=True)  # CASH, BANK, CHEQUE, etc.
    
    notes = Column(String, nullable=True)
    
    # Relationships (Phase 2)
    invoice_allocations = relationship("InvoicePayment", back_populates="payment")
    
    def __repr__(self):
        return f"<Payment {self.id}: {self.party_type} {self.party_name}, ₹{self.amount}>"
