from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date
import os
from collections import defaultdict

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user


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
# FILTER BY DATE (🔒)
# =====================================================

@router.get("/filter/by-date", response_model=list[schemas.QuotationResponse])
def filter_quotations_by_date(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return db.query(models.Quotation).filter(
        func.date(models.Quotation.created_at) >= start_date,
        func.date(models.Quotation.created_at) <= end_date
    ).order_by(models.Quotation.id.desc()).all()


# =====================================================
# GET SINGLE (🔒)
# =====================================================

@router.get("/{quotation_id}", response_model=schemas.QuotationResponse)
def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    # Inject service_name for frontend
    for item in quotation.items:
        service = db.query(models.Service).filter(
            models.Service.id == item.service_id
        ).first()
        setattr(item, "service_name", service.name if service else "Service")

    return quotation


# =====================================================
# PDF (🌍 LUXURY BROCHURE – PUBLIC)
# =====================================================

@router.get("/{quotation_id}/pdf")
def download_customer_pdf(quotation_id: int, db: Session = Depends(get_db)):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    if not quotation.items:
        raise HTTPException(status_code=400, detail="No services in quotation")

    file_path = f"quotation_{quotation_id}.pdf"

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=50
    )

    elements = []
    styles = getSampleStyleSheet()

    # ===== HEADER =====
    elements.append(
        Paragraph(f"<b>Quotation #{quotation.quotation_number}</b>", styles["Heading2"])
    )
    elements.append(
        Paragraph(f"Date: {quotation.created_at.strftime('%d %B %Y')}", styles["Normal"])
    )
    elements.append(Spacer(1, 20))

    # ===== COST TABLE =====
    data = [["Service", "Qty", "Amount"]]

    for item in quotation.items:
        service = db.query(models.Service).filter(
            models.Service.id == item.service_id
        ).first()

        data.append([
            service.name if service else "Service",
            str(item.quantity),
            f"{item.total_sell:,.0f}"
        ])

    data.append(["Total Package Cost", "", f"{quotation.total_sell:,.0f}"])

    table = Table(
        data,
        colWidths=[4.2 * inch, 0.8 * inch, 1.5 * inch],
        hAlign="LEFT"
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163E82")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'inline; filename="{quotation.quotation_number}.pdf"'
        }
    )
