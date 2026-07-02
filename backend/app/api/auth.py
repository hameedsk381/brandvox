from collections import defaultdict
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse, UserResponse,
    LoginResponse, ForgotPasswordRequest, ResetPasswordRequest,
    ChangePasswordRequest, MfaSetupResponse, MfaVerifyRequest,
    MfaLoginVerifyRequest,
)
from app.services.auth_service import (
    register_user, authenticate_user, change_user_password,
    create_password_reset_token, verify_reset_token, has_admin_role,
)
from app.services.audit_service import audit_service
from app.core.dependencies import get_current_active_user
from app.core.auth import create_access_token, decode_access_token
from app.models.user import User
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])

# ---- Rate limiter (simple in-memory) ----
_login_attempts: dict = defaultdict(list)
_RATE_LIMIT = 5
_RATE_WINDOW = 300

def _check_rate_limit(ip: str) -> None:
    now = datetime.now(timezone.utc)
    _login_attempts[ip] = [t for t in _login_attempts[ip] if (now - t).total_seconds() < _RATE_WINDOW]
    if len(_login_attempts[ip]) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, req)
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    _check_rate_limit(request.client.host if request.client else "unknown")
    user = await authenticate_user(db, req)

    if user.mfa_enabled:
        mfa_token = create_access_token(
            data={"sub": user.email, "mfa_pending": True},
            expires_delta=timedelta(minutes=5),
        )
        return {
            "access_token": "",
            "token_type": "bearer",
            "user": user,
            "mfa_required": True,
            "mfa_token": mfa_token,
        }

    if user and user.agency_id:
        await audit_service.log_action(
            db=db,
            agency_id=user.agency_id,
            action="user.login",
            resource_type="User",
            resource_id=str(user.id),
            user_id=user.id,
            details={"email": user.email},
            request=request
        )

    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "mfa_required": False,
    }

@router.post("/mfa/verify-login", response_model=TokenResponse)
async def verify_mfa_login(
    req: MfaLoginVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = decode_access_token(req.mfa_token)
    if not payload or payload.get("mfa_pending") is not True:
        raise HTTPException(status_code=400, detail="Invalid MFA token")

    result = await db.execute(select(User).filter(User.email == payload.get("sub")))
    user = result.scalars().first()
    if not user or not user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA not enabled")

    import pyotp
    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(req.code):
        raise HTTPException(status_code=400, detail="Invalid authentication code")

    if user.agency_id:
        await audit_service.log_action(
            db=db,
            agency_id=user.agency_id,
            action="user.login",
            resource_type="User",
            resource_id=str(user.id),
            user_id=user.id,
            details={"email": user.email, "mfa": True},
            request=request
        )

    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.patch("/password", status_code=status.HTTP_200_OK)
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await change_user_password(db, current_user, req.current_password, req.new_password)
    if current_user.agency_id:
        await audit_service.log_action(
            db=db,
            agency_id=current_user.agency_id,
            action="user.password_change",
            resource_type="User",
            resource_id=str(current_user.id),
            user_id=current_user.id,
            details={},
        )
    return {"detail": "Password changed successfully"}

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    req: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    token = await create_password_reset_token(db, req.email)
    if token:
        # In production, send email with reset link
        import logging
        logging.getLogger(__name__).info("Password reset token for %s: %s", req.email, token)
    return {"detail": "If the email exists, a reset link has been sent"}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    req: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    await verify_reset_token(db, req.token, req.password)
    return {"detail": "Password has been reset successfully"}

# ---- MFA endpoints ----

@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not has_admin_role(current_user.role):
        raise HTTPException(status_code=403, detail="Only admins can enable MFA")
    import pyotp
    secret = pyotp.random_base32()
    current_user.mfa_secret = secret
    await db.commit()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name="ReputationOS AI"
    )
    return MfaSetupResponse(
        secret=secret,
        uri=uri,
        qr_code_url=f"otpauth://totp/ReputationOS%20AI:{current_user.email}?secret={secret}&issuer=ReputationOS%20AI",
    )

@router.post("/mfa/verify", status_code=status.HTTP_200_OK)
async def verify_mfa(
    req: MfaVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not has_admin_role(current_user.role):
        raise HTTPException(status_code=403, detail="Only admins can enable MFA")
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not initialized. Call /auth/mfa/setup first.")

    import pyotp
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(req.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    current_user.mfa_enabled = True
    await db.commit()
    return {"detail": "MFA enabled successfully"}

@router.post("/mfa/disable", status_code=status.HTTP_200_OK)
async def disable_mfa(
    req: MfaVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    import pyotp
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(req.code):
        raise HTTPException(status_code=400, detail="Invalid authentication code")
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    await db.commit()
    return {"detail": "MFA disabled successfully"}

@router.get("/mfa/status")
async def mfa_status(
    current_user: User = Depends(get_current_active_user),
):
    return {"mfa_enabled": current_user.mfa_enabled, "can_enable": has_admin_role(current_user.role)}
