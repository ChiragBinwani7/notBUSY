"""Core configuration for the textile accounting system."""

import os
from enum import Enum

# Database configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'textile_accounting.db')}"

# Product definitions (hardcoded)
PRODUCTS = {
    "TAIWAN_BRIGHT": {
        "name": "Taiwan Bright",
        "takas_per_parcel": 4,
        "purchase_by_weight": False
    },
    "BRIGHT_LYCRA": {
        "name": "Bright Lycra",
        "takas_per_parcel": 6,
        "purchase_by_weight": True  # Special case: purchased by weight, takas created on mill receipt
    },
    "ROTO": {
        "name": "Roto",
        "takas_per_parcel": 12,
        "purchase_by_weight": False
    }
}

# Inventory states
class InventoryState(str, Enum):
    GREY_PURCHASED = "GREY_PURCHASED"
    IN_MILL = "IN_MILL"
    IN_SHOP = "IN_SHOP"

# GST transaction types
class GSTTransactionType(str, Enum):
    GREY_PURCHASE = "GREY_PURCHASE"
    MILL_JOB = "MILL_JOB"
    SALE = "SALE"

# GST rates
GST_RATES = {
    "CGST": 0.025,  # 2.5%
    "SGST": 0.025,  # 2.5%
    "IGST": 0.05    # 5%
}

# Gujarat state for GST calculation
GUJARAT_STATE = "Gujarat"

# Freight charges
FREIGHT_PER_PARCEL = 100  # ₹100 per parcel

# Company information (displayed on invoice print)
COMPANY_NAME = "Your Company Name"
COMPANY_TYPE = "Textile Merchant & Fabric Dealer"
COMPANY_ADDRESS = "Surat, Gujarat — 395001"
COMPANY_GSTIN = "24XXXXX0000X1ZX"
COMPANY_PHONE = "+91-XXXXX-XXXXX"
COMPANY_BANK_NAME = "__________________"
COMPANY_BANK_ACCOUNT = "__________________"
COMPANY_BANK_IFSC = "__________________"
