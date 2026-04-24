"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from core.database import engine, Base, SessionLocal
from core.config import PRODUCTS
from models.product import Product

# Import all models to ensure they're registered with Base
from models import product, inventory, purchase, mill, invoice, invoice_payment, payment, gst

# Import routes
from routes import dashboard, purchases, mill as mill_routes, invoices, payments, gst as gst_routes, reports as reports_routes

# Create FastAPI app
app = FastAPI(title="Local Textile Accounting System")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(dashboard.router)
app.include_router(purchases.router)
app.include_router(mill_routes.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(gst_routes.router)
app.include_router(reports_routes.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database and seed products on startup."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Run schema migrations for columns added after initial creation
    from sqlalchemy import text
    with engine.connect() as conn:
        # ---------- inventory_batches ----------
        result = conn.execute(text("PRAGMA table_info(inventory_batches)"))
        existing_cols = {row[1] for row in result.fetchall()}
        if "finished_variant" not in existing_cols:
            conn.execute(text("ALTER TABLE inventory_batches ADD COLUMN finished_variant VARCHAR"))
            conn.commit()

        # ---------- mill_jobs ----------
        result = conn.execute(text("PRAGMA table_info(mill_jobs)"))
        existing_cols = {row[1] for row in result.fetchall()}
        if "raw_category" not in existing_cols:
            conn.execute(text("ALTER TABLE mill_jobs ADD COLUMN raw_category VARCHAR"))
            conn.commit()
        if "finished_variant" not in existing_cols:
            conn.execute(text("ALTER TABLE mill_jobs ADD COLUMN finished_variant VARCHAR NOT NULL DEFAULT 'TBD'"))
            conn.commit()
        if "variant_finalized" not in existing_cols:
            conn.execute(text("ALTER TABLE mill_jobs ADD COLUMN variant_finalized BOOLEAN NOT NULL DEFAULT 0"))
            conn.commit()

        # ---------- invoices ----------
        result = conn.execute(text("PRAGMA table_info(invoices)"))
        existing_cols = {row[1] for row in result.fetchall()}
        if "transport_name" not in existing_cols:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN transport_name VARCHAR NOT NULL DEFAULT ''"))
            conn.commit()
        if "invoice_number" not in existing_cols:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN invoice_number VARCHAR"))
            conn.commit()
            # Back-fill invoice numbers for existing rows
            conn.execute(text(
                "UPDATE invoices SET invoice_number = 'INV-' || strftime('%Y%m%d', invoice_date) || '-' || printf('%03d', id) "
                "WHERE invoice_number IS NULL"
            ))
            conn.commit()
        if "total_parcels" not in existing_cols:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN total_parcels INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
        if "remaining_due" not in existing_cols:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN remaining_due FLOAT NOT NULL DEFAULT 0"))
            conn.commit()
            # Back-fill remaining_due = grand_total for existing rows
            conn.execute(text("UPDATE invoices SET remaining_due = grand_total WHERE remaining_due = 0"))
            conn.commit()
        if "payment_status" not in existing_cols:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN payment_status VARCHAR NOT NULL DEFAULT 'UNPAID'"))
            conn.commit()
        if "payment_terms_days" not in existing_cols:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN payment_terms_days INTEGER NOT NULL DEFAULT 30"))
            conn.commit()
        if "due_date" not in existing_cols:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN due_date DATETIME"))
            conn.commit()
            # Back-fill due_date = invoice_date + 30 days
            conn.execute(text(
                "UPDATE invoices SET due_date = datetime(invoice_date, '+30 days') WHERE due_date IS NULL"
            ))
            conn.commit()

        # ---------- purchases ----------
        result = conn.execute(text("PRAGMA table_info(purchases)"))
        existing_cols = {row[1] for row in result.fetchall()}
        if "send_to_mill" not in existing_cols:
            conn.execute(text("ALTER TABLE purchases ADD COLUMN send_to_mill BOOLEAN NOT NULL DEFAULT 0"))
            conn.commit()
        if "mill_name" not in existing_cols:
            conn.execute(text("ALTER TABLE purchases ADD COLUMN mill_name VARCHAR"))
            conn.commit()
        if "expected_finished_variant" not in existing_cols:
            conn.execute(text("ALTER TABLE purchases ADD COLUMN expected_finished_variant VARCHAR"))
            conn.commit()
    
    # Seed products if not already present
    db = SessionLocal()
    try:
        existing_products = db.query(Product).count()
        if existing_products == 0:
            for code, details in PRODUCTS.items():
                product = Product(
                    code=code,
                    name=details["name"],
                    takas_per_parcel=details["takas_per_parcel"],
                    purchase_by_weight=details["purchase_by_weight"]
                )
                db.add(product)
            db.commit()
            print("Products seeded successfully")
        else:
            print(f"Database already has {existing_products} products")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
