from io import BytesIO
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


def generate_payment_voucher_pdf(payment):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []
    styles = getSampleStyleSheet()

    # ===============================
    # COMPANY HEADER
    # ===============================
    logo_path = os.path.join("app", "static", "uniworld_logo.png")

    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=1.2 * inch, height=1.2 * inch))

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("<b>UniWorld Travel & Tours Pvt. Ltd.</b>", styles["Title"]))
    elements.append(Spacer(1, 0.4 * inch))

    # ===============================
    # VOUCHER TITLE
    # ===============================
    elements.append(Paragraph("<b>PAYMENT RECEIPT VOUCHER</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.4 * inch))

    invoice = payment.invoice
    client = invoice.client

    # ===============================
    # DETAILS TABLE
    # ===============================
    data = [
        ["Receipt No:", payment.receipt_number],
        ["Invoice No:", invoice.invoice_number],
        ["Client:", client.company_name],
        ["Payment Date:", str(payment.payment_date)],
        ["Payment Method:", payment.payment_method.value],
        ["Reference No:", payment.reference_no or "-"],
        ["Amount Paid:", f"PKR {payment.amount:,.2f}"],
    ]

    table = Table(data, colWidths=[2 * inch, 3.5 * inch])

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.8 * inch))

    elements.append(Paragraph("Authorized Signature ____________________", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)

    return buffer
