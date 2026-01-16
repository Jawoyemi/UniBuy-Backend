from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from database import get_db
from models import User
from core.rate_limiter import signup_limiter, login_limiter, otp_limiter, verify_limiter, password_limiter
from schemas.user import UserCreate, User as UserSchema, Token, LoginRequest, OTPVerify, ForgotPasswordRequest, ResetPasswordRequest
from utils import get_password_hash, verify_password, create_access_token, generate_otp, get_otp_expiration, send_otp_email, send_password_reset_email, UserAlreadyExistsException, InvalidCredentialsException, NotVerifiedException, InvalidOTPException


router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", status_code=status.HTTP_201_CREATED, dependencies=[Depends(signup_limiter)])
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise UserAlreadyExistsException()

    # Create new user
    otp_code = generate_otp()
    otp_expires_at = get_otp_expiration()
    
    new_user = User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        university=user_in.university,
        hashed_password=get_password_hash(user_in.password),
        otp_code=otp_code,
        otp_expires_at=otp_expires_at,
        is_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    send_otp_email(new_user.email, otp_code)
    
    return {"message": "Verification code sent to email"}

@router.post("/verify-otp", response_model=Token, dependencies=[Depends(verify_limiter)])
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    email = data.email.strip()
    otp_code = data.otp_code.strip()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise InvalidOTPException()
    
    # Check if OTP matches and is not expired
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    is_expired = user.otp_expires_at and user.otp_expires_at < now
    
    if user.otp_code != otp_code or is_expired:
        raise InvalidOTPException()
    
    # Verify user
    user.is_verified = True
    user.otp_code = None  # Clear OTP after successful verification
    user.otp_expires_at = None
    db.commit()
    
    # Generate token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token, dependencies=[Depends(login_limiter)])
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise InvalidCredentialsException()
    
    if not user.is_verified:
        raise NotVerifiedException()
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/resend-otp", dependencies=[Depends(otp_limiter)])
def resend_otp(email: str, db: Session = Depends(get_db)):
    email = email.strip()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_verified:
        return {"message": "Account already verified"}
        
    otp_code = generate_otp()
    user.otp_code = otp_code
    user.otp_expires_at = get_otp_expiration()
    db.commit()
    
    send_otp_email(user.email, otp_code)
    
    return {"message": "New verification code sent to email"}

@router.post("/forgot-password", dependencies=[Depends(otp_limiter)])
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = data.email.strip()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # We return success even if user not found for security reasons (avoid email enumeration)
        return {"message": "If an account exists with this email, a reset code has been sent."}
    
    otp_code = generate_otp()
    user.otp_code = otp_code
    user.otp_expires_at = get_otp_expiration()
    db.commit()
    
    send_password_reset_email(user.email, otp_code)
    
    return {"message": "Password reset code sent to email"}

@router.post("/reset-password", dependencies=[Depends(password_limiter)])
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = data.email.strip()
    otp_code = data.otp_code.strip()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise InvalidOTPException()
    
    # Check if OTP matches and is not expired
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    is_expired = user.otp_expires_at and user.otp_expires_at < now
    
    if user.otp_code != otp_code or is_expired:
        raise InvalidOTPException()
    
    # Update password and clear OTP
    user.hashed_password = get_password_hash(data.new_password)
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    
    return {"message": "Password reset successful"}
