# routers/tenant_user_role_mapping.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from api.v1.models.rbac.role_module_action_mapping import RoleModuleActionMapping
from api.v1.models.tenants.tenant import Tenant
from api.v1.models.tenants.tenant_user import TenantUser
from api.v1.models.tenants.tenant_user_assign_role import TenantUserRoleAssign
from api.v1.schemas.tenant_schemas import TenantUserRoleAssignSimpleResponse, TenantUserRoleAssignmentCreate
from auth.auth_bearer import JWTBearer, get_master_admin, get_super_admin
from db.session import get_db
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import joinedload
from utils.helper_function import paginate


router = APIRouter()


@router.post(
    "/v1/assign-tenant-user-role-module-actions",
    description="Super Admin Login required",
    dependencies=[Depends(JWTBearer()), Depends(get_super_admin)]
)
async def assign_roles_to_tenant_user(
    request: TenantUserRoleAssignmentCreate,
    db: Session = Depends(get_db)
):
    try:
        tenant_user = db.query(TenantUser).filter_by(tenant_user_id=request.tenant_user_id).first()
        if not tenant_user:
            raise HTTPException(status_code=404, detail="Tenant user not found")

        tenant = db.query(Tenant).filter_by(tenant_id=request.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        role_module_action_mapping = db.query(RoleModuleActionMapping).filter_by(role_module_action_mapping_id=request.role_module_action_mapping_id).first()

        if not role_module_action_mapping:
            raise HTTPException(status_code=404, detail="Role-module-action mapping not found")

        existing_assignment = db.query(TenantUserRoleAssign).filter_by(tenant_user_id=request.tenant_user_id,
                                   role_module_action_mapping_id=request.role_module_action_mapping_id).first()

        if existing_assignment:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Role-module-action already assigned to this tenant user.")

        new_assignment = TenantUserRoleAssign(
            tenant_user_id=request.tenant_user_id,
            role_module_action_mapping_id=request.role_module_action_mapping_id,
            tenant_id=request.tenant_id,
            assignment_date=datetime.utcnow()
        )

        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)

        return {
            "message": "Tenant user successfully assigned role-module-action mapping.",
            "data": {
                "tenant_user_role_mapping_id": new_assignment.tenant_user_role_mapping_id,
                "tenant_user_id": request.tenant_user_id,
                "role_module_action_mapping_id": request.role_module_action_mapping_id,
                "tenant_id": request.tenant_id
            }
        }

    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database error occurred"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Unexpected error occurred, please try again. {e}")
    

@router.get(
    "/v1/tenant-user-role-assignments",
    description="Super Admin required",
    response_model=List[TenantUserRoleAssignSimpleResponse],
    dependencies=[Depends(JWTBearer()), Depends(get_super_admin)]  
)
async def get_tenant_user_role_assignments(
    db: Session = Depends(get_db),
    tenant_user_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    role_module_action_mapping_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    try:
        query = (
            db.query(TenantUserRoleAssign)
            .options(
                joinedload(TenantUserRoleAssign.role_module_action_mapping)
                .joinedload(RoleModuleActionMapping.role),
                joinedload(TenantUserRoleAssign.role_module_action_mapping)
                .joinedload(RoleModuleActionMapping.module),
                joinedload(TenantUserRoleAssign.role_module_action_mapping)
                .joinedload(RoleModuleActionMapping.action),
                joinedload(TenantUserRoleAssign.tenant)
            )
        )

        if tenant_user_id:
            query = query.filter(TenantUserRoleAssign.tenant_user_id == tenant_user_id)
        if tenant_id:
            query = query.filter(TenantUserRoleAssign.tenant_id == tenant_id)
        if role_module_action_mapping_id:
            query = query.filter(
                TenantUserRoleAssign.role_module_action_mapping_id == role_module_action_mapping_id
            )

        all_results = query.all()
        paginated_data = paginate(all_results, page, limit)  #
        return paginated_data["items"]

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database error occurred while fetching tenant user role assignments.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Unexpected error occurred. Please try again. {e}")
    





# from typing import List

# class TenantUserRoleAssignmentBulkCreate(BaseModel):
#     tenant_user_id: str
#     tenant_id: str
#     role_module_action_mapping_ids: List[int]  # multiple ids here

# @router.post(
#     "/v1/assign-tenant-user-role-module-actions",
#     description="Super Admin Login required",
#     dependencies=[Depends(JWTBearer()), Depends(get_super_admin)]
# )
# async def assign_roles_to_tenant_user_bulk(
#     request: TenantUserRoleAssignmentBulkCreate,
#     db: Session = Depends(get_db)
# ):
#     try:
#         tenant_user = db.query(TenantUser).filter_by(tenant_user_id=request.tenant_user_id).first()
#         if not tenant_user:
#             raise HTTPException(status_code=404, detail="Tenant user not found")

#         tenant = db.query(Tenant).filter_by(tenant_id=request.tenant_id).first()
#         if not tenant:
#             raise HTTPException(status_code=404, detail="Tenant not found")

#         # Fetch all RoleModuleActionMapping records by IDs
#         mappings = db.query(RoleModuleActionMapping).filter(
#             RoleModuleActionMapping.role_module_action_mapping_id.in_(request.role_module_action_mapping_ids)
#         ).all()

#         if len(mappings) != len(request.role_module_action_mapping_ids):
#             raise HTTPException(status_code=404, detail="One or more Role-module-action mappings not found")

#         # Check existing assignments to avoid duplicates
#         existing_assignments = db.query(TenantUserRoleAssign).filter(
#             TenantUserRoleAssign.tenant_user_id == request.tenant_user_id,
#             TenantUserRoleAssign.role_module_action_mapping_id.in_(request.role_module_action_mapping_ids)
#         ).all()

#         existing_ids = {ea.role_module_action_mapping_id for ea in existing_assignments}

#         new_assignments = []
#         for mapping_id in request.role_module_action_mapping_ids:
#             if mapping_id in existing_ids:
#                 # Skip or optionally raise conflict error here
#                 continue

#             new_assignment = TenantUserRoleAssign(
#                 tenant_user_id=request.tenant_user_id,
#                 role_module_action_mapping_id=mapping_id,
#                 tenant_id=request.tenant_id,
#                 assignment_date=datetime.utcnow()
#             )
#             new_assignments.append(new_assignment)
#             db.add(new_assignment)

#         if not new_assignments:
#             return {"message": "No new role-module-action mappings were assigned (all were already assigned)."}

#         db.commit()

#         return {
#             "message": f"Successfully assigned {len(new_assignments)} role-module-action mappings.",
#             "assigned_ids": [a.role_module_action_mapping_id for a in new_assignments]
#         }

#     except HTTPException:
#         raise
#     except SQLAlchemyError:
#         db.rollback()
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred, please try again. {e}")