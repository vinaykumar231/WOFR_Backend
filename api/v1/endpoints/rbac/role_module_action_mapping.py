from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query,status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from api.v1.models.rbac.action import Action
from api.v1.models.rbac.module import Module
from api.v1.models.rbac.role import Role
from api.v1.models.rbac.role_module_action_mapping import RoleModuleActionMapping
from api.v1.schemas.rbac_schemas import RoleModuleActionResponse, RoleModuleAssignments, RoleModuleAssignmentsUpdate, RoleModuleStatusUpdate, StatusEnum
from sqlalchemy.orm import Session, joinedload
from db.session import get_db
from utils.helper_function import SortOrder, paginate, sort_items
from sqlalchemy.exc import SQLAlchemyError


router = APIRouter()

@router.post("/v1/mapping-module-actions-roles")
def assign_module_actions_bulk(
    request: RoleModuleAssignments,
    db: Session = Depends(get_db)
):
    try:
        new_ids = []
        existing_mappings = []

        for assignment in request.assignments:
            for action_id in assignment.action_ids:
                action_exists = db.query(Action).filter(Action.action_id == action_id).first()
                if not action_exists:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action ID {action_id} does not exist.")
        try:
            for assignment in request.assignments:
                for role_id in assignment.role_id:  
                    for action_id in assignment.action_ids:
                        existing = db.query(RoleModuleActionMapping).filter_by(module_id=request.module_id,role_id=role_id,action_id=action_id).first()

                        if existing:
                            existing_mappings.append({
                                "role_id": role_id,
                                "action_id": action_id
                            })
                        else:
                            mapping = RoleModuleActionMapping(
                                module_id=request.module_id,
                                role_id=role_id,
                                action_id=action_id,
                                assigned_by=request.assigned_by,
                                status=assignment.status,
                                assignment_date=datetime.utcnow()
                            )
                            db.add(mapping)
                            db.flush()
                            new_ids.append(mapping.role_module_action_mapping_id)

            db.commit()

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Assignment failed: {str(e)}")

        action_ids = sorted(set(aid for r in request.assignments for aid in r.action_ids))
        role_ids = sorted(set(rid for r in request.assignments for rid in r.role_id))

        return {
            "message": "Role-Module-Action mappings assigned successfully.",
            "data": {
                "role_module_action_mapping_ids": new_ids,
                "module_id": request.module_id,
                "action_ids": action_ids,
                "role_ids": role_ids,
                "assigned_by": request.assigned_by,
                "assignment_date": datetime.utcnow(),
                "existing_mappings": existing_mappings
            }
        }
    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred, please try again.")
    

@router.get("/v1/mapped-module-actions-roles", response_model=Dict[str, Any])
def get_role_module_action_mappings(
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page", ge=1),
    limit: int = Query(10, alias="limit", ge=1, le=100),
    module_name: Optional[str] = Query(None, alias="module_name"),
    action_name: Optional[str] = Query(None, alias="action_name"),
    role_name: Optional[str] = Query(None, alias="role_name"),
    sort_by: str = Query("assignment_date", alias="sort_by"),
    sort_order: SortOrder = SortOrder.ASC
):
    try:
        query = db.query(RoleModuleActionMapping).options(
            joinedload(RoleModuleActionMapping.user),
            joinedload(RoleModuleActionMapping.module),
            joinedload(RoleModuleActionMapping.action),
            joinedload(RoleModuleActionMapping.role)
        )

        if module_name:
            query = query.join(RoleModuleActionMapping.module).filter(func.lower(Module.module_name) == module_name.lower())
        if action_name:
            query = query.join(RoleModuleActionMapping.action).filter(func.lower(Action.action_name) == action_name.lower())
        if role_name:
            query = query.join(RoleModuleActionMapping.role).filter(func.lower(Role.role_name) == role_name.lower())

        sort_columns = {
            "assignment_date": RoleModuleActionMapping.assignment_date,
            "module_name": Module.module_name,
            "action_name": Action.action_name,
            "role_name": Role.role_name
        }

        if sort_by not in sort_columns:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid sort_by field.")

        sort_column = sort_columns[sort_by]

        if sort_by in ["module_name", "action_name", "role_name"]:
            if sort_by == "module_name":
                query = query.join(RoleModuleActionMapping.module)
            elif sort_by == "action_name":
                query = query.join(RoleModuleActionMapping.action)
            elif sort_by == "role_name":
                query = query.join(RoleModuleActionMapping.role)

        query = query.order_by(sort_column.desc() if sort_order == SortOrder.DESC else sort_column.asc())

        all_results = query.all()  
        paginated_data = paginate(all_results, page, limit)

        response = []
        for item in paginated_data["items"]:
            response.append({
                "role_module_action_mapping_id": item.role_module_action_mapping_id,
                "module_id": item.module_id,
                "module_name": item.module.module_name if item.module else None,
                "action_id": item.action_id,
                "action_name": item.action.action_name if item.action else None,
                "role_id": item.role_id,
                "role_name": item.role.role_name if item.role else None,
                "mapper_id": item.assigned_by,
                "mapper_name": item.user.username if item.user else None,
                "assignment_date": item.assignment_date
            })

        return {
            "success": True,
            "data": {"modules": response},
            "meta": paginated_data["meta"]
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred, please try again.")


@router.put("/v1//update-module-actions-roles")
def update_module_actions_bulk(
    role_module_action_mapping_id: int,  
    request: RoleModuleAssignmentsUpdate,
    db: Session = Depends(get_db)
):
    updated_data = []

    module_exists = db.query(Module).filter(Module.module_id == request.module_id).first()
    if not module_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Module ID {request.module_id} does not exist.")

    try:
        for assignment in request.assignments:
            for action_id in assignment.action_ids or []:
                action_exists = db.query(Action).filter(Action.action_id == action_id).first()
                if not action_exists:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action ID {action_id} does not exist.")

            for assignment in request.assignments:
                existing_mapping = db.query(RoleModuleActionMapping).filter_by(role_module_action_mapping_id=role_module_action_mapping_id).first()

                if existing_mapping:
                    if assignment.role_id:
                        existing_mapping.role_id = assignment.role_id
                    if assignment.action_ids:
                        existing_mapping.action_id = assignment.action_ids[0]  
                    if assignment.assigned_by:
                        existing_mapping.assigned_by = assignment.assigned_by
                    if assignment.status:
                        existing_mapping.status = assignment.status
                    existing_mapping.updated_at = datetime.utcnow()

                    db.commit() 
                    updated_data.append({
                        "role_module_action_mapping_id": existing_mapping.role_module_action_mapping_id,
                        "module_id": existing_mapping.module_id,
                        "role_id": existing_mapping.role_id,
                        "action_id": existing_mapping.action_id,
                        "status": existing_mapping.status,
                        "assigned_by": existing_mapping.assigned_by,
                        "updated_at": existing_mapping.updated_at
                    })
                else:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mapping ID {assignment.role_module_action_mapping_id} not found.")

        return {
            "message": "Role-Module-Action mappings updated successfully.",
            "data": {
                "updated_role_module_action_mapping_data": updated_data,
            }
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred, please try again.")
    

@router.patch("/v1/update-role-module-action-status")
def update_status_for_mappings(
    request: RoleModuleStatusUpdate,
    db: Session = Depends(get_db)
):
    updated_ids = []

    try:
        for mapping_id in request.mapping_ids:
            mapping = db.query(RoleModuleActionMapping).filter_by(role_module_action_mapping_id=mapping_id).first()

            if not mapping:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mapping ID {mapping_id} not found.")

            mapping.status = request.status
            mapping.updated_at = datetime.utcnow()
            db.add(mapping)
            updated_ids.append(mapping_id)

        db.commit()

        return {
            "message": f"Status updated to '{request.status}' for the provided mappings.",
            "data": {
                "updated_mapping_ids": updated_ids,
                "new_status": request.status
            }
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred, please try again.")
