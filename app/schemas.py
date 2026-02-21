from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from enum import Enum


# =====================================================
# ENUMS
# =====================================================

class QuotationStatus(str, Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    CONFIRMED = "CONFIRMED"
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


class PaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"
    ONLINE = "ONLINE"
    OTHER = "OTHER"


class ServiceCategory(str, Enum):
    HOTEL = "HOTEL"
    TOUR = "TOUR"
    TRANSFER = "TRANSFER"
    VISA = "VISA"
    TICKET = "TICKET"
    OTHER = "OTHER"


# =====================================================
# COUNTRY
# =====================================================

class CountryBase(BaseModel):
    name: str


class CountryCreate(CountryBase):
    pass


class CountryResponse(CountryBase):
    id: int

    class Config:
        from_attributes = True


# =====================================================
# CITY
# =====================================================

class CityBase(BaseModel):
    name: str
    country_id: int


class CityCreate(CityBase):
    pass


class CityResponse(BaseModel):
    id: int
    name: str
    country_id: int
    country: CountryResponse

    class Config:
        from_attributes = True


# =====================================================
# CLIENT
# =====================================================

class ClientBase(BaseModel):
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientResponse(ClientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# SERVICE MINI (for VendorResponse)
# =====================================================

class ServiceMini(BaseModel):
    id: int
    name: str
    category: ServiceCategory

    class Config:
        from_attributes = True


# =====================================================
# VENDOR
# =====================================================

class VendorBase(BaseModel):
    name: str
    vendor_type: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class VendorCreate(VendorBase):
    pass


class VendorResponse(VendorBase):
    id: int
    created_at: datetime
    services: Optional[List[ServiceMini]] = []

    class Config:
        from_attributes = True


# =====================================================
# SERVICE
# =====================================================

class ServiceBase(BaseModel):
    name: str
    category: ServiceCategory
    city_id: int


class ServiceCreate(ServiceBase):
    vendor_ids: Optional[List[int]] = []


class VendorMini(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ServiceResponse(ServiceBase):
    id: int
    created_at: datetime
    vendors: Optional[List[VendorMini]] = []

    class Config:
        from_attributes = True


# =====================================================
# QUOTATION ITEM
# =====================================================

class QuotationItemCreate(BaseModel):
    service_id: int
    vendor_id: Optional[int] = None
    quantity: int = 1
    start_date: date
    end_date: date
    cost_price: float
    manual_margin_percentage: Optional[float] = None


class QuotationItemResponse(BaseModel):
    id: int
    quotation_id: int
    service_id: int
    service_name: Optional[str] = None
    vendor_id: Optional[int] = None
    quantity: int
    start_date: date
    end_date: date
    cost_price: float
    manual_margin_percentage: Optional[float] = None
    sell_price: float
    total_cost: float
    total_sell: float

    # 🔥 ADDED FOR NESTED SERVICE (NO DELETE)
    service: Optional[ServiceResponse] = None

    class Config:
        from_attributes = True


# =====================================================
# QUOTATION
# =====================================================

class QuotationCreate(BaseModel):
    client_id: int
    margin_percentage: Optional[float] = 25
    items: List[QuotationItemCreate]


class QuotationResponse(BaseModel):
    id: int
    quotation_number: str
    client_id: int
    total_cost: float
    total_sell: float
    total_profit: float
    margin_percentage: float
    status: QuotationStatus
    created_at: datetime
    items: List[QuotationItemResponse]

    # 🔥 ADDED FOR CLIENT NAME ACCESS
    client: Optional[ClientResponse] = None

    class Config:
        from_attributes = True


class QuotationStatusUpdate(BaseModel):
    status: QuotationStatus


class DeleteQuotationRequest(BaseModel):
    reason: str


# =====================================================
# INVOICE
# =====================================================

class InvoiceCreate(BaseModel):
    quotation_id: int


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    quotation_id: int
    client_id: int
    total_amount: float
    paid_amount: float
    due_amount: float
    payment_status: PaymentStatus
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# PAYMENT UPDATE
# =====================================================

class PaymentUpdate(BaseModel):
    paid_amount: float
    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


# =====================================================
# INVOICE PAYMENT RESPONSE
# =====================================================

class InvoicePaymentResponse(BaseModel):
    id: int
    invoice_id: int
    payment_date: date
    amount: float
    payment_method: Optional[PaymentMethod] = None
    reference_no: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
