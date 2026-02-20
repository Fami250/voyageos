from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app import models, schemas


router = APIRouter(
    prefix="/cities",
    tags=["Cities"]
)


# =====================================================
# CREATE CITY
# =====================================================

@router.post("/", response_model=schemas.CityResponse)
def create_city(
    data: schemas.CityCreate,
    db: Session = Depends(get_db)
):
    # Validate country
    country = db.query(models.Country).filter(
        models.Country.id == data.country_id
    ).first()

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    city = models.City(
        name=data.name.strip(),
        country_id=data.country_id
    )

    db.add(city)
    db.commit()
    db.refresh(city)

    # Reload with country relationship
    city = db.query(models.City).options(
        joinedload(models.City.country)
    ).filter(
        models.City.id == city.id
    ).first()

    return city


# =====================================================
# GET ALL CITIES (Alphabetical Order)
# =====================================================

@router.get("/", response_model=List[schemas.CityResponse])
def get_cities(db: Session = Depends(get_db)):

    cities = db.query(models.City).options(
        joinedload(models.City.country)
    ).order_by(
        models.City.name.asc()
    ).all()

    return cities


# =====================================================
# GET CITIES BY COUNTRY (Alphabetical Order)
# =====================================================

@router.get("/by-country/{country_id}", response_model=List[schemas.CityResponse])
def get_cities_by_country(
    country_id: int,
    db: Session = Depends(get_db)
):

    cities = db.query(models.City).options(
        joinedload(models.City.country)
    ).filter(
        models.City.country_id == country_id
    ).order_by(
        models.City.name.asc()
    ).all()

    return cities
