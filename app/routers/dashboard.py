from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models
from app.dependencies import verify_token   # 🔐 NEW


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(verify_token)]   # 🔒 GLOBAL PROTECTION
)


@router.get("/")
def get_dashboard_summary(db: Session = Depends(get_db)):

    # =========================
    # QUOTATION METRICS
    # =========================
    total_quotations = db.query(func.count(models.Quotation.id)).scalar() or 0

    confirmed_quotations = db.query(
        func.count(models.Quotation.id)
    ).filter(
        models.Quotation.status == models.QuotationStatus.CONFIRMED
    ).scalar() or 0

    total_profit = db.query(
        func.sum(models.Quotation.total_profit)
    ).scalar() or 0

    conversion_rate = 0
    if total_quotations > 0:
        conversion_rate = (confirmed_quotations / total_quotations) * 100

    # =========================
    # INVOICE METRICS
    # =========================
    total_revenue = db.query(
        func.sum(models.Invoice.total_amount)
    ).scalar() or 0

    total_paid = db.query(
        func.sum(models.Invoice.paid_amount)
    ).scalar() or 0

    total_outstanding = db.query(
        func.sum(models.Invoice.due_amount)
    ).scalar() or 0

    total_invoices = db.query(
        func.count(models.Invoice.id)
    ).scalar() or 0

    # =========================
    # RESPONSE
    # =========================
    return {
        "quotation_metrics": {
            "total_quotations": total_quotations,
            "confirmed_quotations": confirmed_quotations,
            "conversion_rate_percentage": round(conversion_rate, 2),
            "total_profit": total_profit
        },
        "invoice_metrics": {
            "total_invoices": total_invoices,
            "total_revenue": total_revenue,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding
        }
    }
