# tickapp/models.py
from dataclasses import dataclass
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

# ============================================================================
# MODELS SIGNAL
# ============================================================================

# ============================================================================
# MODELS RECEIPT (Magasins, Transactions, Articles)
# ============================================================================

@dataclass
class Store:
    """Magasin"""
    store_name: str
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = None
    phone: Optional[str] = None

@dataclass
class Transaction:
    """Transaction (ticket de caisse)"""
    store_id: int  # Sera rempli après insertion du store
    message_id: Optional[int] = None
    transaction_category_id: Optional[int] = None  # Catégorie de dépense (spend) - ID
    transaction_category_name: Optional[str] = None  # Catégorie de dépense (spend) - Nom (sera converti en lowercase)
    receipt_number: Optional[str] = None
    transaction_date: date = None
    transaction_time: Optional[time] = None
    currency: str = None
    total: Decimal = None
    payment_method: Optional[str] = None
    source: str = "signal"

@dataclass
class Item:
    """Article d'un ticket"""
    transaction_id: int  # Sera rempli après insertion de la transaction
    product_name: str
    product_reference: Optional[str] = None
    brand: Optional[str] = None
    quantity: Decimal = None
    unit_price: Decimal = None
    total_price: Decimal = None
    vat_rate: Optional[str] = None
    category_main: str = None
    category_sub: str = None
    line_number: int = None

@dataclass
class Category:
    """Catégorie de dépense"""
    category_main: str
    category_sub: str
    description: Optional[str] = None
    active: bool = True

# ============================================================================
# MODELS COMPOSÉS (pour faciliter les retours de fonctions)
# ============================================================================

@dataclass
class ReceiptData:
    """Données complètes d'un ticket"""
    store: Store
    transaction: Transaction
    items: List[Item]