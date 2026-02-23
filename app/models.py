from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey, Date, Enum, Text, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base
import enum


# =====================================================
# ENUMS
# =====================================================

class QuotationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    CONFIRMED = "CONFIRMED"
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"
    ONLINE = "ONLINE"
    OTHER = "OTHER"


class ServiceCategory(str, enum.Enum):
    HOTEL = "HOTEL"
    TOUR = "TOUR"
    TRANSFER = "TRANSFER"
    VISA = "VISA"
    TICKET = "TICKET"
    OTHER = "OTHER"


class SupplierType(str, enum.Enum):
    HOTEL = "HOTEL"
    TOUR = "TOUR"
    TRANSFER = "TRANSFER"
    OTHER = "OTHER"


class SupplierAPIType(str, enum.Enum):
    REST = "REST"
    XML = "XML"
    MANUAL = "MANUAL"


# =====================================================
# EXTERNAL SUPPLIER (NEW FOUNDATION)
# =====================================================

class ExternalSupplier(Base):
    __tablename__ = "external_suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    supplier_type = Column(Enum(SupplierType), nullable=False)
    api_type = Column(Enum(SupplierAPIType), default=SupplierAPIType.MANUAL)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship(
        "ExternalProduct",
        back_populates="supplier",
        cascade="all, delete-orphan"
    )


class ExternalProduct(Base):
    __tablename__ = "external_products"

    id = Column(Integer, primary_key=True, index=True)

    supplier_id = Column(Integer, ForeignKey("external_suppliers.id"))
    external_product_id = Column(String, nullable=False)

    name = Column(String, nullable=False)
    city_name = Column(String)
    country_name = Column(String)

    last_known_price = Column(Float)
    currency = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("ExternalSupplier", back_populates="products")


# =====================================================
# EXISTING MODELS (UNCHANGED BELOW)
# =====================================================

# ---- KEEP EVERYTHING BELOW EXACT SAME AS YOUR ORIGINAL ----
# (Country, City, Client, Vendor, Service, VendorService,
#  Quotation, QuotationItem, Invoice, InvoicePayment)

# ONLY CHANGE inside QuotationItem below 👇


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True)

    quotation_id = Column(Integer, ForeignKey("quotations.id"))
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)

    # 🔥 NEW (External integration ready)
    external_supplier_id = Column(Integer, ForeignKey("external_suppliers.id"), nullable=True)
    external_product_id = Column(String, nullable=True)

    quantity = Column(Integer, default=1)

    start_date = Column(Date)
    end_date = Column(Date)

    manual_margin_percentage = Column(Float, nullable=True)

    cost_price = Column(Float)
    sell_price = Column(Float)

    total_cost = Column(Float)
    total_sell = Column(Float)

    quotation = relationship("Quotation", back_populates="items")
    service = relationship("Service", back_populates="quotation_items")
    vendor = relationship("Vendor", back_populates="quotation_items")
