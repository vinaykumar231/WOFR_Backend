from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

class TenantCreate(BaseModel):
    #user_id: str = Field(..., max_length=10)
    name: str
    organization_type: str
    industry_sector: str
    registration_tax_id: str
    address: str
    country: str
    zip_postal_code: str

class TenantResponse(BaseModel):
    tenant_id: str
    user_id: Optional[str]
    user_name: Optional[str]
    name: str
    organization_type: str
    industry_sector: str
    registration_tax_id: str
    address: str
    country: str
    zip_postal_code: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }

#---------------------------------------------------- tenant user ----------------------------------------------

class TenantUserRoleAssignmentCreate(BaseModel):
    tenant_user_id: str
    tenant_id: str
    role_module_action_mapping_id: int

class TenantUserCreate(BaseModel):
    name: str
    email: EmailStr
    position: Optional[str] = None
    department: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None

class TenantUserResponse(BaseModel):
    tenant_user_id: str
    tenant_id: str
    tenant_name: Optional[str] = None 
    name: str
    email: str
    position: str
    department: str
    contact_number: str
    address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  

#-------------------- tenant user assign role --------------------------------------

class RoleSimpleResponse(BaseModel):
    role_name: Optional[str]

    model_config = dict(from_attributes=True)

class ModuleSimpleResponse(BaseModel):
    module_name: Optional[str]

    model_config = dict(from_attributes=True)

class ActionSimpleResponse(BaseModel):
    action_name: Optional[str]

    model_config = dict(from_attributes=True)

class RoleModuleActionMappingSimpleResponse(BaseModel):
    tenant_user_role_mapping_id: int = Field(..., alias="role_module_action_mapping_id")  
    role: Optional[RoleSimpleResponse]
    module: Optional[ModuleSimpleResponse]
    action: Optional[ActionSimpleResponse]

    model_config = dict(from_attributes=True)

class TenantSimpleResponse(BaseModel):
    tenant_name: Optional[str] = Field(default=None, alias="name")

    model_config = dict(from_attributes=True)

class TenantUserRoleAssignSimpleResponse(BaseModel):
    tenant_user_role_mapping_id: int = Field(..., alias="tenant_user_role_mapping_id")  
    tenant_user_id: str
    tenant_id: str
    assignment_date: datetime
    updated_at: datetime

    role_module_action_mapping: Optional[RoleModuleActionMappingSimpleResponse]
    tenant: Optional[TenantSimpleResponse]

    model_config = dict(from_attributes=True)