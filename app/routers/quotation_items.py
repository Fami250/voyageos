from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/quotation-items",
    tags=["Quotation Items"]
)


# =====================================================
# CREATE QUOTATION ITEM
# =====================================================

@router.post("/", response_model=schemas.QuotationItemResponse)
def create_quotation_item(
    data: schemas.QuotationItemCreate,
    db: Session = Depends(get_db)
):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == data.quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    service = db.query(models.Service).filter(
        models.Service.id == data.service_id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Example pricing logic (simplified)
    cost_price = Decimal(data.manual_fare or 0)
    margin_percent = Decimal(data.manual_margin_percentage or 0)

    sell_price = cost_price + (cost_price * margin_percent / 100)

    total_cost = cost_price * data.quantity
    total_sell = sell_price * data.quantity

    item = models.QuotationItem(
        quotation_id=data.quotation_id,
        service_id=data.service_id,
        quantity=data.quantity,
        start_date=data.start_date,
        end_date=data.end_date,
        manual_fare=data.manual_fare,
        manual_margin_percentage=data.manual_margin_percentage,
        cost_price=float(cost_price),
        sell_price=float(sell_price),
        total_cost=float(total_cost),
        total_sell=float(total_sell)
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    # 🔥 Recalculate quotation totals
    items = db.query(models.QuotationItem).filter(
        models.QuotationItem.quotation_id == quotation.id
    ).all()

    quotation.total_cost = sum(i.total_cost for i in items)
    quotation.total_sell = sum(i.total_sell for i in items)
    quotation.total_profit = quotation.total_sell - quotation.total_cost

    if quotation.total_cost > 0:
        quotation.margin_percentage = (
            quotation.total_profit / quotation.total_cost
        ) * 100

    db.commit()
    db.refresh(quotation)

    return item
