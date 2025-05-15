from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from api.v1.models.tenants.tenant import Tenant
from api.v1.models.tenants.tenant_user import TenantUser
from api.v1.models.user.user_auth import User
from api.v1.schemas.tenant_schemas import TenantUserCreate, TenantUserResponse
from db.session import get_db
from auth.auth_bearer import JWTBearer, get_current_user, get_super_admin
from utils.helper_function import SortOrder, paginate
from utils.validators import generate_next_tenant_user_id

router = APIRouter()

@router.post("/v1/tenant-user", response_model=None, status_code=status.HTTP_201_CREATED)
async def create_tenant_user(
    request: TenantUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        tenant = db.query(Tenant).filter(Tenant.user_id == current_user.user_id).first()
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Tenant not found for the current user.")

        if db.query(TenantUser).filter(TenantUser.email == request.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email is already registered.")

        tenant_user_id = generate_next_tenant_user_id(db)

        tenant_user = TenantUser(
            tenant_user_id=tenant_user_id,
            tenant_id=tenant.tenant_id,
            name=request.name,
            email=request.email,
            position=request.position,
            department=request.department,
            contact_number=request.contact_number,
            address=request.address
        )

        db.add(tenant_user)
        db.commit()
        db.refresh(tenant_user)

        return tenant_user

    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database error occurred while creating tenant user.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="An unexpected error occurred while creating tenant user.")
    
@router.get(
    "/v1/tenant-user",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    description="Super Admin Login required",
    dependencies=[Depends(JWTBearer()), Depends(get_super_admin)],
)
async def get_tenant_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    email: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: SortOrder = SortOrder.ASC
):
    try:
        query = db.query(TenantUser).options(joinedload(TenantUser.tenant))

        if email:
            query = query.filter(func.lower(TenantUser.email) == email.lower())
        if name:
            query = query.filter(func.lower(TenantUser.name).like(f"%{name.lower()}%"))
        if department:
            query = query.filter(func.lower(TenantUser.department).like(f"%{department.lower()}%"))

        sort_columns = {
            "created_at": TenantUser.created_at,
            "updated_at": TenantUser.updated_at,
            "name": TenantUser.name,
            "email": TenantUser.email,
            "department": TenantUser.department,
        }

        if sort_by not in sort_columns:
            valid_fields = ", ".join(sort_columns.keys())
            raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Valid options: {valid_fields}")

        query = query.order_by(
            sort_columns[sort_by].desc() if sort_order == SortOrder.DESC else sort_columns[sort_by].asc()
        )

        all_results = query.all()
        paginated_data = paginate(all_results, page, limit)  

        response = []
        for tenant_user in paginated_data["items"]:
            tu_response = TenantUserResponse.from_orm(tenant_user).dict()
            tu_response["tenant_name"] = tenant_user.tenant.name if tenant_user.tenant else None
            response.append(tu_response)

        return {
            "success": True,
            "data": {
                "tenant_users": response
            },
            "meta": paginated_data["meta"]
        }

    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred while fetching tenant users.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred. Please try again. {e}")
