"""Mill job work service."""

from sqlalchemy.orm import Session
from models.mill import MillJob
from models.product import Product
from models.inventory import InventoryBatch
from models.payment import MillLedger
from models.gst import GSTTransaction
from services.inventory_service import InventoryService
from core.config import InventoryState, GSTTransactionType
from datetime import datetime

class MillService:
    """Service for managing mill job work."""
    
    @staticmethod
    def send_to_mill(
        db: Session,
        mill_name: str,
        product_id: int,
        raw_category: str,
        finished_variant: str,
        grey_quantity: float,
        batch_ids: list = None
    ) -> MillJob:
        """
        Send grey to mill.
        For Taiwan Bright/Roto: Move existing batches from GREY_PURCHASED to IN_MILL.
        For Bright Lycra: Just record the weight sent.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Product not found")
        
        quantity_unit = "kg" if product.purchase_by_weight else "takas"
        
        # Create mill job record
        mill_job = MillJob(
            mill_name=mill_name,
            product_id=product_id,
            raw_category=raw_category,
            finished_variant=finished_variant,
            variant_finalized=(finished_variant != "TBD"),
            grey_quantity=grey_quantity,
            grey_quantity_unit=quantity_unit,
            sent_date=datetime.utcnow(),
            status="SENT"
        )
        db.add(mill_job)
        db.flush()
        
        # Move batches to IN_MILL state (if not Bright Lycra)
        if not product.purchase_by_weight and batch_ids:
            InventoryService.move_batches_to_state(
                db=db,
                batch_ids=batch_ids,
                new_state=InventoryState.IN_MILL.value
            )
            
            # Update batch mill_job_id
            batches = db.query(InventoryBatch).filter(InventoryBatch.id.in_(batch_ids)).all()
            for batch in batches:
                batch.mill_job_id = mill_job.id
        
        db.commit()
        db.refresh(mill_job)
        return mill_job
    
    @staticmethod
    def receive_from_mill(
        db: Session,
        mill_job_id: int,
        processed_takas: int,
        meters_per_taka: float,
        shortage_meters: float,
        job_work_charges: float,
        gst_amount: float,
        finished_variant: str = None
    ) -> MillJob:
        """
        Receive processed cloth from mill.
        For Bright Lycra: Creates inventory batches here.
        For others: Updates existing batches with meters and moves to IN_SHOP.
        """
        mill_job = db.query(MillJob).filter(MillJob.id == mill_job_id).first()
        if not mill_job:
            raise ValueError("Mill job not found")
        
        product = db.query(Product).filter(Product.id == mill_job.product_id).first()
        
        total_meters = processed_takas * meters_per_taka
        
        # Update mill job
        # If finished_variant provided and was TBD, finalize it
        if finished_variant and mill_job.finished_variant == "TBD":
            mill_job.finished_variant = finished_variant
            mill_job.variant_finalized = True
        elif not mill_job.variant_finalized:
            raise ValueError("Finished variant must be specified for TBD mill jobs")
        
        mill_job.processed_takas = processed_takas
        mill_job.meters_per_taka = meters_per_taka
        mill_job.total_meters = total_meters
        mill_job.shortage_meters = shortage_meters
        mill_job.job_work_charges = job_work_charges
        mill_job.gst_amount = gst_amount
        mill_job.total_charges = job_work_charges + gst_amount
        mill_job.received_date = datetime.utcnow()
        mill_job.status = "RECEIVED"
        
        if product.purchase_by_weight:
            # Bright Lycra: Create inventory batches here with finished variant
            InventoryService.create_batch(
                db=db,
                product_id=product.id,
                original_meters=total_meters,
                taka_count=processed_takas,
                location_state=InventoryState.IN_SHOP.value,
                finished_variant=mill_job.finished_variant,
                mill_job_id=mill_job.id
            )
        else:
            # Taiwan Bright/Roto: Update existing batches and move to IN_SHOP
            batches = db.query(InventoryBatch).filter(
                InventoryBatch.mill_job_id == mill_job_id
            ).all()
            
            if batches:
                # Update meters and finished variant for batches
                meters_per_batch = total_meters / len(batches)
                for batch in batches:
                    batch.original_meters = meters_per_batch
                    batch.available_meters = meters_per_batch
                    batch.finished_variant = mill_job.finished_variant
                    batch.location_state = InventoryState.IN_SHOP.value
        
        # Record mill payable
        mill_ledger = MillLedger(
            mill_name=mill_job.mill_name,
            transaction_type="MILL_JOB",
            reference_id=mill_job.id,
            debit=mill_job.total_charges,
            description=f"Job work for {processed_takas} takas {product.name}"
        )
        db.add(mill_ledger)
        
        # Record GST transaction
        gst_transaction = GSTTransaction(
            transaction_type=GSTTransactionType.MILL_JOB.value,
            reference_id=mill_job.id,
            party_name=mill_job.mill_name,
            party_state="Gujarat",  # Simplified
            taxable_amount=job_work_charges,
            cgst_amount=0,
            sgst_amount=0,
            igst_amount=gst_amount,
            total_gst=gst_amount
        )
        db.add(gst_transaction)
        
        db.commit()
        db.refresh(mill_job)
        return mill_job
    
    @staticmethod
    def get_all_mill_jobs(db: Session):
        """Get all mill jobs."""
        return db.query(MillJob).order_by(MillJob.sent_date.desc()).all()
    
    @staticmethod
    def get_pending_mill_jobs(db: Session):
        """Get pending mill jobs (not yet received)."""
        return db.query(MillJob).filter(MillJob.status == "SENT").all()
