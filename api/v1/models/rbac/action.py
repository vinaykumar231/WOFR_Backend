from sqlalchemy import TIMESTAMP, Column, DateTime, Integer, String, Text,Enum, func
from db.session import Base
from sqlalchemy.orm import relationship
from api.v1.schemas.rbac_schemas import StatusEnum

class Action(Base):
    __tablename__ = "actions"

    action_id = Column(Integer, primary_key=True)
    action_name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    #module_action_pair = relationship("ModuleActionPair", back_populates="action")
    role_module_action_mappings = relationship("RoleModuleActionMapping", back_populates="action")
