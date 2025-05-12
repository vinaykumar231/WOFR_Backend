
from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional, Union
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

class RoleModuleActionMappingCreate(BaseModel):
    module_id: int
    action_id: int
    role_id: int
    assigned_by: str  

    class Config:
        from_attributes = True

class RoleModuleActionResponse(BaseModel):
    role_module_action_mapping_id: int
    module_id: int
    module_name: Optional[str]
    action_id: int
    action_name: Optional[str]
    role_id: int
    role_name: Optional[str]  # New field to include role name
    assigner_id: str
    assigner_name: Optional[str]
    assignment_date: datetime

    class Config:
        orm_mode = True

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
    
class ModuleCreate(BaseModel):
    Module_Name: str
    Description: Optional[str]
    Status: Optional[str] = "Active"

class ActionCreate(BaseModel):
    Action_Name: str
    Description: Optional[str]
    Status: Optional[str] = "Active"

class RoleCreate(BaseModel):
    Role_Name: str
    Description: Optional[str]
    Status: Optional[str] = "Active"

class RoleMappingCreate(BaseModel):
    Role_ID: int
    Pair_ID: int
    Assigned_By: int
    Assignment_Date: Optional[datetime] = None
