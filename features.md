PROJECT NAME: Local Textile Accounting System

STACK:
- Python FastAPI backend
- SQLite database
- HTML templates frontend
- Localhost only (single user)

GOAL:
Manage textile trading business involving grey purchase, mill job work, inventory, challans, billing, payments and GST.

========================================
PRODUCT RULES
========================================

Main product categories:

1. Taiwan Bright
   - 4 takas per parcel

2. Bright Lycra
   - 6 takas per parcel
   - Purchased by weight, converted to takas after mill

3. Roto
   - 12 takas per parcel

System must track cloth by METERS internally.
Takas and parcels are containers.

Each taka has:
- id
- product_type
- meters
- location (SHOP / MILL / GREY)

========================================
INVENTORY STATES
========================================

Goods can be in only one of:

- GREY_PURCHASED
- IN_MILL
- IN_SHOP

Dashboard must show meters by product in each state.

========================================
PURCHASE FLOW (GREY VENDORS)
========================================

Create Purchase:
- Vendor name
- Vendor state
- Product
- Quantity (takas or weight)
- Purchase value
- GST amount

Status becomes GREY_PURCHASED.

Record payable to vendor.

========================================
MILL JOB WORK
========================================

Send GREY to mill:

Create Mill Job:
- Mill name
- Product
- Grey quantity sent
- Date

Goods become IN_MILL.

Receive from mill:
- Processed takas
- Meters per taka
- Shortage allowed
- Dyeing/job work charges
- GST on job work

Goods become IN_SHOP.

Create mill payable.

========================================
CHALLAN (DISPATCH DOCUMENT)
========================================

Purpose: logistics + internal tracking.

Fields:
- Party name
- City
- Transport
- Date

For each product:
- Number of parcels

System expands parcels → takas.
Print each taka raw meters.

NO FOLD
NO GST
NO FREIGHT

Stock is NOT reduced on challan.

========================================
INVOICE / BILL
========================================

Invoice created from challan or directly.

For EACH product separately:

1. Enter parcel count
2. System calculates takas
3. Sum raw meters
4. Ask fold percentage
5. Calculate:

net_meters = raw_meters - (raw_meters * fold / 100)

Inventory reduced by net_meters.

Freight:
- ₹100 per parcel

GST:
- If Gujarat customer: CGST 2.5% + SGST 2.5%
- Else: IGST 5%

Invoice includes:
- Product value
- Freight
- GST
- Grand total

Create customer receivable.

========================================
PAYMENTS
========================================

Three ledgers:

1. Customers (receivable)
2. Grey Vendors (payable)
3. Mills (payable)

Each ledger:
- Opening balance
- Transactions
- Payments
- Current balance

========================================
GST MODULE
========================================

Track:

Purchases:
- Vendor
- State
- Taxable amount
- CGST / SGST / IGST

Sales:
- Customer
- State
- Taxable amount
- CGST / SGST / IGST

Monthly reports:

1. GSTR-1 (sales)
2. GSTR-3B (summary)
3. Purchase GST summary

Export reports to Excel.

System does NOT auto-file GST.
Only generates summaries.

========================================
DASHBOARD
========================================

Home screen shows:

STOCK:
- Finished meters in shop (by product)
- Meters in mill
- Grey purchased pending

MONEY:
- Total receivable
- Total payable

TODAY:
- Bills created
- Dispatches
- Payments

GST (current month):
- Total sales GST
- Total purchase GST
- Net GST payable

========================================
UI SCREENS
========================================

- Dashboard
- Products
- Purchases
- Mill Jobs
- Challans
- Invoices
- Payments
- GST Reports

Simple HTML forms and tables.
No frontend framework.

========================================
TECH RULES
========================================

- FastAPI
- SQLite
- SQLAlchemy ORM
- Jinja templates
- Clean separation:
  routes/
  models/
  services/

No authentication.
Single local user.

END.
