"""GST transaction tracking model."""

from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from datetime import datetime
from core.database import Base

class GSTTransaction(Base):
    """GST transaction tracking with separate types for grey purchases, mill jobs, and sales."""
    __tablename__ = "gst_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Transaction type: GREY_PURCHASE, MILL_JOB, SALE
    transaction_type = Column(String, nullable=False, index=True)
    
    # Reference
    reference_id = Column(Integer, nullable=False)  # Purchase ID, Mill Job ID, or Invoice ID
    
    # Party details
    party_name = Column(String, nullable=False)
    party_state = Column(String, nullable=False)
    
    # Taxable amount
    taxable_amount = Column(Float, nullable=False)
    
    # GST breakdown
    cgst_amount = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    total_gst = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<GSTTransaction {self.transaction_type}: {self.party_name}, ₹{self.total_gst}>"
