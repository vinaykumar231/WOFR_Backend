from fastapi import APIRouter, Depends, Query, Path, Body, status, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Literal
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from db.session import get_db
from api.v1.models.rbac.role import Role
from api.v1.schemas.rbac_schemas import RoleOut, RoleUpdate, StatusUpdate, SuccessResponse, StatusEnum
from utils.helper_function import SortOrder, filter_items, paginate, sort_items

router = APIRouter()


@router.get("/v1/roles", response_model=SuccessResponse)
async def list_roles(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[StatusEnum] = Query(None),
    sort_by: Literal["role_id", "role_name"] = "role_name",
    order: SortOrder = SortOrder.ASC,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Role)
        if status_filter:
            query = query.filter(Role.status == status_filter)

        all_roles = query.all()
        sorted_roles = sort_items(all_roles, sort_by, order)
        roles_out = [RoleOut.from_orm(role) for role in sorted_roles]
        paginated = paginate(roles_out, page, limit)

        return {
            "success": True,
            "data": {"roles": paginated["items"]},
            "meta": paginated["meta"]
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred please try again")


@router.put("/v1/roles/{role_id}", response_model=SuccessResponse)
async def update_role(
    role_id: int = Path(..., ge=1),
    role_update: RoleUpdate = Body(...),
    db: Session = Depends(get_db)
):
    try:
        role = db.query(Role).filter(Role.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        # Update fields if provided
        if role_update.role_name:
            role.role_name = role_update.role_name
        if role_update.description:
            role.description = role_update.description
        if role_update.status:
            role.status = role_update.status

        db.commit()
        db.refresh(role)

        return {
            "success": True,
            "data": {"role": RoleOut.from_orm(role)},  
            "meta": {
                "message": f"Role with ID {role_id} updated successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred please try again")


@router.patch("/v1/roles/{role_id}", response_model=SuccessResponse)
async def update_role_status(
    role_id: int = Path(...),
    status_update: StatusUpdate = Body(...),
    db: Session = Depends(get_db)
):
    try:
        role = db.query(Role).filter(Role.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        role.status = status_update.status
        role.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(role)

        return {
            "success": True,
            "data": {"role": RoleOut.from_orm(role)},
            "meta": {
                "message": f"Status of role ID {role_id} updated successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred please try again")
