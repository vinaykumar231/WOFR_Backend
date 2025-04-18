import enum
from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class StatusEnum(str, Enum):
    active = "active"
    locked = "locked"
    inactive = "inactive"

class TenantTypeEnum(str, Enum):
    created = "created"
    supported = "supported"

class LoginTypeEnum(str, Enum):
    email = "email"
    google = "google"
    admin = "admin"

class LoginStatusEnum(str, Enum):
    success = "success"
    locked = "locked"
    failed = "failed"

class UserType(str, Enum):
    admin = "admin"
    user = "user"

# class OTPStatusEnum(str, Enum):
#     ACTIVE = "active"
#     EXPIRED = "expired"
#     FROZEN = "frozen"


class RegisterUser(BaseModel):
    user_name: str
    user_email: EmailStr
    phone: str
    user_password: str
    confirm_password: str
    user_type: UserType = UserType.user
    status: StatusEnum

class LoginUser(BaseModel):
    email: EmailStr
    password: str


class OTPVerify(BaseModel):
    email: str
    otp_code: str


class RegisterUserResponse(BaseModel):
    message: str
    user_name: str
    user_email: EmailStr
    phone: str


class LoginResponse(BaseModel):
    message: str
    user_name: str
    user_email: EmailStr
    phone: str

class UserOut(RegisterUser):
    created_at: datetime
    class Config:
        orm_mode = True
        
class ALLUser(BaseModel):
    user_id: int
    username: str
    email: str
    phone_number: Optional[str]
    status: Optional[str]
    user_type: Optional[str]
    created_at: datetime
    is_verified: bool

    class Config:
        orm_mode = True

# LoginAudit
class LoginAuditBase(BaseModel):
    user_id: str
    login_type: LoginTypeEnum
    status: LoginStatusEnum
    ip_address: str

class LoginAuditOut(LoginAuditBase):
    id: int
    login_time: datetime
    class Config:
        orm_mode = True


# PasswordHistory
class PasswordHistoryOut(BaseModel):
    history_id: int
    user_id: str
    password_hash: str
    changed_at: datetime
    class Config:
        orm_mode = True


# OTP
class OTPOut(BaseModel):
    otp_id: int
    user_id: str
    otp_code: str
    attempt_count: int
    is_verified: bool
    generated_at: datetime
    expired_at: datetime
    class Config:
        orm_mode = True


# SocialAuth
class SocialAuthOut(BaseModel):
    id: int
    user_id: str
    provider: str
    provider_user_id: str
    access_token: str
    refresh_token: str
    expiry_token: str
    class Config:
        orm_mode = True
