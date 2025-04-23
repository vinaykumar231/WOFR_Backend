import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from db.session import Base
import enum
from api.v1.schemas import StatusEnum, TenantTypeEnum,LoginTypeEnum, LoginStatusEnum

class User(Base):
    __tablename__ = 'user'
    user_id = Column(String(10), primary_key=True, unique=True, index=True, nullable=False)
    username = Column(String(255))
    email = Column(String(255), unique=True)
    phone_number = Column(String(255))
    organization_name = Column(String(255))
    password_hash = Column(String(255))
    status = Column(Enum(StatusEnum))
    user_type = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=False)

    social_auths = relationship("SocialAuth", back_populates="user")


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



# class Role(Base):
#     __tablename__ = 'role'
#     role_id = Column(Integer, primary_key=True, autoincrement=True)
#     role_name = Column(String(255))  
#     created_at = Column(DateTime, default=datetime.utcnow)

#     user_roles = relationship("UserRole", back_populates="role")


# class UserRole(Base):
#     __tablename__ = 'userrole'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey('user_tb.user_id'))
#     role_id = Column(Integer, ForeignKey('role.role_id'))

#     user = relationship("User", back_populates="roles")
#     role = relationship("Role", back_populates="user_roles")


# class Tenant(Base):
#     __tablename__ = 'tenant'
#     tenant_id = Column(Integer, primary_key=True, autoincrement=True)
#     org_name = Column(String(255))
#     org_mail = Column(String(255))
#     created_by = Column(Integer, ForeignKey("user_tb.user_id"))
#     tenant_type = Column(Enum(TenantTypeEnum))
#     is_registered = Column(Boolean)
#     created_at = Column(DateTime, default=datetime.utcnow)

#     # Define the relationship with explicit foreign_keys to resolve ambiguity
#     users = relationship("User", back_populates="tenant", foreign_keys="User.tenant_id")
#     creator = relationship("User", back_populates="created_tenants", foreign_keys=[created_by])

# The commented-out classes remain the same


# class FrontEndMenu(Base):
#     __tablename__ = 'frontendmenu'
#     id = Column(Integer, primary_key=True)
#     screenname = Column(String)
#     ui_screenname = Column(String)


# class FrontEndMenuPermission(Base):
#     __tablename__ = 'frontendmenu_permission'
#     id = Column(Integer, primary_key=True)
#     FrontEndMenu_id = Column(Integer, ForeignKey('frontendmenu.id'))
#     user_id = Column(String, ForeignKey('user.user_id'))

#     user = relationship("User", back_populates="permissions")
#     menu = relationship("FrontEndMenu")


# class LoginAudit(Base):
#     __tablename__ = 'login_audit'
#     id = Column(Integer, primary_key=True)
#     user_id = Column(String, ForeignKey('user.user_id'))
#     login_time = Column(DateTime, default=datetime.utcnow)
#     login_type = Column(Enum(LoginTypeEnum))
#     status = Column(Enum(LoginStatusEnum))
#     ip_address = Column(String)

#     user = relationship("User", back_populates="login_audits")


# class PasswordHistory(Base):
#     __tablename__ = 'password_history'
#     history_id = Column(Integer, primary_key=True)
#     user_id = Column(String, ForeignKey('user.user_id'))
#     password_hash = Column(String)
#     changed_at = Column(DateTime, default=datetime.utcnow)

#     user = relationship("User", back_populates="password_history")


    






