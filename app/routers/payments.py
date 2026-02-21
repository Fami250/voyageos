from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List

from app.database import get_db
from app import models
from app.dependencies import verify_token   # 🔐 NEW


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    dependencies=[Depends(verify_token)]   # 🔒 GLOBAL PROTECTION
)

# =====================================================
# ADD PAYMENT
# =====================================================

@router.post("/")
def add_payment(
    quotation_id: int,
    amount_paid: float,
    payment_method: models.PaymentMethod = models.PaymentMethod.CASH,
    reference_number: str = None,
    notes: str = None,
    db: Session = Depends(get_db)
):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    payment = models.Payment(
        quotation_id=quotation.id,
        client_id=quotation.client_id,
        amount_paid=amount_paid,
        payment_method=payment_method,
        reference_number=reference_number,
        notes=notes
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    # -------------------------------------------------
    # Recalculate totals
    # -------------------------------------------------

    total_paid = db.query(
        func.coalesce(func.sum(models.Payment.amount_paid), 0)
    ).filter(
        models.Payment.quotation_id == quotation.id
    ).scalar()

    invoice = quotation.invoice

    if invoice:
        invoice.paid_amount = total_paid
        invoice.due_amount = invoice.total_amount - total_paid

        if invoice.due_amount <= 0:
            invoice.payment_status = models.PaymentStatus.PAID
        elif total_paid > 0:
            invoice.payment_status = models.PaymentStatus.PARTIAL
        else:
            invoice.payment_status = models.PaymentStatus.UNPAID

        if quotation.due_date and invoice.due_amount > 0:
            if quotation.due_date < date.today():
                invoice.payment_status = models.PaymentStatus.OVERDUE

        db.commit()

    return {
        "message": "Payment added successfully",
        "total_paid": total_paid
    }


# =====================================================
# GET PAYMENTS BY QUOTATION
# =====================================================

@router.get("/quotation/{quotation_id}")
def get_payments_by_quotation(
    quotation_id: int,
    db: Session = Depends(get_db)
):

    payments = db.query(models.Payment).filter(
        models.Payment.quotation_id == quotation_id
    ).all()

    return payments


# =====================================================
# PAYMENT SUMMARY
# =====================================================

@router.get("/summary")
def payment_summary(db: Session = Depends(get_db)):

    total_collected = db.query(
        func.coalesce(func.sum(models.Payment.amount_paid), 0)
    ).scalar()

    total_due = db.query(
        func.coalesce(func.sum(models.Invoice.due_amount), 0)
    ).scalar()

    overdue_amount = db.query(
        func.coalesce(func.sum(models.Invoice.due_amount), 0)
    ).filter(
        models.Invoice.payment_status == models.PaymentStatus.OVERDUE
    ).scalar()

    return {
        "total_collected": total_collected,
        "total_due": total_due,
        "overdue_amount": overdue_amount
    }
