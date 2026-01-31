"""Product model - hardcoded products auto-seeded on startup."""

from sqlalchemy import Column, Integer, String, Boolean
from core.database import Base

class Product(Base):
    """Product model with hardcoded types."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)  # TAIWAN_BRIGHT, BRIGHT_LYCRA, ROTO
    name = Column(String, nullable=False)  # Taiwan Bright, Bright Lycra, Roto
    takas_per_parcel = Column(Integer, nullable=False)
    purchase_by_weight = Column(Boolean, default=False)  # True only for Bright Lycra
    
    def __repr__(self):
        return f"<Product {self.name}>"
