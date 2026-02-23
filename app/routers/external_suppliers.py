from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/external-suppliers",
    tags=["External Suppliers"]
)


@router.post("/", response_model=schemas.ExternalSupplierResponse)
def create_supplier(data: schemas.ExternalSupplierCreate, db: Session = Depends(get_db)):

    existing = db.query(models.ExternalSupplier).filter_by(name=data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Supplier already exists")

    supplier = models.ExternalSupplier(**data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/", response_model=List[schemas.ExternalSupplierResponse])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(models.ExternalSupplier).order_by(models.ExternalSupplier.id.desc()).all()


@router.get("/{supplier_id}", response_model=schemas.ExternalSupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(models.ExternalSupplier).filter_by(id=supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=schemas.ExternalSupplierResponse)
def update_supplier(supplier_id: int, data: schemas.ExternalSupplierUpdate, db: Session = Depends(get_db)):
    supplier = db.query(models.ExternalSupplier).filter_by(id=supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)

    db.commit()
    db.refresh(supplier)
    return suppl
