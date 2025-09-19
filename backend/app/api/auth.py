from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginIn, TokenOut
from app.core.security import (
    verify_password,
    create_access_token,
    decode_token,
    oauth2_scheme,   # <-- use the shared scheme (tokenUrl="/auth/token")
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    """
    JSON login (programmatic). Body: {"email":"..","password":".."}
    """
    u = db.query(User).filter(User.email == payload.email).first()
    if not u or not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = create_access_token(sub=str(u.id))
    return TokenOut(access_token=token)

@router.post("/token")
def issue_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 password flow for Swagger UI. Treats form.username as email.
    """
    email = form.username
    password = form.password

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(sub=str(user.id))
    return {"access_token": token, "token_type": "bearer"}

# Dependencies you can reuse in other routers
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    data = decode_token(token)
    if not data or "sub" not in data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token")
    # If your SQLAlchemy version warns on .get, you can use db.get(User, int(data["sub"]))
    u = db.query(User).get(int(data["sub"]))
    if not u:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return u

def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin required")
    return user
