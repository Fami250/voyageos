from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app import models, schemas
from app.dependencies import verify_token  # 🔐 NEW


router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
    dependencies=[Depends(verify_token)]  # 🔒 GLOBAL PROTECTION
)

# =====================================================
# CREATE VENDOR
# =====================================================

@router.post("/", response_model=schemas.VendorResponse)
def create_vendor(
    data: schemas.VendorCreate,
    db: Session = Depends(get_db)
):

    existing = db.query(models.Vendor).filter(
        models.Vendor.name == data.name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Vendor already exists")

    vendor = models.Vendor(
        name=data.name,
        vendor_type=data.vendor_type,
        contact_person=data.contact_person,
        phone=data.phone,
        email=data.email,
        address=data.address
    )

    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    return vendor


# =====================================================
# GET VENDORS (FIXED SERIALIZATION)
# =====================================================

@router.get("/", response_model=List[schemas.VendorResponse])
def get_vendors(db: Session = Depends(get_db)):

    vendors = db.query(models.Vendor).options(
        joinedload(models.Vendor.services)
        .joinedload(models.VendorService.service)
    ).all()

    result = []

    for v in vendors:
        services_list = []

        for mapping in v.services:
            if mapping.service:
                services_list.append({
                    "id": mapping.service.id,
                    "name": mapping.service.name,
                    "category": mapping.service.category
                })

        result.append({
            "id": v.id,
            "name": v.name,
            "vendor_type": v.vendor_type,
            "contact_person": v.contact_person,
            "phone": v.phone,
            "email": v.email,
            "address": v.address,
            "created_at": v.created_at,
            "services": services_list
        })

    return result
