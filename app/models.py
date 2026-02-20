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
    CANCELLED = "CANCELLED"   # ✅ FIXED (was missing)
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


# =====================================================
# COUNTRY
# =====================================================

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    cities = relationship(
        "City",
        back_populates="country",
        cascade="all, delete-orphan"
    )


# =====================================================
# CITY
# =====================================================

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    country_id = Column(
        Integer,
        ForeignKey("countries.id", ondelete="CASCADE"),
        nullable=False
    )

    country = relationship("Country", back_populates="cities")
    services = relationship("Service", back_populates="city")


# =====================================================
# CLIENT
# =====================================================

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_person = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    quotations = relationship("Quotation", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")


# =====================================================
# VENDOR
# =====================================================

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    vendor_type = Column(String)

    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    services = relationship(
        "VendorService",
        back_populates="vendor",
        cascade="all, delete-orphan"
    )

    quotation_items = relationship("QuotationItem", back_populates="vendor")


# =====================================================
# SERVICE
# =====================================================

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    category = Column(Enum(ServiceCategory), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    itinerary_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    city = relationship("City", back_populates="services")

    vendors = relationship(
        "VendorService",
        back_populates="service",
        cascade="all, delete-orphan"
    )

    quotation_items = relationship("QuotationItem", back_populates="service")


# =====================================================
# VENDOR SERVICE
# =====================================================

class VendorService(Base):
    __tablename__ = "vendor_services"

    id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    vendor = relationship("Vendor", back_populates="services")
    service = relationship("Service", back_populates="vendors")


# =====================================================
# QUOTATION
# =====================================================

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String, unique=True, index=True)

    client_id = Column(Integer, ForeignKey("clients.id"))

    total_cost = Column(Float, default=0)
    total_sell = Column(Float, default=0)
    total_profit = Column(Float, default=0)

    margin_percentage = Column(Float, default=25)

    status = Column(
        Enum(QuotationStatus),
        default=QuotationStatus.DRAFT,
        nullable=False
    )

    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    delete_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="quotations")

    items = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete-orphan"
    )

    invoice = relationship(
        "Invoice",
        back_populates="quotation",
        uselist=False
    )


# =====================================================
# QUOTATION ITEM
# =====================================================

class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True)

    quotation_id = Column(Integer, ForeignKey("quotations.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    vendor_id = Column(Integer, ForeignKey("vendors.id"))

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


# =====================================================
# INVOICE
# =====================================================

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True)

    quotation_id = Column(Integer, ForeignKey("quotations.id"), unique=True)
    client_id = Column(Integer, ForeignKey("clients.id"))

    total_amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    due_amount = Column(Float, default=0)

    payment_status = Column(
        Enum(PaymentStatus),
        default=PaymentStatus.UNPAID,
        nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    quotation = relationship("Quotation", back_populates="invoice")
    client = relationship("Client", back_populates="invoices")

    payments = relationship(
        "InvoicePayment",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )


# =====================================================
# INVOICE PAYMENT
# =====================================================

class InvoicePayment(Base):
    __tablename__ = "invoice_payments"

    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String, unique=True, index=True)

    invoice_id = Column(Integer, ForeignKey("invoices.id"))

    payment_date = Column(Date, default=date.today)
    amount = Column(Float, nullable=False)

    payment_method = Column(
        Enum(PaymentMethod),
        default=PaymentMethod.CASH
    )

    reference_no = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="payments")
