from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date
import os

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user


# ❌ GLOBAL JWT REMOVED
router = APIRouter(
    prefix="/quotations",
    tags=["Quotations"]
)

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
# CREATE QUOTATION (🔒 PROTECTED)
# =====================================================

@router.post("/", response_model=schemas.QuotationResponse,
             dependencies=[Depends(get_current_user)])
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
            quantity=item.quantity,
            start_date=item.start_date,
            end_date=item.end_date,
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
# UPDATE STATUS (🔒 PROTECTED)
# =====================================================

@router.put("/{quotation_id}/status",
            dependencies=[Depends(get_current_user)])
def update_quotation_status(
    quotation_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    new_status = payload.get("status")

    if new_status not in models.QuotationStatus.__members__:
        raise HTTPException(status_code=400, detail="Invalid status")

    quotation.status = models.QuotationStatus[new_status]

    db.commit()
    db.refresh(quotation)

    return {"message": "Status updated successfully"}


# =====================================================
# FILTER BY DATE (🔒 PROTECTED)
# =====================================================

@router.get("/filter/by-date",
            response_model=list[schemas.QuotationResponse],
            dependencies=[Depends(get_current_user)])
def filter_quotations_by_date(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):

    quotations = db.query(models.Quotation).filter(
        func.date(models.Quotation.created_at) >= start_date,
        func.date(models.Quotation.created_at) <= end_date
    ).all()

    return quotations


# =====================================================
# GET SINGLE (🔒 PROTECTED)
# =====================================================

@router.get("/{quotation_id}",
            response_model=schemas.QuotationResponse,
            dependencies=[Depends(get_current_user)])
def get_quotation(quotation_id: int, db: Session = Depends(get_db)):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    return quotation


# =====================================================
# PDF ENGINE (🌍 PUBLIC ACCESS)
# =====================================================

@router.get("/{quotation_id}/pdf")
def download_customer_pdf(quotation_id: int, db: Session = Depends(get_db)):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    file_path = f"quotation_{quotation_id}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(
        f"<b>Quotation #{quotation.quotation_number}</b>",
        styles["Heading2"]
    ))

    doc.build(elements)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'inline; filename="{quotation.quotation_number}.pdf"'
        }
    )
