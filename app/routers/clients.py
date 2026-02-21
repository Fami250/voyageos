from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.dependencies import verify_token  # 🔐 NEW


router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
    dependencies=[Depends(verify_token)]  # 🔒 GLOBAL PROTECTION
)


# ===============================
# CREATE CLIENT
# ===============================
@router.post("/", response_model=schemas.ClientResponse)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):

    # Check if email already exists
    existing_client = db.query(models.Client).filter(
        models.Client.email == client.email
    ).first()

    if existing_client:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_client = models.Client(
        company_name=client.company_name,
        contact_person=client.contact_person,
        email=client.email,
        phone=client.phone,
        address=client.address
    )

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return new_client


# ===============================
# GET ALL CLIENTS
# ===============================
@router.get("/", response_model=List[schemas.ClientResponse])
def get_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).all()


# ===============================
# GET SINGLE CLIENT
# ===============================
@router.get("/{client_id}", response_model=schemas.ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):

    client = db.query(models.Client).filter(
        models.Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return client


# ===============================
# DELETE CLIENT
# ===============================
@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):

    client = db.query(models.Client).filter(
        models.Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(client)
    db.commit()

    return {"message": "Client deleted successfully"}
