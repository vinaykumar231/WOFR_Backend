import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from api.v1.schemas.user_schemas import StatusEnum
from db.session import Base
import enum
#from api.v1.schemas import StatusEnum, TenantTypeEnum,LoginTypeEnum, LoginStatusEnum

class User(Base):
    __tablename__ = 'user'
    user_id = Column(String(10), primary_key=True, unique=True, index=True, nullable=False)
    username = Column(String(255))
    email = Column(String(255), unique=True)
    phone_number = Column(String(255))
    organization_name = Column(String(255))
    password_hash = Column(String(255))
    status = Column(String(255))
    user_type = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=False)
    #is_login_without_otp = Column(Boolean, default=False)

    social_auths = relationship("SocialAuth", back_populates="user")
    user_role_assignment = relationship("UserRoleAssignment", back_populates="user")
    tenant = relationship("Tenant", back_populates="user", uselist=False)
    #role_module_action_mappings = relationship("RoleModuleActionMapping", back_populates="user")

class OTP(Base):
    __tablename__ = 'otp'
    otp_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(255))
    purpose= Column(String(100), nullable=True)
    otp_code = Column(String(10), nullable=True)
    attempt_count = Column(Integer, nullable=True)
    is_verified = Column(Boolean, nullable=True)
    status = Column(String(255), nullable=True, default="active")  
    generated_at = Column(DateTime, nullable=True)
    expired_at = Column(DateTime, nullable=True)



