"""Purchase model for grey cloth procurement."""

from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Purchase(Base):
    """Purchase model for grey cloth procurement."""
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Vendor details
    vendor_name = Column(String, nullable=False)
    vendor_state = Column(String, nullable=False)
    
    # Product and quantity
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)  # Takas for Taiwan Bright/Roto, kg for Bright Lycra
    quantity_unit = Column(String, nullable=False)  # "takas" or "kg"
    
    # Financial
    purchase_value = Column(Float, nullable=False)
    gst_amount = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)  # purchase_value + gst_amount
    
    # Direct-to-mill option (Phase 2)
    send_to_mill = Column(Boolean, default=False)
    mill_name = Column(String, nullable=True)
    expected_finished_variant = Column(String, nullable=True)  # Can be "TBD"
    
    # Timestamps
    purchase_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relations
    product = relationship("Product")
    inventory_batches = relationship("InventoryBatch", back_populates="purchase")
    
    def __repr__(self):
        return f"<Purchase {self.id}: {self.vendor_name}, {self.quantity} {self.quantity_unit}>"
