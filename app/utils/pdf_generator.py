from io import BytesIO
from decimal import Decimal
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import os


CURRENCY = "PKR"


def format_currency(value):
    try:
        return f"{CURRENCY} {Decimal(value):,.2f}"
    except:
        return f"{CURRENCY} 0.00"


# =====================================================
# COMPANY HEADER
# =====================================================

def add_company_header(elements, styles):

    logo_path = os.path.join("app", "static", "uniworld_logo.png")

    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=1.2 * inch, height=1.2 * inch))

    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("<b>UniWorld Travel & Tours Pvt. Ltd.</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))


# =====================================================
# INVOICE PDF (FULL SAFE VERSION)
# =====================================================

def generate_invoice_pdf(invoice):

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40
    )

    elements = []
    styles = getSampleStyleSheet()

    add_company_header(elements, styles)

    elements.append(Paragraph("<b>INVOICE</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))

    # ==============================
    # BASIC INFO
    # ==============================

    client_name = ""
    if invoice.client:
        client_name = invoice.client.company_name

    elements.append(Paragraph(f"<b>Invoice Number:</b> {invoice.invoice_number}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {invoice.created_at.date()}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Client:</b> {client_name}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    # ==============================
    # SERVICES TABLE
    # ==============================

    data = [["Service", "Units", "Unit Price", "Total"]]

    quotation = invoice.quotation

    if quotation and quotation.items:
        for item in quotation.items:

            service_name = ""
            if item.service:
                service_name = item.service.name

            data.append([
                service_name,
                str(item.quantity),
                format_currency(item.sell_price),
                format_currency(item.total_sell)
            ])

    data.append(["", "", "Total Amount", format_currency(invoice.total_amount)])
    data.append(["", "", "Paid Amount", format_currency(invoice.paid_amount)])
    data.append(["", "", "Due Amount", format_currency(invoice.due_amount)])
    data.append(["", "", "Payment Status", invoice.payment_status.value])

    table = Table(
        data,
        colWidths=[2.8 * inch, 0.8 * inch, 1.5 * inch, 1.4 * inch]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("ALIGN", (2, 1), (3, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (-2, -4), (-1, -1), colors.lightgrey)
    ]))

    elements.append(table)

    # ==============================
    # PAYMENT HISTORY (SAFE)
    # ==============================

    payments = []

    # Safely load payments
    if hasattr(invoice, "payments") and invoice.payments:
        payments = invoice.payments

    if payments:

        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("<b>Payment History</b>", styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        payment_data = [["Date", "Method", "Reference", "Amount"]]

        for p in payments:

            method = ""
            if p.payment_method:
                method = p.payment_method.value

            payment_data.append([
                str(p.payment_date),
                method,
                p.reference_no or "",
                format_currency(p.amount)
            ])

        payment_table = Table(
            payment_data,
            colWidths=[1.2 * inch, 1.2 * inch, 1.8 * inch, 1.2 * inch]
        )

        payment_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)
        ]))

        elements.append(payment_table)

    doc.build(elements)
    buffer.seek(0)

    return buffer
