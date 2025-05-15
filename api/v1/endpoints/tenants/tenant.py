from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from api.v1.models.tenants.tenant import Tenant
from api.v1.models.user.user_auth import User
from api.v1.schemas.tenant_schemas import TenantCreate, TenantResponse
from auth.auth_bearer import JWTBearer, get_current_user, get_master_admin, get_super_admin
from db.session import get_db
from api.v1.models.rbac.user_role_assignment import UserRoleAssignment
from api.v1.models.rbac.role_module_action_mapping import RoleModuleActionMapping
#from api.v1.schemas.rbac_schemas import UserRoleAssignmentCreate
from sqlalchemy.exc import SQLAlchemyError
from utils.helper_function import SortOrder, paginate
from utils.validators import generate_next_tenant_id
from sqlalchemy.orm import Session, joinedload

router = APIRouter()


@router.post("/v1/tenant", response_model=None, status_code=status.HTTP_201_CREATED)
def create_tenant(request: TenantCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {request.user_id} does not exist.")
        
        tenant_id = generate_next_tenant_id(db)

        tenant = Tenant(
            tenant_id=tenant_id,
            user_id=current_user.user_id,
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
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred.")

@router.get("/v1/tenants", response_model=Dict[str, Any],
description=" Master Admin Login required", 
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
async def get_tenants(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: SortOrder = SortOrder.ASC
):
    try:
        query = db.query(Tenant).options(joinedload(Tenant.user))

        if user_id:
            query = query.filter(Tenant.user_id == user_id)
        if name:
            query = query.filter(func.lower(Tenant.name).like(f"%{name.lower()}%"))
        if country:
            query = query.filter(func.lower(Tenant.country) == country.lower())

        sort_columns = {
            "created_at": Tenant.created_at,
            "updated_at": Tenant.updated_at,
            "name": Tenant.name,
            "country": Tenant.country
        }

        if sort_by not in sort_columns:
            raise HTTPException(status_code=400, detail="Invalid sort_by field.")

        query = query.order_by(
            sort_columns[sort_by].desc() if sort_order == SortOrder.DESC else sort_columns[sort_by].asc()
        )

        all_results = query.all()
        paginated_data = paginate(all_results, page, limit)

        response = [
            TenantResponse(
                tenant_id=t.tenant_id,
                user_id=t.user_id,
                user_name=t.user.username if t.user else None,
                name=t.name,
                organization_type=t.organization_type,
                industry_sector=t.industry_sector,
                registration_tax_id=t.registration_tax_id,
                address=t.address,
                country=t.country,
                zip_postal_code=t.zip_postal_code,
                created_at=t.created_at,
                updated_at=t.updated_at
            )
            for t in paginated_data["items"]
        ]

        return {
            "success": True,
            "data": {
                "tenants": response
            },
            "meta": paginated_data["meta"]
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred please try again")
    

@router.get("/v1/tenant", response_model=Dict[str, Any],
description=" Super Admin Login required", 
dependencies=[Depends(JWTBearer()), Depends(get_super_admin)],
)
async def get_tenants(
    db: Session = Depends(get_db), 
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: SortOrder = SortOrder.ASC,
    current_user: User = Depends(get_current_user)
):
    try:
        query = db.query(Tenant).options(joinedload(Tenant.user))

        #if user_id:
        query = query.filter(Tenant.user_id == current_user.user_id)
        
        if not query:
            raise HTTPException(status_code=400, detail="data not found")
        
        if name:
            query = query.filter(func.lower(Tenant.name).like(f"%{name.lower()}%"))
        if country:
            query = query.filter(func.lower(Tenant.country) == country.lower())

        sort_columns = {
            "created_at": Tenant.created_at,
            "updated_at": Tenant.updated_at,
            "name": Tenant.name,
            "country": Tenant.country
        }

        if sort_by not in sort_columns:
            raise HTTPException(status_code=400, detail="Invalid sort_by field.")

        query = query.order_by(
            sort_columns[sort_by].desc() if sort_order == SortOrder.DESC else sort_columns[sort_by].asc()
        )

        all_results = query.all()
        paginated_data = paginate(all_results, page, limit)

        response = [
            TenantResponse(
                tenant_id=t.tenant_id,
                user_id=t.user_id,
                user_name=t.user.username if t.user else None,
                name=t.name,
                organization_type=t.organization_type,
                industry_sector=t.industry_sector,
                registration_tax_id=t.registration_tax_id,
                address=t.address,
                country=t.country,
                zip_postal_code=t.zip_postal_code,
                created_at=t.created_at,
                updated_at=t.updated_at
            )
            for t in paginated_data["items"]
        ]

        return {
            "success": True,
            "data": {
                "tenants": response
            },
            "meta": paginated_data["meta"]
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred please try again")
    