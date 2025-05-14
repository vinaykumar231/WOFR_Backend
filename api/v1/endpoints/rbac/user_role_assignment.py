from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from api.v1.models.rbac.action import Action
from api.v1.models.rbac.module import Module
from api.v1.models.rbac.role import Role
from api.v1.models.user.user_auth import User
from api.v1.schemas.rbac_schemas import UserRoleAssignmentCreate
from auth.auth_bearer import JWTBearer, get_current_user, get_master_admin, get_super_admin
from db.session import get_db
from api.v1.models.rbac.user_role_assignment import UserRoleAssignment
from api.v1.models.rbac.role_module_action_mapping import RoleModuleActionMapping
from utils.helper_function import SortOrder, paginate
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
#from api.v1.schemas.rbac_schemas import UserRoleAssignmentCreate

router = APIRouter()



@router.post("/v1/assign-user-role-module-actions", 
description=" Master Admin Login required",
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
def assign_user_roles_by_module(
    request: UserRoleAssignmentCreate,
    db: Session = Depends(get_db)
):
    try:
        created_ids = []

        mappings = db.query(RoleModuleActionMapping).filter_by(module_id=request.module_id).all()

        if not mappings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No role-module-action mappings found for module ID {request.module_id}."
            )

        for mapping in mappings:
            existing_assignment = db.query(UserRoleAssignment).filter_by(user_id=request.user_id,
                role_module_action_mapping_id=mapping.role_module_action_mapping_id,
                tenant_id=request.tenant_id
            ).first()

            if not existing_assignment:
                new_assignment = UserRoleAssignment(
                    user_id=request.user_id,
                    tenant_id=request.tenant_id,
                    role_module_action_mapping_id=mapping.role_module_action_mapping_id,
                    assigned_by=request.assigned_by,
                    assignment_date=datetime.utcnow()
                )
                db.add(new_assignment)
                db.flush()
                created_ids.append(new_assignment.user_role_assignment_id)

        db.commit()

        return {
            "message": "User assigned to all role-module-action mappings for the given module.",
            "data": {
                "created_user_role_assignment_ids": created_ids,
                "user_id": request.user_id,
                "tenant_id": request.tenant_id,
                "module_id": request.module_id
            }
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred please try again")
    
    

@router.get("/v1/users-roles-assiged",response_model=Dict[str, Any],
description="Master Admin Login required",
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
def get_user_role_assigned(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    module_name: Optional[str] = Query(None),
    role_name: Optional[str] = Query(None),
    action_name: Optional[str] = Query(None),
    sort_by: str = Query("assignment_date"),
    sort_order: SortOrder = SortOrder.ASC
):
    try:
        query = db.query(UserRoleAssignment).options(
            joinedload(UserRoleAssignment.role_module_action_mappings)
            .joinedload(RoleModuleActionMapping.module),
            joinedload(UserRoleAssignment.role_module_action_mappings)
            .joinedload(RoleModuleActionMapping.action),
            joinedload(UserRoleAssignment.role_module_action_mappings)
            .joinedload(RoleModuleActionMapping.role)
        )

        # Filtering
        if user_id:
            query = query.filter(UserRoleAssignment.user_id == user_id)
        if tenant_id:
            query = query.filter(UserRoleAssignment.tenant_id == tenant_id)
        if module_name:
            query = query.join(UserRoleAssignment.role_module_action_mappings)\
                .join(RoleModuleActionMapping.module)\
                .filter(func.lower(Module.module_name) == module_name.lower())
        if role_name:
            query = query.join(UserRoleAssignment.role_module_action_mappings)\
                .join(RoleModuleActionMapping.role)\
                .filter(func.lower(Role.role_name) == role_name.lower())
        if action_name:
            query = query.join(UserRoleAssignment.role_module_action_mappings)\
                .join(RoleModuleActionMapping.action)\
                .filter(func.lower(Action.action_name) == action_name.lower())

        sort_columns = {
            "assignment_date": UserRoleAssignment.assignment_date,
            "module_name": Module.module_name,
            "action_name": Action.action_name,
            "role_name": Role.role_name
        }

        if sort_by not in sort_columns:
            raise HTTPException(status_code=400, detail="Invalid sort_by field.")

        if sort_by in ["module_name", "action_name", "role_name"]:
            if sort_by == "module_name":
                query = query.join(UserRoleAssignment.role_module_action_mappings).join(RoleModuleActionMapping.module)
            elif sort_by == "action_name":
                query = query.join(UserRoleAssignment.role_module_action_mappings).join(RoleModuleActionMapping.action)
            elif sort_by == "role_name":
                query = query.join(UserRoleAssignment.role_module_action_mappings).join(RoleModuleActionMapping.role)

        query = query.order_by(
            sort_columns[sort_by].desc() if sort_order == SortOrder.DESC else sort_columns[sort_by].asc()
        )

        all_results = query.all()
        paginated_data = paginate(all_results, page, limit)

        response = []
        for assignment in paginated_data["items"]:
            mappings = assignment.role_module_action_mappings
            if isinstance(mappings, list):  
                for mapping in mappings:
                    response.append({
                        "user_role_assignment_id": assignment.user_role_assignment_id,
                        "user_id": assignment.user_id,
                        "tenant_id": assignment.tenant_id,
                        "assigned_by": assignment.assigned_by,
                        "assignment_date": assignment.assignment_date,
                        "role_module_action_mapping_id": mapping.role_module_action_mapping_id,
                        "module_id": mapping.module_id,
                        "module_name": mapping.module.module_name if mapping.module else None,
                        "action_id": mapping.action_id,
                        "action_name": mapping.action.action_name if mapping.action else None,
                        "role_id": mapping.role_id,
                        "role_name": mapping.role.role_name if mapping.role else None,
                        "status": mapping.status
                    })
            else:  
                mapping = mappings
                if mapping:
                    response.append({
                        "user_role_assignment_id": assignment.user_role_assignment_id,
                        "user_id": assignment.user_id,
                        "tenant_id": assignment.tenant_id,
                        "assigned_by": assignment.assigned_by,
                        "assignment_date": assignment.assignment_date,
                        "role_module_action_mapping_id": mapping.role_module_action_mapping_id,
                        "module_id": mapping.module_id,
                        "module_name": mapping.module.module_name if mapping.module else None,
                        "action_id": mapping.action_id,
                        "action_name": mapping.action.action_name if mapping.action else None,
                        "role_id": mapping.role_id,
                        "role_name": mapping.role.role_name if mapping.role else None,
                        "status": mapping.status
                    })

        return {
            "success": True,
            "data": {
                "assignments": response
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
    
    
@router.get("/v1/user-role-assignd", response_model=Dict[str, Any],
description=" Super Admin Login required",
dependencies=[Depends(JWTBearer()), Depends(get_super_admin)]
)
def get_user_role_assignments(
    db: Session = Depends(get_db),
    tenant_id: str = Query(...), 
    #user_id: Optional[str] = Query(None)
    current_user: User = Depends(get_current_user)
):
    try:
        query = db.query(UserRoleAssignment).options(
            joinedload(UserRoleAssignment.role_module_action_mappings)
            .joinedload(RoleModuleActionMapping.module),
            joinedload(UserRoleAssignment.role_module_action_mappings)
            .joinedload(RoleModuleActionMapping.action),
            joinedload(UserRoleAssignment.role_module_action_mappings)
            .joinedload(RoleModuleActionMapping.role)
        )

        query = query.filter(UserRoleAssignment.user_id == current_user.user_id)

        if tenant_id:
            query = query.filter(func.lower(UserRoleAssignment.tenant_id) == func.lower(tenant_id))

        all_results = query.all()

        if not all_results:
            return {
                "success": True,
                "data": {
                    "assignments": []
                }
            }

        response = []
        for assignment in all_results:
            mappings = assignment.role_module_action_mappings
            if isinstance(mappings, list):  
                for mapping in mappings:
                    response.append({
                        "user_role_assignment_id": assignment.user_role_assignment_id,
                        "user_id": assignment.user_id,
                        "tenant_id": assignment.tenant_id,
                        "assigned_by": assignment.assigned_by,
                        "assignment_date": assignment.assignment_date,
                        "role_module_action_mapping_id": mapping.role_module_action_mapping_id,
                        "module_id": mapping.module_id,
                        "module_name": mapping.module.module_name if mapping.module else None,
                        "action_id": mapping.action_id,
                        "action_name": mapping.action.action_name if mapping.action else None,
                        "role_id": mapping.role_id,
                        "role_name": mapping.role.role_name if mapping.role else None,
                        "status": mapping.status
                    })
            else:  
                mapping = mappings
                if mapping:
                    response.append({
                        "user_role_assignment_id": assignment.user_role_assignment_id,
                        "user_id": assignment.user_id,
                        "tenant_id": assignment.tenant_id,
                        "assigned_by": assignment.assigned_by,
                        "assignment_date": assignment.assignment_date,
                        "role_module_action_mapping_id": mapping.role_module_action_mapping_id,
                        "module_id": mapping.module_id,
                        "module_name": mapping.module.module_name if mapping.module else None,
                        "action_id": mapping.action_id,
                        "action_name": mapping.action.action_name if mapping.action else None,
                        "role_id": mapping.role_id,
                        "role_name": mapping.role.role_name if mapping.role else None,
                        "status": mapping.status
                    })

        return {
            "success": True,
            "data": {
                "assignments": response
            }
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred please try again")
    