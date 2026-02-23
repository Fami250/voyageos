from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class SupplierType(str, Enum):
    HOTEL = "HOTEL"
    TOUR = "TOUR"
    TRANSFER = "TRANSFER"
    OTHER = "OTHER"


class SupplierAPIType(str, Enum):
    REST = "REST"
    XML = "XML"
    MANUAL = "MANUAL"


class ExternalSupplierBase(BaseModel):
    name: str
    supplier_type: SupplierType
    api_type: SupplierAPIType = SupplierAPIType.MANUAL
    is_active: Optional[bool] = True


class ExternalSupplierCreate(ExternalSupplierBase):
    pass


class ExternalSupplierUpdate(BaseModel):
    name: Optional[str]
    supplier_type: Optional[SupplierType]
    api_type: Optional[SupplierAPIType]
    is_active: Optional[bool]


class ExternalSupplierOut(ExternalSupplierBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
