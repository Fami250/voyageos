from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import pandas as pd

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/services",
    tags=["Services"]
)

# =====================================================
# CREATE SERVICE (WITH VENDOR MAPPING)
# =====================================================

@router.post("/", response_model=schemas.ServiceResponse)
def create_service(
    data: schemas.ServiceCreate,
    db: Session = Depends(get_db)
):

    # Validate City
    city = db.query(models.City).filter(
        models.City.id == data.city_id
    ).first()

    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Validate Category
    try:
        category_enum = models.ServiceCategory[data.category]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid category")

    # Duplicate Check
    existing = db.query(models.Service).filter(
        models.Service.name == data.name,
        models.Service.city_id == data.city_id,
        models.Service.category == category_enum
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Service already exists")

    # Create Service
    new_service = models.Service(
        name=data.name,
        category=category_enum,
        city_id=data.city_id
    )

    db.add(new_service)
    db.flush()

    # Vendor Mapping
    if data.vendor_ids:
        for vendor_id in data.vendor_ids:

            vendor = db.query(models.Vendor).filter(
                models.Vendor.id == vendor_id
            ).first()

            if not vendor:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vendor {vendor_id} not found"
                )

            mapping = models.VendorService(
                vendor_id=vendor_id,
                service_id=new_service.id
            )

            db.add(mapping)

    db.commit()

    # Reload with join
    service = db.query(models.Service).options(
        joinedload(models.Service.vendors)
        .joinedload(models.VendorService.vendor)
    ).filter(
        models.Service.id == new_service.id
    ).first()

    # 🔥 IMPORTANT FIX: MANUAL RESPONSE FORMAT
    return {
        "id": service.id,
        "name": service.name,
        "category": service.category,
        "city_id": service.city_id,
        "created_at": service.created_at,
        "vendors": [
            {
                "id": vs.vendor.id,
                "name": vs.vendor.name
            }
            for vs in service.vendors
        ]
    }


# =====================================================
# GET SERVICES
# =====================================================

@router.get("/", response_model=List[schemas.ServiceResponse])
def get_services(
    city_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):

    services = db.query(models.Service).options(
        joinedload(models.Service.vendors)
        .joinedload(models.VendorService.vendor)
    )

    if city_id:
        services = services.filter(models.Service.city_id == city_id)

    if category:
        try:
            category_enum = models.ServiceCategory[category.upper()]
            services = services.filter(models.Service.category == category_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid category")

    services = services.all()

    result = []

    for service in services:
        result.append({
            "id": service.id,
            "name": service.name,
            "category": service.category,
            "city_id": service.city_id,
            "created_at": service.created_at,
            "vendors": [
                {
                    "id": vs.vendor.id,
                    "name": vs.vendor.name
                }
                for vs in service.vendors
            ]
        })

    return result


# =====================================================
# DELETE SERVICE
# =====================================================

@router.delete("/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):

    service = db.query(models.Service).filter(
        models.Service.id == service_id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    used = db.query(models.QuotationItem).filter(
        models.QuotationItem.service_id == service_id
    ).first()

    if used:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete service. It is used in quotations."
        )

    db.delete(service)
    db.commit()

    return {"message": "Service deleted successfully"}
# =====================================================
# FILTER SERVICES BY CITY + CATEGORY
# =====================================================

@router.get("/filter")
def filter_services(
    city_id: int,
    category: models.ServiceCategory,
    db: Session = Depends(get_db)
):
    services = db.query(models.Service).filter(
        models.Service.city_id == city_id,
        models.Service.category == category
    ).order_by(models.Service.name.asc()).all()

    return services

