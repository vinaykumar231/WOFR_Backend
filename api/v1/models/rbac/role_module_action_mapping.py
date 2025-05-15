from sqlalchemy import TIMESTAMP, Column, Integer, ForeignKey, DateTime, String, func
from sqlalchemy.orm import relationship
from db.session import Base

class RoleModuleActionMapping(Base):
    __tablename__ = "role_module_action_mapping"

    role_module_action_mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey("modules.module_id"))  
    action_id = Column(Integer, ForeignKey("actions.action_id"))  
    role_id = Column(Integer, ForeignKey("roles.role_id"))
    status = Column(String(255))
    mapping_date = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    # Relationships
    role = relationship("Role", back_populates="role_module_action_mappings")
    module = relationship("Module", back_populates="role_module_action_mappings")
    action = relationship("Action", back_populates="role_module_action_mappings")
    #user = relationship("User", back_populates="role_module_action_mappings")
    user_role_assignment = relationship("UserRoleAssignment", back_populates="role_module_action_mappings")

    tenant_user_role_mappings = relationship("TenantUserRoleAssign", back_populates="role_module_action_mapping")
