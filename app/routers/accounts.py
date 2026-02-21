from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.database import get_db
from app import models
from app.dependencies import verify_token   # 🔐 NEW


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    dependencies=[Depends(verify_token)]   # 🔒 GLOBAL PROTECTION
)


@router.get("/summary")
def accounts_summary(db: Session = Depends(get_db)):

    total_revenue = db.query(
        func.coalesce(func.sum(models.Invoice.total_amount), 0)
    ).scalar()

    total_paid = db.query(
        func.coalesce(func.sum(models.Invoice.paid_amount), 0)
    ).scalar()

    total_outstanding = db.query(
        func.coalesce(func.sum(models.Invoice.due_amount), 0)
    ).scalar()

    total_invoices = db.query(models.Invoice).count()

    # Monthly Cashflow (Paid grouped by month)
    monthly = db.query(
        func.to_char(models.Invoice.created_at, "Mon").label("month"),
        func.coalesce(func.sum(models.Invoice.paid_amount), 0).label("cash_in")
    ).group_by("month").all()

    monthly_cashflow = [
        {"month": m.month, "cash_in": float(m.cash_in)}
        for m in monthly
    ]

    return {
        "total_revenue": float(total_revenue),
        "total_paid": float(total_paid),
        "total_outstanding": float(total_outstanding),
        "total_invoices": total_invoices,
        "monthly_cashflow": monthly_cashflow
    }
