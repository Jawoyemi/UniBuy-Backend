from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    university = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Verification flags
    is_verified = Column(Boolean, default=False)
    is_student_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # OTP verification support
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self):
        return f"<User {self.email}>"
