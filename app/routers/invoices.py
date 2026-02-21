from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from typing import List, Optional

from app.database import get_db
from app import models, schemas
from app.utils.pdf_generator import generate_invoice_pdf
from app.utils.payment_voucher_generator import generate_payment_voucher_pdf
from app.dependencies import get_current_user


# ❌ GLOBAL JWT REMOVED
router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)

# =====================================================
# GENERATE INVOICE NUMBER
# =====================================================

def generate_invoice_number(db: Session):
    last = db.query(models.Invoice).order_by(models.Invoice.id.desc()).first()

    if not last:
        return f"INV-{datetime.utcnow().year}-0001"

    try:
        last_no = int(last.invoice_number.split("-")[-1])
        return f"INV-{datetime.utcnow().year}-{last_no + 1:04d}"
    except:
        return f"INV-{datetime.utcnow().year}-{last.id + 1:04d}"


# =====================================================
# GENERATE RECEIPT NUMBER
# =====================================================

def generate_receipt_number(db: Session):
    last = db.query(models.InvoicePayment).order_by(models.InvoicePayment.id.desc()).first()

    if not last:
        return f"RCPT-{datetime.utcnow().year}-0001"

    try:
        last_no = int(last.receipt_number.split("-")[-1])
        return f"RCPT-{datetime.utcnow().year}-{last_no + 1:04d}"
    except:
        return f"RCPT-{datetime.utcnow().year}-{last.id + 1:04d}"


# =====================================================
# CREATE INVOICE (🔒 PROTECTED)
# =====================================================

@router.post("/", response_model=schemas.InvoiceResponse,
             dependencies=[Depends(get_current_user)])
def create_invoice(data: schemas.InvoiceCreate, db: Session = Depends(get_db)):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == data.quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    existing = db.query(models.Invoice).filter(
        models.Invoice.quotation_id == quotation.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Invoice already exists")

    invoice_number = generate_invoice_number(db)
    total = float(quotation.total_sell)

    invoice = models.Invoice(
        invoice_number=invoice_number,
        quotation_id=quotation.id,
        client_id=quotation.client_id,
        total_amount=total,
        paid_amount=0.0,
        due_amount=total,
        payment_status=models.PaymentStatus.UNPAID,
        created_at=datetime.utcnow()
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice


# =====================================================
# GET ALL INVOICES (🔒 PROTECTED)
# =====================================================

@router.get("/", response_model=List[schemas.InvoiceResponse],
            dependencies=[Depends(get_current_user)])
def get_invoices(
    quotation_id: Optional[int] = None,
    db: Session = Depends(get_db)
):

    query = db.query(models.Invoice)

    if quotation_id:
        query = query.filter(models.Invoice.quotation_id == quotation_id)

    invoices = query.order_by(models.Invoice.id.desc()).all()

    for inv in invoices:

        total_paid = db.query(
            func.coalesce(func.sum(models.InvoicePayment.amount), 0)
        ).filter(
            models.InvoicePayment.invoice_id == inv.id
        ).scalar()

        inv.paid_amount = float(total_paid)
        inv.due_amount = float(inv.total_amount - inv.paid_amount)

        if inv.due_amount <= 0:
            inv.due_amount = 0.0
            inv.payment_status = models.PaymentStatus.PAID
        elif inv.paid_amount > 0:
            inv.payment_status = models.PaymentStatus.PARTIAL
        else:
            inv.payment_status = models.PaymentStatus.UNPAID

    db.commit()
    return invoices


# =====================================================
# CANCEL INVOICE (🔒 PROTECTED)
# =====================================================

@router.put("/{invoice_id}/cancel",
            response_model=schemas.InvoiceResponse,
            dependencies=[Depends(get_current_user)])
def cancel_invoice(invoice_id: int, db: Session = Depends(get_db)):

    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.payment_status == models.PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Cannot cancel paid invoice")

    invoice.payment_status = models.PaymentStatus.CANCELLED
    invoice.due_amount = 0.0

    db.commit()
    db.refresh(invoice)

    return invoice


# =====================================================
# GET PAYMENT HISTORY (🔒 PROTECTED)
# =====================================================

@router.get("/{invoice_id}/payments",
            response_model=List[schemas.InvoicePaymentResponse],
            dependencies=[Depends(get_current_user)])
def get_invoice_payments(invoice_id: int, db: Session = Depends(get_db)):

    return db.query(models.InvoicePayment)\
        .filter(models.InvoicePayment.invoice_id == invoice_id)\
        .order_by(models.InvoicePayment.payment_date.asc())\
        .all()


# =====================================================
# PAYMENT ENGINE (🔒 PROTECTED)
# =====================================================

@router.put("/{invoice_id}/payment",
            response_model=schemas.InvoiceResponse,
            dependencies=[Depends(get_current_user)])
def update_payment(invoice_id: int, data: schemas.PaymentUpdate, db: Session = Depends(get_db)):

    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.payment_status == models.PaymentStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Invoice is cancelled")

    if data.paid_amount <= 0:
        raise HTTPException(status_code=400, detail="Payment must be greater than zero")

    receipt_number = generate_receipt_number(db)

    payment = models.InvoicePayment(
        receipt_number=receipt_number,
        invoice_id=invoice.id,
        payment_date=data.payment_date or date.today(),
        amount=data.paid_amount,
        payment_method=data.payment_method or models.PaymentMethod.CASH,
        reference_no=data.reference_number,
        notes=data.notes
    )

    db.add(payment)
    db.commit()

    total_paid = db.query(
        func.coalesce(func.sum(models.InvoicePayment.amount), 0)
    ).filter(
        models.InvoicePayment.invoice_id == invoice.id
    ).scalar()

    invoice.paid_amount = float(total_paid)
    invoice.due_amount = float(invoice.total_amount - invoice.paid_amount)

    if invoice.due_amount <= 0:
        invoice.payment_status = models.PaymentStatus.PAID
    elif invoice.paid_amount > 0:
        invoice.payment_status = models.PaymentStatus.PARTIAL
    else:
        invoice.payment_status = models.PaymentStatus.UNPAID

    db.commit()
    db.refresh(invoice)

    return invoice


# =====================================================
# INVOICE PDF (🌍 PUBLIC)
# =====================================================

@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):

    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    pdf_buffer = generate_invoice_pdf(invoice)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'inline; filename="{invoice.invoice_number}.pdf"'
        }
    )


# =====================================================
# PAYMENT VOUCHER PDF (🌍 PUBLIC)
# =====================================================

@router.get("/payments/{payment_id}/voucher")
def view_payment_voucher(payment_id: int, db: Session = Depends(get_db)):

    payment = db.query(models.InvoicePayment).filter(
        models.InvoicePayment.id == payment_id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    pdf_buffer = generate_payment_voucher_pdf(payment)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'inline; filename="Voucher-{payment.receipt_number}.pdf"'
        }
    )
