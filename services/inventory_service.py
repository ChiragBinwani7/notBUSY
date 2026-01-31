"""Inventory batch management service with FIFO reduction."""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.inventory import InventoryBatch
from models.product import Product
from core.config import InventoryState
from datetime import datetime

class InventoryService:
    """Service for managing inventory batches with FIFO reduction."""
    
    @staticmethod
    def create_batch(
        db: Session,
        product_id: int,
        original_meters: float,
        taka_count: int,
        location_state: str,
        finished_variant: str = None,
        purchase_id: int = None,
        mill_job_id: int = None
    ) -> InventoryBatch:
        """Create a new inventory batch."""
        batch = InventoryBatch(
            product_id=product_id,
            original_meters=original_meters,
            available_meters=original_meters,  # Initially same as original
            taka_count=taka_count,
            location_state=location_state,
            finished_variant=finished_variant,
            purchase_id=purchase_id,
            mill_job_id=mill_job_id,
            created_at=datetime.utcnow()
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch
    
    @staticmethod
    def move_batches_to_state(
        db: Session,
        batch_ids: list,
        new_state: str
    ):
        """Move batches to a new state."""
        batches = db.query(InventoryBatch).filter(InventoryBatch.id.in_(batch_ids)).all()
        for batch in batches:
            batch.location_state = new_state
        db.commit()
    
    @staticmethod
    def get_stock_summary(db: Session):
        """Get stock summary by product and state."""
        summary = {}
        
        products = db.query(Product).all()
        for product in products:
            summary[product.name] = {
                "GREY_PURCHASED": {"meters": 0, "takas": 0},
                "IN_MILL": {"meters": 0, "takas": 0},
                "IN_SHOP": {"meters": 0, "takas": 0}
            }
            
            for state in [InventoryState.GREY_PURCHASED, InventoryState.IN_MILL, InventoryState.IN_SHOP]:
                batches = db.query(InventoryBatch).filter(
                    and_(
                        InventoryBatch.product_id == product.id,
                        InventoryBatch.location_state == state.value,
                        InventoryBatch.available_meters > 0
                    )
                ).all()
                
                total_meters = sum(b.available_meters for b in batches)
                total_takas = sum(b.taka_count for b in batches)
                
                summary[product.name][state.value] = {
                    "meters": total_meters,
                    "takas": total_takas
                }
        
        return summary
    
    @staticmethod
    def reduce_inventory_fifo(
        db: Session,
        product_id: int,
        finished_variant: str,
        meters_to_reduce: float
    ) -> list:
        """
        Reduce inventory using FIFO (oldest batches first by created_at).
        CRITICAL: Filters by both product_id AND finished_variant.
        Excludes batches with finished_variant = "TBD".
        Returns list of batch IDs that were affected.
        """
        # Get available batches in FIFO order (oldest first)
        # MUST match exact variant and exclude TBD
        batches = db.query(InventoryBatch).filter(
            and_(
                InventoryBatch.product_id == product_id,
                InventoryBatch.finished_variant == finished_variant,
                InventoryBatch.finished_variant != "TBD",
                InventoryBatch.location_state == InventoryState.IN_SHOP.value,
                InventoryBatch.available_meters > 0
            )
        ).order_by(InventoryBatch.created_at.asc()).all()
        
        remaining_to_reduce = meters_to_reduce
        affected_batch_ids = []
        
        for batch in batches:
            if remaining_to_reduce <= 0:
                break
            
            if batch.available_meters >= remaining_to_reduce:
                # This batch can fulfill the remaining requirement
                batch.available_meters -= remaining_to_reduce
                affected_batch_ids.append(batch.id)
                remaining_to_reduce = 0
            else:
                # Consume entire batch and continue
                remaining_to_reduce -= batch.available_meters
                batch.available_meters = 0
                affected_batch_ids.append(batch.id)
        
        if remaining_to_reduce > 0:
            raise ValueError(f"Insufficient inventory. Need {meters_to_reduce} meters, but only {meters_to_reduce - remaining_to_reduce} available.")
        
        db.commit()
        return affected_batch_ids
    
    @staticmethod
    def get_available_inventory(
        db: Session,
        product_id: int,
        state: str = InventoryState.IN_SHOP.value
    ):
        """Get available inventory for a product in a specific state."""
        batches = db.query(InventoryBatch).filter(
            and_(
                InventoryBatch.product_id == product_id,
                InventoryBatch.location_state == state,
                InventoryBatch.available_meters > 0
            )
        ).order_by(InventoryBatch.created_at.asc()).all()
        
        total_meters = sum(b.available_meters for b in batches)
        total_takas = sum(b.taka_count for b in batches)
        
        return {
            "batches": batches,
            "total_meters": total_meters,
            "total_takas": total_takas
        }
    
    @staticmethod
    def get_available_variants(db: Session, product_id: int):
        """
        Get list of available finished variants for a product.
        Excludes "TBD" variants.
        Used for billing dropdown/selection.
        """
        from sqlalchemy import distinct
        
        variants = db.query(distinct(InventoryBatch.finished_variant)).filter(
            and_(
                InventoryBatch.product_id == product_id,
                InventoryBatch.location_state == InventoryState.IN_SHOP.value,
                InventoryBatch.finished_variant.isnot(None),
                InventoryBatch.finished_variant != "TBD",
                InventoryBatch.available_meters > 0
            )
        ).all()
        
        return [v[0] for v in variants if v[0]]
