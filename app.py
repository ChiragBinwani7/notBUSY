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
from routes import dashboard, purchases, mill as mill_routes, invoices, payments, gst as gst_routes

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

@app.on_event("startup")
async def startup_event():
    """Initialize database and seed products on startup."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
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
