from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas, models
from app.services.quotation_service import create_quotation
from app.utils.pdf_generator import generate_quotation_pdf, generate_profit_pdf

router = APIRouter(
    prefix="/quotations",
    tags=["Quotations"]
)


@router.post("/", response_model=schemas.QuotationOut)
def create_new_quotation(quotation_data: schemas.QuotationCreate, db: Session = Depends(get_db)):
    return create_quotation(db, quotation_data)


@router.get("/{quotation_id}/pdf")
def download_quotation_pdf(quotation_id: int, db: Session = Depends(get_db)):

    quotation = db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()
    client = db.query(models.Client).filter(models.Client.id == quotation.client_id).first()
    items = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quotation_id).all()

    pdf_buffer = generate_quotation_pdf(quotation, items, client)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=quotation_{quotation_id}.pdf"}
    )


@router.get("/{quotation_id}/profit")
def download_profit_pdf(quotation_id: int, db: Session = Depends(get_db)):

    quotation = db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()
    client = db.query(models.Client).filter(models.Client.id == quotation.client_id).first()
    items = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quotation_id).all()

    pdf_buffer = generate_profit_pdf(quotation, items, client)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=profit_sheet_{quotation_id}.pdf"}
    )
