# from sqlalchemy import TIMESTAMP, Column, DateTime, ForeignKey, Integer, String, Text,Enum, func
# from api.v1.schemas.rbac_schemas import StatusEnum
# from db.session import Base
# from sqlalchemy.orm import relationship

# class ModuleActionPair(Base):
#     __tablename__ = "module_action_pairs"

#     module_action_pair_id = Column(Integer, primary_key=True)
#     module_id = Column(Integer, ForeignKey("modules.module_id"))
#     action_id = Column(Integer, ForeignKey("actions.action_id"))
#     status = Column(String(255))
#     created_at = Column(DateTime(timezone=True), default=func.now())
#     updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())


#     module = relationship("Module", back_populates="module_action_pair")
#     action = relationship("Action", back_populates="module_action_pair")
#     role_module_action_mappings = relationship("RoleModuleActionMapping", back_populates="module_action_pair")