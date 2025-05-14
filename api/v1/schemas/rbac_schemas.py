
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum


class StatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"

class StatusUpdate(BaseModel):
    status: StatusEnum

#------------------------------------------ Modules ---------------------------------------------
class ModuleOut(BaseModel):
    module_id: int
    module_name: str
    description: str
    status: str 
    created_at: datetime 

    model_config = ConfigDict(from_attributes=True)

class ModuleUpdate(BaseModel):
    module_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StatusEnum] = None

    class Config:
        orm_mode = True
        from_attributes = True
#------------------------------------------ Actions ---------------------------------------------

class ActionOut(BaseModel):
    action_id: int
    action_name: str
    description: Optional[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ActionUpdate(BaseModel):
    action_name: Optional[str]= None
    description: Optional[str]= None
    status: Optional[str]= None
#--------------------------------------------- Roles -------------------------------------------------------------

class RoleCreate(BaseModel):
    role_name: str
    description: Optional[str] = None
    status: Optional[StatusEnum] = StatusEnum.active

class RoleOut(BaseModel):
    role_id: int
    role_name: str
    description: Optional[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleUpdate(BaseModel):
    role_name: Optional[str]
    description: Optional[str]
    status: Optional[StatusEnum]


class StatusUpdate(BaseModel):
    status: StatusEnum


class SuccessResponse(BaseModel):
    success: bool
    data: dict
    meta: Optional[dict] = None

#----------------------------------------- Role Module Action Mapping ------------------------------------

class RoleModuleAssignment(BaseModel):
    role_id: List[int]                     
    action_ids: List[int]                 
    status: StatusEnum = StatusEnum.active

class RoleModuleAssignments(BaseModel):
    module_id: int
    assignments: List[RoleModuleAssignment]

class RoleModuleAssignmentUpdate(BaseModel):
    role_id: Optional[int] = None
    action_ids: Optional[List[int]] = None
    assigned_by: Optional[str] = None
    status: Optional[str] = None

class RoleModuleAssignmentsUpdate(BaseModel):
    module_id: int
    assignments: List[RoleModuleAssignmentUpdate]

class RoleModuleStatusUpdate(BaseModel):
    mapping_ids: List[int]
    status: StatusEnum
    
    class Config:
        from_attributes = True

class Meta(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int

class RoleModuleActionResponse(BaseModel):
    role_module_action_mapping_id: int
    module_id: int
    module_name: Optional[str]
    action_id: int
    action_name: Optional[str]
    role_id: int
    role_name: Optional[str]
    assigner_id: str
    assigner_name: Optional[str]
    assignment_date: datetime

    class Config:
        orm_mode = True

#------------------------------------------ User Role Assigned ----------------------------------------------------
class UserRoleAssignmentCreate(BaseModel):
    user_id: str = Field(..., max_length=10, description="ID of the user to assign")
    tenant_id: str = Field(..., description="Tenant under which assignment is made")
    module_id: int = Field(..., description="Module ID whose actions/roles are to be assigned to the user")
    assigned_by: int = Field(..., description="Admin/User ID who is assigning")

#-------------------------------------------------------------------------------------------------------------

class MessageMeta(BaseModel):
    message: str
    timestamp: str

class ResponseMeta(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int

class SuccessResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    meta: Optional[Union[ResponseMeta, MessageMeta]] = None

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    

