from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from decimal import Decimal
from collections import defaultdict
from datetime import datetime, date
import os

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

from app.database import get_db
from app import models, schemas
from app.services.external_api.grn import fetch_grn_rate  # 🔥 GRN MOCK

router = APIRouter(prefix="/quotations", tags=["Quotations"])


# =====================================================
# AUTO NUMBER
# =====================================================

def generate_quotation_number(db: Session):
    last = db.query(models.Quotation).order_by(
        models.Quotation.id.desc()
    ).first()

    if not last:
        return "QT-0001"

    try:
        last_number = int(last.quotation_number.split("-")[1])
        return f"QT-{last_number + 1:04d}"
    except:
        return f"QT-{last.id + 1:04d}"


# =====================================================
# CREATE QUOTATION
# =====================================================

@router.post("/", response_model=schemas.QuotationResponse)
def create_quotation(data: schemas.QuotationCreate, db: Session = Depends(get_db)):

    client = db.query(models.Client).filter(
        models.Client.id == data.client_id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    quotation = models.Quotation(
        quotation_number=generate_quotation_number(db),
        client_id=data.client_id,
        margin_percentage=data.margin_percentage or 0,
        status=models.QuotationStatus.DRAFT
    )

    db.add(quotation)
    db.flush()

    total_cost = Decimal("0")
    total_sell = Decimal("0")

    for item in data.items:

        service = db.query(models.Service).filter(
            models.Service.id == item.service_id
        ).first()

        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        # 🔥 Business Rule: Cannot use both vendor and external supplier
        if item.vendor_id and item.external_supplier_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot use both vendor and external supplier for same item"
            )

        # 🔥 External Supplier GRN Logic
        if item.external_supplier_id:
            supplier = db.query(models.ExternalSupplier).filter(
                models.ExternalSupplier.id == item.external_supplier_id
            ).first()

            if not supplier:
                raise HTTPException(status_code=404, detail="External supplier not found")

            if supplier.api_type == models.SupplierAPIType.REST:
                fetched_rate = fetch_grn_rate(item.external_product_id)
                cost_price = Decimal(str(fetched_rate))
            else:
                cost_price = Decimal(str(item.cost_price))
        else:
            cost_price = Decimal(str(item.cost_price))

        margin = Decimal(str(
            item.manual_margin_percentage
            if item.manual_margin_percentage is not None
            else data.margin_percentage or 0
        ))

        sell_price = cost_price + (cost_price * margin / Decimal("100"))

        item_total_cost = cost_price * item.quantity
        item_total_sell = sell_price * item.quantity

        db_item = models.QuotationItem(
            quotation_id=quotation.id,
            service_id=service.id,
            vendor_id=item.vendor_id,
            external_supplier_id=item.external_supplier_id,
            external_product_id=item.external_product_id,
            quantity=item.quantity,
            start_date=item.start_date,
            end_date=item.end_date,
            manual_margin_percentage=item.manual_margin_percentage,
            cost_price=float(cost_price),
            sell_price=float(sell_price),
            total_cost=float(item_total_cost),
            total_sell=float(item_total_sell)
        )

        db.add(db_item)

        total_cost += item_total_cost
        total_sell += item_total_sell

    quotation.total_cost = float(total_cost)
    quotation.total_sell = float(total_sell)
    quotation.total_profit = float(total_sell - total_cost)

    db.commit()
    db.refresh(quotation)

    return quotation


# =====================================================
# (बाकी file unchanged — GET / FILTER / PDF ENGINE same as before)
# =====================================================
