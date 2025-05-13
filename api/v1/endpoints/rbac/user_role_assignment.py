from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db.session import get_db
from api.v1.models.rbac.user_role_assignment import UserRoleAssignment
from api.v1.models.rbac.role_module_action_mapping import RoleModuleActionMapping
#from api.v1.schemas.rbac_schemas import UserRoleAssignmentCreate

router = APIRouter()

class UserRoleAssignmentCreate(BaseModel):
    user_id: str = Field(..., max_length=10)
    tenant_id: int
    role_module_action_mapping_ids: List[int]
    assigned_by: int

@router.post("/v1/assign-user-role-module-actions")
def assign_user_roles(
    request: UserRoleAssignmentCreate,
    db: Session = Depends(get_db)
):
    try:
        created_ids = []

        for mapping_id in request.role_module_action_mapping_ids:
            mapping_exists = db.query(RoleModuleActionMapping).filter_by(role_module_action_mapping_id=mapping_id).first()
            if not mapping_exists:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mapping ID {mapping_id} not found.")

            new_assignment = UserRoleAssignment(
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                role_module_action_mapping_id=mapping_id,
                assigned_by=request.assigned_by,
                assignment_date=datetime.utcnow()
            )
            db.add(new_assignment)
            db.flush()
            created_ids.append(new_assignment.user_role_assignment_id)

        db.commit()

        return {
            "message": "User assigned to role-module-action mappings successfully.",
            "data": {
                "created_user_role_assignment_ids": created_ids,
                "user_id": request.user_id,
                "tenant_id": request.tenant_id
            }
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Assignment failed: {str(e)}")
