from datetime import datetime
from enum import Enum
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func, TIMESTAMP
from db.session import Base
from sqlalchemy.orm import relationship

class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignment"
    
    user_role_assignment_id = Column(Integer, primary_key=True)
    user_id = Column(String(10), ForeignKey("user.user_id"))
    role_id = Column(Integer, ForeignKey("roles.role_id"))
    assigned_by = Column(Integer)
    assignment_date = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    role = relationship("Role", back_populates="user_roles")
    user = relationship("User", back_populates="user_role_assignment")
