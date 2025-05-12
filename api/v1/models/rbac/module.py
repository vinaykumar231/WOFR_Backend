from sqlalchemy import TIMESTAMP, Column, Integer, String, Text, Enum, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from api.v1.schemas.rbac_schemas import StatusEnum
from datetime import datetime
from db.session import Base


class Module(Base):
    __tablename__ = "modules"

    module_id = Column(Integer, primary_key=True, autoincrement=True)
    module_name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    #module_action_pair = relationship("ModuleActionPair", back_populates="module")
    role_module_action_mappings = relationship("RoleModuleActionMapping", back_populates="module")