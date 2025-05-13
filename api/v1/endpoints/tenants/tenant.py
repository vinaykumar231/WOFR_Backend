from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from api.v1.models.tenants.tenant import Tenant
from db.session import get_db
from api.v1.models.rbac.user_role_assignment import UserRoleAssignment
from api.v1.models.rbac.role_module_action_mapping import RoleModuleActionMapping
#from api.v1.schemas.rbac_schemas import UserRoleAssignmentCreate
from sqlalchemy.exc import SQLAlchemyError
from utils.helper_function import paginate

router = APIRouter()

class TenantCreate(BaseModel):
    user_id: str = Field(..., max_length=10)
    name: str
    organization_type: str
    industry_sector: str
    registration_tax_id: str
    address: str
    country: str
    zip_postal_code: str

class TenantResponse(BaseModel):
    tenant_id: int
    user_id: str
    name: str
    organization_type: str
    industry_sector: str
    registration_tax_id: str
    address: str
    country: str
    zip_postal_code: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

@router.post("/v1/tenant", response_model=TenantResponse)
def create_tenant(request: TenantCreate, db: Session = Depends(get_db)):
    try:
        tenant = Tenant(
            user_id=request.user_id,
            name=request.name,
            organization_type=request.organization_type,
            industry_sector=request.industry_sector,
            registration_tax_id=request.registration_tax_id,
            address=request.address,
            country=request.country,
            zip_postal_code=request.zip_postal_code
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error occurred.")