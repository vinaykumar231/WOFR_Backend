from pydantic import BaseModel, ConfigDict, Field
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
