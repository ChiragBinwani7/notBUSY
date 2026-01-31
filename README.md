# Local Textile Accounting System

A FastAPI + SQLite application for managing textile trading business with grey purchase, mill job work, inventory tracking, challans, billing, payments, and GST reporting.

## Features

✅ **Hardcoded Products** (auto-seeded on startup):
- Taiwan Bright (4 takas/parcel)
- Bright Lycra (6 takas/parcel, purchased by weight)
- Roto (12 takas/parcel)

✅ **Inventory Management**:
- Batch-based tracking with `original_meters` and `available_meters`
- FIFO reduction by `created_at` timestamp
- Three states: GREY_PURCHASED → IN_MILL → IN_SHOP

✅ **Purchase Workflow**:
- Grey cloth procurement from vendors
- Special handling for Bright Lycra (weight-based, takas created on mill receipt)
- Vendor ledger tracking

✅ **Mill Job Work**:
- Send grey to mill
- Receive processed cloth with meters per taka
- Mill ledger tracking
- Separate GST tracking for job work

✅ **Challans** (Dispatch Documents):
- Document-only (no inventory mutation)
- Parcel-to-taka expansion calculated on-the-fly
- Print view with meters from available inventory

✅ **Invoices**:
- Fold calculation: `net_meters = raw_meters - (raw_meters * fold / 100)`
- Freight: ₹100 per parcel
- GST: Gujarat (CGST 2.5% + SGST 2.5%), Others (IGST 5%)
- FIFO inventory reduction
- Customer ledger tracking

✅ **Payments & Ledgers**:
- Customer receivables
- Vendor payables
- Mill payables
- Complete transaction history

✅ **GST Reports**:
- GSTR-1 (Sales)
- Purchase GST (separate sections for grey purchases vs mill job work)
- GSTR-3B Summary
- Excel export

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --reload
```

The application will be available at: **http://127.0.0.1:8000**

## First Run

On first startup, the application will:
1. Create the SQLite database (`textile_accounting.db`)
2. Create all tables
3. Auto-seed the three hardcoded products

## Usage

### Dashboard
Visit `http://127.0.0.1:8000` to see:
- Stock summary by product and state
- Money summary (receivables, payables)
- Today's activity
- Current month GST summary

### Workflow

1. **Create Purchase**:
   - Navigate to Purchases → New Purchase
   - For Taiwan Bright/Roto: Enter quantity in takas
   - For Bright Lycra: Enter quantity in kg
   - Inventory batches created automatically (except Bright Lycra)

2. **Send to Mill**:
   - Navigate to Mill Jobs → Send to Mill
   - Select product and quantity
   - Batches move from GREY_PURCHASED to IN_MILL

3. **Receive from Mill**:
   - Navigate to Mill Jobs → Click "Receive" on pending job
   - Enter processed takas, meters per taka, charges
   - For Bright Lycra: Inventory batches created here
   - Batches move to IN_SHOP

4. **Create Challan** (Optional):
   - Navigate to Challans → New Challan
   - Document-only, no inventory changes
   - Print view shows taka expansion

5. **Create Invoice**:
   - Navigate to Invoices → New Invoice
   - Enter customer details
   - Specify parcels, fold %, rate per meter
   - System calculates:
     - Raw meters from parcels
     - Net meters after fold reduction
     - Freight (₹100 per parcel)
     - GST based on customer state
   - Inventory reduced using FIFO

6. **Record Payments**:
   - Navigate to Payments → Record Payment
   - Select party type (Customer/Vendor/Mill)
   - Enter amount and payment method
   - View ledgers for transaction history

7. **GST Reports**:
   - Navigate to GST Reports
   - View GSTR-1, Purchase GST, GSTR-3B
   - Export to Excel

## Key Business Rules

### Inventory Batches
- Stored as batches (not individual takas)
- `original_meters`: Initial meters in batch
- `available_meters`: Remaining after consumption
- FIFO reduction: Oldest batches consumed first

### Bright Lycra Special Case
- Purchased by weight (kg)
- NO inventory batches created on purchase
- Batches created on mill receipt with taka count

### Fold Calculation
```
net_meters = raw_meters - (raw_meters * fold_percent / 100)
```

### GST Calculation
- **Gujarat customers**: CGST 2.5% + SGST 2.5% = 5% total
- **Other states**: IGST 5%
- **Separate tracking**: Grey purchases vs mill job work

### Challan
- Document only
- No DB-level taka expansion
- No inventory mutation
- Taka details calculated on-the-fly for display

## Project Structure

```
notBUSY/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── core/
│   ├── config.py         # Configuration and constants
│   └── database.py       # Database setup
├── models/               # SQLAlchemy models
│   ├── product.py
│   ├── inventory.py      # InventoryBatch model
│   ├── purchase.py
│   ├── mill.py
│   ├── challan.py
│   ├── invoice.py
│   ├── payment.py        # Ledger models
│   └── gst.py
├── services/             # Business logic
│   ├── inventory_service.py
│   ├── purchase_service.py
│   ├── mill_service.py
│   ├── challan_service.py
│   ├── invoice_service.py
│   ├── payment_service.py
│   ├── gst_service.py
│   └── dashboard_service.py
├── routes/               # API endpoints
│   ├── dashboard.py
│   ├── purchases.py
│   ├── mill.py
│   ├── challans.py
│   ├── invoices.py
│   ├── payments.py
│   └── gst.py
├── templates/            # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── purchases/
│   ├── mill/
│   ├── challans/
│   ├── invoices/
│   ├── payments/
│   └── gst/
├── static/
│   └── style.css         # CSS styling
└── exports/              # Excel exports (auto-created)
```

## Database

SQLite database: `textile_accounting.db`

Tables:
- `products` - Hardcoded product types
- `inventory_batches` - Inventory tracking with FIFO
- `purchases` - Grey cloth purchases
- `mill_jobs` - Mill job work tracking
- `challans` - Dispatch documents
- `invoices` - Sales invoices
- `vendor_ledgers` - Vendor payables
- `mill_ledgers` - Mill payables
- `customer_ledgers` - Customer receivables
- `payments` - Payment transactions
- `gst_transactions` - GST tracking (separate types)

## Notes

- **No Authentication**: Single local user system
- **No Product CRUD**: Products are hardcoded and auto-seeded
- **Localhost Only**: Designed for single-user local deployment
- **Excel Export**: GST reports can be exported to Excel in `exports/` folder

## Future Enhancements

- Dynamic line item forms (currently simplified)
- Advanced reporting and analytics
- Backup and restore functionality
- Multi-user support with authentication
- Cloud deployment options
