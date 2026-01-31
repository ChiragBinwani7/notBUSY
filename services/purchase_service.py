"""Purchase service for grey cloth procurement."""

from sqlalchemy.orm import Session
from models.purchase import Purchase
from models.product import Product
from models.payment import VendorLedger
from models.gst import GSTTransaction
from services.inventory_service import InventoryService
from core.config import InventoryState, GSTTransactionType
from datetime import datetime

class PurchaseService:
    """Service for managing grey cloth purchases."""
    
    @staticmethod
    def create_purchase(
        db: Session,
        vendor_name: str,
        vendor_state: str,
        product_id: int,
        quantity: float,
        purchase_value: float,
        gst_amount: float,
        send_to_mill: bool = False,
        mill_name: str = None,
        expected_finished_variant: str = None
    ) -> Purchase:
        """
        Create a purchase record.
        For Taiwan Bright/Roto: Creates inventory batches immediately.
        For Bright Lycra: Stores weight only, batches created on mill receipt.
        
        Phase 2: If send_to_mill=True, auto-creates mill job and moves batch to IN_MILL.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Product not found")
        
        # Determine quantity unit
        quantity_unit = "kg" if product.purchase_by_weight else "takas"
        
        # Create purchase record
        purchase = Purchase(
            vendor_name=vendor_name,
            vendor_state=vendor_state,
            product_id=product_id,
            quantity=quantity,
            quantity_unit=quantity_unit,
            purchase_value=purchase_value,
            gst_amount=gst_amount,
            total_amount=purchase_value + gst_amount,
            purchase_date=datetime.utcnow(),
            send_to_mill=send_to_mill,
            mill_name=mill_name,
            expected_finished_variant=expected_finished_variant
        )
        db.add(purchase)
        db.flush()  # Get purchase ID
        
        # Create inventory batches (except for Bright Lycra)
        batch_ids = []
        if not product.purchase_by_weight:
            # Taiwan Bright or Roto: create batches immediately
            taka_count = int(quantity)
            # For now, we don't know meters yet - will be set after mill processing
            # But we create the batch in GREY_PURCHASED state
            batch = InventoryService.create_batch(
                db=db,
                product_id=product_id,
                original_meters=0,  # Will be updated after mill processing
                taka_count=taka_count,
                location_state=InventoryState.GREY_PURCHASED.value,
                finished_variant=None,  # Raw grey, no variant yet
                purchase_id=purchase.id
            )
            batch_ids.append(batch.id)
        
        # Record vendor payable
        vendor_ledger = VendorLedger(
            vendor_name=vendor_name,
            transaction_type="PURCHASE",
            reference_id=purchase.id,
            debit=purchase.total_amount,
            description=f"Purchase of {quantity} {quantity_unit} {product.name}"
        )
        db.add(vendor_ledger)
        
        # Record GST transaction
        gst_transaction = GSTTransaction(
            transaction_type=GSTTransactionType.GREY_PURCHASE.value,
            reference_id=purchase.id,
            party_name=vendor_name,
            party_state=vendor_state,
            taxable_amount=purchase_value,
            cgst_amount=0,  # Will be calculated based on state
            sgst_amount=0,
            igst_amount=gst_amount,  # Simplified for now
            total_gst=gst_amount
        )
        db.add(gst_transaction)
        
        db.commit()
        db.refresh(purchase)
        
        # Phase 2: If send_to_mill, auto-create mill job
        if send_to_mill and mill_name:
            from services.mill_service import MillService
            MillService.send_to_mill(
                db=db,
                mill_name=mill_name,
                product_id=product_id,
                raw_category=product.name,
                finished_variant=expected_finished_variant or "TBD",
                grey_quantity=quantity,
                batch_ids=batch_ids
            )
        
        return purchase
    
    @staticmethod
    def get_all_purchases(db: Session):
        """Get all purchases."""
        return db.query(Purchase).order_by(Purchase.purchase_date.desc()).all()
    
    @staticmethod
    def get_purchase_by_id(db: Session, purchase_id: int):
        """Get purchase by ID."""
        return db.query(Purchase).filter(Purchase.id == purchase_id).first()
