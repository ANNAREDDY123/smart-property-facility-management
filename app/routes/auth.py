from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
)
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.utils.rate_limit import limiter

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

security = HTTPBearer()


@router.post("/register", response_model=UserResponse)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("1000/minute")
def login(
    request: Request,
    user_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        user_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        )

    access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
    })

    refresh_token = create_refresh_token({
        "sub": str(user.id),
        "role": user.role,
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Access token required",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        )

    return user
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Refresh token required",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        )

    new_access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
    })

    new_refresh_token = create_refresh_token({
        "sub": str(user.id),
        "role": user.role,
    })

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.put("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Access token required",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        )

    if not verify_password(
        current_password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )

    if len(new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 6 characters",
        )

    if current_password == new_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password",
        )

    user.hashed_password = hash_password(new_password)

    db.commit()

    return {
        "message": "Password changed successfully"
    }