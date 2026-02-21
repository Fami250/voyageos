from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# =====================================================
# SECURITY CONFIG
# =====================================================

SECRET_KEY = "voyageos_super_secret_key"
ALGORITHM = "HS256"

# This tells FastAPI where login endpoint is
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# =====================================================
# TOKEN VERIFICATION DEPENDENCY
# =====================================================

def get_current_user(token: str = Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        return username

    except JWTError:
        raise credentials_exception
