from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

def validate_school_email(v: str) -> str:
    if v is None:
        return v
    email_lower = v.lower()
    if not (email_lower.endswith('.edu') or email_lower.endswith('.edu.ng')):
        raise ValueError('Only school emails (.edu or .edu.ng) are allowed')
    return v

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    university: Literal["University of Porthacourt (UNIPORT)", "Rivers State University (RSU)"]

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str):
        return validate_school_email(v)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    hashed_password: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]):
        if v is None:
            return v
        return validate_school_email(v)

class User(UserBase):
    id: int
    is_verified: bool
    is_student_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str
    otp_code: Optional[str] = None
    otp_expires_at: Optional[datetime] = None

class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str):
        return validate_school_email(v)

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str):
        return validate_school_email(v)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str):
        return validate_school_email(v)

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str):
        return validate_school_email(v)
