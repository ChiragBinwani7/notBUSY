"""Inventory batch model for tracking cloth stock."""

from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base
from core.config import InventoryState

class InventoryBatch(Base):
    """Inventory batch tracking cloth in batches (not individual takas)."""
    __tablename__ = "inventory_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="inventory_batches")
    
    # Finished variant (e.g., "Bright Lycra 26G", "Taiwan 24G CXC")
    # Can be "TBD" for batches in mill that haven't been finalized
    # NULL for raw grey purchases (before mill processing)
    finished_variant = Column(String, nullable=True)
    
    # Meters tracking
    original_meters = Column(Float, nullable=False)  # Initial meters in batch
    available_meters = Column(Float, nullable=False)  # Remaining meters after consumption
    
    # Taka tracking
    taka_count = Column(Integer, nullable=False)  # Number of takas in this batch
    
    # State tracking
    location_state = Column(String, nullable=False, index=True)  # GREY_PURCHASED, IN_MILL, IN_SHOP
    
    # FIFO tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=True)
    mill_job_id = Column(Integer, ForeignKey("mill_jobs.id"), nullable=True)
    
    # Relations
    product = relationship("Product")
    purchase = relationship("Purchase", back_populates="inventory_batches")
    mill_job = relationship("MillJob", back_populates="inventory_batches")
    
    def __repr__(self):
        return f"<InventoryBatch {self.id}: {self.available_meters}/{self.original_meters}m, {self.taka_count} takas, {self.location_state}>"
