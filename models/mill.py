"""Mill job work models."""

from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class MillJob(Base):
    """Mill job tracking grey sent to mill."""
    __tablename__ = "mill_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Mill details
    mill_name = Column(String, nullable=False)
    
    # Product and quantity
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product")
    
    # Product variant tracking (Phase 2)
    raw_category = Column(String, nullable=False)  # Base product name (e.g., "Bright Lycra")
    finished_variant = Column(String, nullable=False)  # Specific variant (e.g., "Bright Lycra 26G" or "TBD")
    variant_finalized = Column(Boolean, default=False)  # True when finished_variant != "TBD"
    
    # Grey sent to mill
    grey_quantity = Column(Float, nullable=False)  # Quantity sent (takas or kg)
    grey_quantity_unit = Column(String, nullable=False)  # "takas" or "kg"
    
    # Dates
    sent_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    received_date = Column(DateTime, nullable=True)
    
    # Receipt details (filled when received)
    processed_takas = Column(Integer, nullable=True)
    meters_per_taka = Column(Float, nullable=True)
    total_meters = Column(Float, nullable=True)
    shortage_meters = Column(Float, default=0.0)
    
    # Charges
    job_work_charges = Column(Float, nullable=True)
    gst_amount = Column(Float, nullable=True)
    total_charges = Column(Float, nullable=True)
    
    # Status
    status = Column(String, default="SENT", nullable=False)  # SENT, RECEIVED
    
    # Relations
    inventory_batches = relationship("InventoryBatch", back_populates="mill_job")
    
    def __repr__(self):
        return f"<MillJob {self.id}: {self.mill_name}, {self.status}>"
