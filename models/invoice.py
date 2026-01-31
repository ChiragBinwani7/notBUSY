"""Invoice model with fold calculation and inventory reduction."""

from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base
import json

class Invoice(Base):
    """Invoice model with fold logic and FIFO inventory reduction."""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Customer details
    customer_name = Column(String, nullable=False)
    customer_state = Column(String, nullable=False)
    transport_name = Column(String, nullable=False)
    
    # Auto-generated invoice number (e.g., "INV-20260131-001")
    invoice_number = Column(String, unique=True, nullable=False)
    
    # Date
    invoice_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Line items stored as JSON (Phase 2 format)
    # Each item: {
    #   product_id, finished_variant, parcel_count,
    #   taka_meters: [25.5, 26.0, ...],  // Individual taka meters
    #   raw_meters,  // Sum of taka_meters
    #   fold_percent, net_meters,  // raw_meters - (raw_meters * fold / 100)
    #   rate_per_meter, item_value  // net_meters * rate_per_meter
    # }
    line_items_json = Column(Text, nullable=False)
    
    # Total parcels across all line items
    total_parcels = Column(Integer, nullable=False)
    
    # Financial calculations
    product_value = Column(Float, nullable=False)
    freight_charges = Column(Float, nullable=False)  # ₹100 per parcel
    
    # GST breakdown
    cgst_amount = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    total_gst = Column(Float, nullable=False)
    
    # Grand total
    grand_total = Column(Float, nullable=False)
    
    # Payment tracking (Phase 2)
    remaining_due = Column(Float, nullable=False)  # Initially equals grand_total
    payment_status = Column(String, default="UNPAID")  # UNPAID, PARTIAL, PAID
    
    # Relationships
    payment_allocations = relationship("InvoicePayment", back_populates="invoice")
    
    def __repr__(self):
        return f"<Invoice {self.id}: {self.customer_name}, ₹{self.grand_total}>"
    
    @property
    def line_items(self):
        """Parse line items from JSON."""
        return json.loads(self.line_items_json) if self.line_items_json else []
    
    @line_items.setter
    def line_items(self, items):
        """Store line items as JSON."""
        self.line_items_json = json.dumps(items)
