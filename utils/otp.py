import secrets
import string
from datetime import datetime, timedelta, timezone

def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure OTP."""
    return "".join(secrets.choice(string.digits) for _ in range(length))

def get_otp_expiration(minutes: int = 5) -> datetime:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(tzinfo=None)
