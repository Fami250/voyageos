from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app import models

router = APIRouter(
    prefix="/service-rates",
    tags=["Service Rates"]
)

# =====================================
# GET RATES BY SERVICE (SAFE + JOINEDLOAD)
# =====================================

@router.get("/service/{service_id}")
def get_rates_by_service(
    service_id: int,
    db: Session = Depends(get_db)
):

    rates = db.query(models.ServiceRate)\
        .options(joinedload(models.ServiceRate.vendor))\
        .filter(models.ServiceRate.service_id == service_id)\
        .all()

    result = []

    for rate in rates:
        result.append({
            "id": rate.id,
            "service_id": rate.service_id,
            "vendor_id": rate.vendor_id,
            "vendor_name": rate.vendor.name if rate.vendor else "Unknown Vendor",
            "cost_price": float(rate.cost_price),
            "currency": rate.currency,
            "valid_from": rate.valid_from,
            "valid_to": rate.valid_to
        })

    return result
