# =====================================================
# VoyageOS Authentication Dependency (Production Safe)
# =====================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
from typing import Optional, Dict

# =====================================================
# SECURITY CONFIG (MUST MATCH auth.py)
# =====================================================

SECRET_KEY = "voyageos_super_secret_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# =====================================================
# TOKEN DECODE CORE FUNCTION
# =====================================================

def _decode_token(token: str) -> Dict:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        exp: Optional[int] = payload.get("exp")

        if username is None:
            raise credentials_exception

        # Extra expiry safety check
        if exp and datetime.utcnow().timestamp() > exp:
            raise credentials_exception

        return {
            "username": username,
            "role": role
        }

    except JWTError:
        raise credentials_exception


# =====================================================
# MAIN DEPENDENCY (USED IN main.py GLOBAL LOCK)
# =====================================================

def get_current_user(token: str = Depends(oauth2_scheme)):
    return _decode_token(token)
