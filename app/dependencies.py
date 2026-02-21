from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional

# =====================================================
# SECURITY CONFIG
# =====================================================

SECRET_KEY = "voyageos_super_secret_key"
ALGORITHM = "HS256"

# OAuth2 scheme for automatic token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# =====================================================
# CORE TOKEN VALIDATION LOGIC
# =====================================================

def _decode_token(token: str):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")

        if username is None:
            raise credentials_exception

        return username

    except JWTError:
        raise credentials_exception


# =====================================================
# MODERN DEPENDENCY (USED IN main.py GLOBAL LOCK)
# =====================================================

def get_current_user(token: str = Depends(oauth2_scheme)):
    return _decode_token(token)


# =====================================================
# BACKWARD COMPATIBILITY (IF OLD ROUTERS STILL IMPORT THIS)
# =====================================================

def verify_token(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        scheme, token = authorization.split()

        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid auth scheme",
            )

        return _decode_token(token)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
