from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models
from pydantic import BaseModel
from app.dependencies import get_current_user  # 🔐 NEW


# =============================
# SCHEMAS (LOCAL)
# =============================

class CountryCreate(BaseModel):
    name: str


class CountryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# =============================
# ROUTER
# =============================

router = APIRouter(
    prefix="/countries",
    tags=["Countries"],
    dependencies=[Depends(get_current_user)]  # 🔒 GLOBAL PROTECTION
)

# =============================
# CREATE COUNTRY
# =============================

@router.post("/", response_model=CountryResponse)
def create_country(data: CountryCreate, db: Session = Depends(get_db)):

    existing = db.query(models.Country).filter(
        models.Country.name == data.name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Country already exists")

    country = models.Country(name=data.name)

    db.add(country)
    db.commit()
    db.refresh(country)

    return country


# =============================
# GET ALL COUNTRIES
# =============================

@router.get("/", response_model=List[CountryResponse])
def get_countries(db: Session = Depends(get_db)):
    return db.query(models.Country).all()
