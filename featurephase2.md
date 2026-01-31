 PHASE 2 – TEXTILE WORKFLOW FIXES & UI CORRECTIONS

This file overrides parts of features.md.
Core inventory batch + FIFO logic remains unchanged.

================================================
1. PURCHASE → DIRECT SEND TO MILL OPTION
================================================

On New Purchase screen:

Add checkbox:
- "Send directly to Mill"

If checked:
- Show fields:
  - Mill Name
  - Expected Finished Category (dropdown or text)
  - Allow value: TBD

Behavior:

- Purchase is created normally.
- Inventory batch is created in GREY_PURCHASED.
- Immediately auto-create MillJob.
- Batch moves to IN_MILL.

If Expected Finished Category = TBD:
- Mill job remains OPEN.
- Later user can finalize finished category before mill receipt.

================================================
2. MILL JOB MUST SUPPORT RAW → FINISHED VARIANTS
================================================

Textile reality:

We do NOT track generic Bright Lycra.
We track variants:

Examples:
- Bright Lycra 24G
- Bright Lycra 26G
- Bright Lycra 28G
- 24G CXC
Same idea for Taiwan/Roto subcategories.

Changes:

Mill Send Screen:

Instead of only Product:
- Ask:

Raw Category (from available GREY inventory)
Finished Category (dropdown / free text)

Rules:

- Raw Category must be selected from GREY_PURCHASED batches.
- Finished Category defines what inventory batch will be created on mill receipt.

For Bright Lycra:
- Raw is weight
- Finished always creates takas + meters under selected finished category.

If Finished Category = TBD:
- Allow send to mill
- Require category before mill receipt.

Mill Receive Screen:

Must ask:
- Finished Category (mandatory if previously TBD)
- Taka count
- Meters per taka
- Job work charges
- GST

Inventory batch created using Finished Category.

================================================
3. CHALLAN + INVOICE MUST BE A SINGLE FLOW (BILL FIRST)
================================================

Remove separate "Challan" menu.

Replace with:

"BILL / INVOICE"

Workflow:

User clicks "New Bill".

Screen asks in order:

1. Party Name
2. Party City + State
3. Transport Name
4. Invoice Number (auto +1)
5. Category (Taiwan / Lycra / Roto)
6. Finished Product Variant (e.g. Bright Lycra 26G)

Then per product:

7. Selling Price per meter
8. Number of parcels

System calculates:
- Takas = parcels × product.takas_per_parcel

Then:

UI must generate input fields:

"Enter meters for each taka"

Example:
2 parcels Taiwan → 8 taka inputs appear.

User fills all taka meters.

System sums raw meters.

Then:

9. Fold %

Calculate:
net_meters = raw_meters - (raw_meters * fold / 100)

Stock reduction uses net_meters via FIFO.

Challan Print:

- Uses SAME bill data
- Shows:
  - Party
  - Transport
  - Product
  - All taka meters (RAW)
  - Total raw meters
  - Fold shown BUT NOT APPLIED

Invoice Print:

- Uses net_meters
- Shows price, freight, GST, roundoff

IMPORTANT:

Challan is NOT separate entity.
It is just a print format of Invoice.

================================================
MULTI PRODUCT IN SAME BILL
================================================

Allow adding multiple product blocks inside one bill.

For each product block:
- Category
- Finished Variant
- Parcels
- Taka meters
- Fold

Final totals:

- Freight = total parcels × 100 (across ALL products)
- GST calculated ONCE at end
- Roundoff applied once.

================================================
4. PAYMENT MUST BE AGAINST INVOICES (PARTIAL SUPPORTED)
================================================

Payment screen:

First fields:

- Party Type
- Party Name

After Party selected:

System fetches ALL unpaid invoices.

Show table:

Invoice No | Date | Amount | Remaining

User can select multiple invoices.

User enters Payment Amount.

Allocation logic:

Apply payment sequentially:

Example:
Invoice A: 800
Invoice B: 200
Payment: 900

Result:
A cleared
B remaining = 100

Store mapping:
payment_id → invoice_id → applied_amount

Invoice shows remaining_due.

Ledger reflects partials.

================================================
UI SIMPLIFICATION
================================================

Remove separate menus:
- Challans

Navigation:

Dashboard
Purchases
Mill Jobs
Invoices (Bill)
Payments
GST Reports

================================================
END PHASE 2
================================================
