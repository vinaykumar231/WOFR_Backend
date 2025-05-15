from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func,TIMESTAMP
from db.session import Base
from sqlalchemy.orm import relationship


class TenantUser(Base):
    __tablename__ = "tenant_users_tb"

    tenant_user_id = Column(String(10), primary_key=True, unique=True, index=True, nullable=False)
    tenant_id = Column(String(10), ForeignKey("tenants.tenant_id"))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    position = Column(String(100))
    department = Column(String(100))
    contact_number = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    tenant = relationship("Tenant", back_populates="tenant_user")
    tenant_user_role_mappings = relationship("TenantUserRoleAssign", back_populates="tenant_user")

    