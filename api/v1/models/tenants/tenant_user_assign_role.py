from datetime import datetime
from sqlalchemy import TIMESTAMP, Column, String, Integer, ForeignKey, DateTime, func
from db.session import Base
from sqlalchemy.orm import relationship

class TenantUserRoleAssign(Base):
    __tablename__ = "tenant_user_assign_role_tb"

    tenant_user_role_mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_user_id = Column(String(10), ForeignKey("tenant_users_tb.tenant_user_id"), nullable=False)
    tenant_id = Column(String(10), ForeignKey("tenants.tenant_id"), nullable=False) 
    role_module_action_mapping_id = Column(Integer, ForeignKey("role_module_action_mapping.role_module_action_mapping_id"), nullable=False)
    assignment_date = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    tenant_user = relationship("TenantUser", back_populates="tenant_user_role_mappings")
   
    role_module_action_mapping = relationship("RoleModuleActionMapping", back_populates="tenant_user_role_mappings")

    tenant = relationship("Tenant", back_populates="tenant_user_role_mappings")
    
    