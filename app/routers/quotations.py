from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date, timedelta
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
# UPDATE STATUS + AUTO INVOICE
# =====================================================

@router.put("/{quotation_id}/status")
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

    if new_status == "CONFIRMED":

        existing_invoice = db.query(models.Invoice).filter(
            models.Invoice.quotation_id == quotation.id
        ).first()

        if not existing_invoice:
            invoice = models.Invoice(
                invoice_number=f"INV-{quotation.id:04d}",
                quotation_id=quotation.id,
                client_id=quotation.client_id,
                total_amount=quotation.total_sell,
                paid_amount=0,
                due_amount=quotation.total_sell,
                payment_status=models.PaymentStatus.UNPAID
            )
            db.add(invoice)

    db.commit()
    db.refresh(quotation)

    return {"message": "Status updated successfully"}


# =====================================================
# FILTER BY DATE
# =====================================================

@router.get("/filter/by-date", response_model=list[schemas.QuotationResponse])
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
# GET SINGLE (SERVICE FIX)
# =====================================================

@router.get("/{quotation_id}", response_model=schemas.QuotationResponse)
def get_quotation(quotation_id: int, db: Session = Depends(get_db)):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    for item in quotation.items:
        service = db.query(models.Service).filter(
            models.Service.id == item.service_id
        ).first()
        setattr(item, "service_name", service.name if service else "Service")

    return quotation


# =====================================================
# PDF (WITH FULL ITINERARY RESTORED)
# =====================================================

@router.get("/{quotation_id}/pdf")
def download_customer_pdf(quotation_id: int, db: Session = Depends(get_db)):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    if not quotation.items:
        raise HTTPException(status_code=400, detail="No items in quotation")

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

    wrap_style = ParagraphStyle(
        "wrap",
        parent=styles["Normal"],
        wordWrap="CJK"
    )

    # ===== DETECT COUNTRY =====
    first_item = quotation.items[0]
    service_obj = db.query(models.Service).filter(
        models.Service.id == first_item.service_id
    ).first()

    city = db.query(models.City).filter(
        models.City.id == service_obj.city_id
    ).first()

    country = db.query(models.Country).filter(
        models.Country.id == city.country_id
    ).first()

    country_name = country.name.lower()

    # ===== LOGO =====
    logo_path = "app/static/uniworld_logo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=120, height=40)
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
    data = [
        [
            Paragraph("<b>Service</b>", styles["Normal"]),
            Paragraph("<b>Qty</b>", styles["Normal"]),
            Paragraph("<b>Amount</b>", styles["Normal"])
        ]
    ]

    for item in quotation.items:
        service = db.query(models.Service).filter(
            models.Service.id == item.service_id
        ).first()

        data.append([
            Paragraph(service.name if service else "Service", wrap_style),
            Paragraph(str(item.quantity), styles["Normal"]),
            Paragraph(f"{item.total_sell:,.0f}", styles["Normal"])
        ])

    data.append([
        Paragraph("<b>Total Package Cost</b>", styles["Normal"]),
        "",
        Paragraph(f"<b>{quotation.total_sell:,.0f}</b>", styles["Normal"])
    ])

    table = Table(data, colWidths=[4 * inch, 0.8 * inch, 1.2 * inch], repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163E82")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))

    # ===== DAY WISE ITINERARY RESTORED =====
    elements.append(Paragraph("<b>Day Wise Itinerary</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    day_counter = 1

    for item in quotation.items:

        service = db.query(models.Service).filter(
            models.Service.id == item.service_id
        ).first()

        city = db.query(models.City).filter(
            models.City.id == service.city_id
        ).first()

        start = item.start_date
        end = item.end_date

        if not start or not end:
            continue

        current_date = start

        while current_date <= end:

            elements.append(
                Paragraph(
                    f"<b>Day {day_counter} – {current_date.strftime('%d %b %Y')}</b>",
                    styles["Normal"]
                )
            )

            elements.append(
                Paragraph(
                    f"• {city.name} – {service.name}",
                    styles["Normal"]
                )
            )

            elements.append(Spacer(1, 6))

            current_date += timedelta(days=1)
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
