from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from api.v1.models.rbac.role_module_action_mapping import RoleModuleActionMapping
from api.v1.schemas.rbac_schemas import RoleModuleActionMappingCreate, RoleModuleActionResponse
from sqlalchemy.orm import Session, joinedload
from db.session import get_db


router = APIRouter()

@router.post("/assign_module_action_to_role")
def assign_module_action_to_role(
    request: RoleModuleActionMappingCreate,
    db: Session = Depends(get_db)
):
    # Optional: Check if the same mapping already exists
    existing_mapping = db.query(RoleModuleActionMapping).filter(
        RoleModuleActionMapping.module_id == request.module_id,
        RoleModuleActionMapping.action_id == request.action_id,
        RoleModuleActionMapping.role_id == request.role_id
    ).first()

    if existing_mapping:
        raise HTTPException(status_code=400, detail="This role-module-action mapping already exists.")

    try:
        new_mapping = RoleModuleActionMapping(
            module_id=request.module_id,
            action_id=request.action_id,
            role_id=request.role_id,
            assigned_by=request.assigned_by
        )
        db.add(new_mapping)
        db.commit()
        db.refresh(new_mapping)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to assign: {str(e)}")

    return {
        "message": "Role-Module-Action mapping assigned successfully.",
        "data": {
            "role_module_action_mapping_id": new_mapping.role_module_action_mapping_id,
            "module_id": new_mapping.module_id,
            "action_id": new_mapping.action_id,
            "role_id": new_mapping.role_id,
            "assigned_by": new_mapping.assigned_by,
            "assignment_date": new_mapping.assignment_date
        }
    }


@router.get("/role-module-actions/", response_model=list[RoleModuleActionResponse])
def get_role_module_action_mappings(db: Session = Depends(get_db)):
    results = db.query(RoleModuleActionMapping)\
        .options(
            joinedload(RoleModuleActionMapping.user),    # Load user (assigner)
            joinedload(RoleModuleActionMapping.module),  # Load module
            joinedload(RoleModuleActionMapping.action),  # Load action
            joinedload(RoleModuleActionMapping.role)     # Load role
        ).all()

    response = []
    for item in results:
        response.append(RoleModuleActionResponse(
            role_module_action_mapping_id=item.role_module_action_mapping_id,
            module_id=item.module_id,
            module_name=item.module.module_name if item.module else None,
            action_id=item.action_id,
            action_name=item.action.action_name if item.action else None,
            role_id=item.role_id,
            role_name=item.role.role_name if item.role else None,  # Assuming Role model has role_name field
            assigner_id=item.assigned_by,
            assigner_name=item.user.username if item.user else None,
            assignment_date=item.assignment_date
        ))

    return response