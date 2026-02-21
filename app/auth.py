from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta

router = APIRouter(tags=["Authentication"])

SECRET_KEY = "voyageos_super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600

# Hardcoded Users (Phase 1 Basic Auth)
fake_users_db = {
    "Faheem": {
        "username": "Faheem",
        "password": "Faheem111",
        "role": "admin"
    },
    "staff": {
        "username": "staff",
        "password": "staff123",
        "role": "staff"
    }
}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    user = fake_users_db.get(form_data.username)

    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    token_data = {
        "sub": user["username"],
        "role": user["role"],
        "exp": expire
    }

    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
