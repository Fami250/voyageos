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
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user


# 🔐 Router WITHOUT global JWT
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

@router.post("/", response_model=schemas.QuotationResponse)
def create_quotation(
    data: schemas.QuotationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

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

@router.put("/{quotation_id}/status")
def update_quotation_status(
    quotation_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
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
# GET SINGLE (🔒 PROTECTED)
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

    return quotation


# =====================================================
# 🌍 LUXURY BROCHURE PDF (PUBLIC)
# =====================================================

@router.get("/{quotation_id}/pdf")
def download_customer_pdf(quotation_id: int, db: Session = Depends(get_db)):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

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

    # ===== DETECT COUNTRY =====
    first_item = quotation.items[0]
    service = db.query(models.Service).filter(
        models.Service.id == first_item.service_id
    ).first()

    city = db.query(models.City).filter(
        models.City.id == service.city_id
    ).first()

    country = db.query(models.Country).filter(
        models.Country.id == city.country_id
    ).first()

    country_name = country.name.lower()

    # ===== LOGO =====
    logo_path = "app/static/uniworld_logo.png"
    if os.path.exists(logo_path):
        img = ImageReader(logo_path)
        iw, ih = img.getSize()
        desired_width = 120
        aspect = ih / iw
        logo = Image(
            logo_path,
            width=desired_width,
            height=desired_width * aspect
        )
        logo.hAlign = 'LEFT'
        elements.append(logo)
        elements.append(Spacer(1, 15))

    # ===== BANNER =====
    jpg_path = f"app/static/countries/{country_name}.jpg"
    png_path = f"app/static/countries/{country_name}.png"
    banner_path = jpg_path if os.path.exists(jpg_path) else png_path

    if os.path.exists(banner_path):
        banner = Image(
            banner_path,
            width=A4[0] - 80,
            height=3 * inch
        )
        banner.hAlign = 'CENTER'
        elements.append(banner)
        elements.append(Spacer(1, 20))

    # ===== HEADER =====
    elements.append(Paragraph(
        f"<b>{country.name} Holiday Package</b>",
        styles["Heading2"]
    ))

    elements.append(Paragraph(
        f"Quotation #: {quotation.quotation_number}",
        styles["Normal"]
    ))

    elements.append(Paragraph(
        f"Date: {quotation.created_at.strftime('%d %B %Y')}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 20))

    # ===== COST TABLE =====
    data = [["Service", "Qty", "Amount"]]

    for item in quotation.items:
        service = db.query(models.Service).filter(
            models.Service.id == item.service_id
        ).first()

        data.append([
            service.name,
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
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # ===== DAY WISE =====
    elements.append(Paragraph("Day Wise Itinerary", styles["Heading2"]))

    grouped = defaultdict(list)

    for item in quotation.items:
        grouped[item.start_date].append(item)

    sorted_dates = sorted(grouped.keys())
    day_counter = 1

    for travel_date in sorted_dates:

        elements.append(
            Paragraph(
                f"<b>Day {day_counter} – {travel_date.strftime('%d %b %Y')}</b>",
                styles["Normal"]
            )
        )

        for item in grouped[travel_date]:
            service = db.query(models.Service).filter(
                models.Service.id == item.service_id
            ).first()

            city = db.query(models.City).filter(
                models.City.id == service.city_id
            ).first()

            elements.append(
                Paragraph(f"• {city.name} – {service.name}", styles["Normal"])
            )

        elements.append(Spacer(1, 8))
        day_counter += 1

    doc.build(elements)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'inline; filename="{quotation.quotation_number}.pdf"'
        }
    )
