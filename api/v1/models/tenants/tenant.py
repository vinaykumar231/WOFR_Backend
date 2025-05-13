from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func,TIMESTAMP
from db.session import Base
from sqlalchemy.orm import relationship

class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(10), ForeignKey("user.user_id"))
    name = Column(String(255), nullable=False)
    organization_type = Column(String(100), nullable=False)
    industry_sector = Column(String(100), nullable=False)
    registration_tax_id = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    country = Column(String(100), nullable=False)
    zip_postal_code = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    user = relationship("User", back_populates="tenant")
    user_role_assignment = relationship("UserRoleAssignment", back_populates="tenant")
