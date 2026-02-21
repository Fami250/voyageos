from fastapi import Header, HTTPException
from jose import jwt, JWTError

SECRET_KEY = "voyageos_super_secret_key"
ALGORITHM = "HS256"

def verify_token(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
