from fastapi import APIRouter, Depends, Query, Path, Body, status, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional, Literal
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from auth.auth_bearer import JWTBearer, get_master_admin
from db.session import get_db
from api.v1.models.rbac.role import Role
from api.v1.schemas.rbac_schemas import RoleCreate, RoleOut, RoleUpdate, StatusUpdate, SuccessResponse, StatusEnum
from utils.helper_function import SortOrder, filter_items, paginate, sort_items

router = APIRouter()


@router.get("/v1/roles", response_model=SuccessResponse, 
description=" Master Admin Login required",
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
async def list_roles(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[StatusEnum] = Query(None),
    role_name: Optional[str] = Query(None),
    sort_by: Literal["role_id", "role_name"] = "role_id",
    order: SortOrder = SortOrder.ASC,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Role)

        if status_filter:
            query = query.filter(Role.status == status_filter)

        if role_name:
            query = query.filter(func.lower(Role.role_name) == role_name.lower())

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
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred please try again")
    
@router.post("/v1/roles", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED,  
description=" Master Admin Login required",
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
async def create_role(
    role_create: RoleCreate = Body(...),
    db: Session = Depends(get_db)
):
    try:
        existing_role = db.query(Role).filter(Role.role_name == role_create.role_name).first()
        if existing_role:
            raise HTTPException(status_code=400, detail="Role with this name already exists.")

        new_role = Role(
            role_name=role_create.role_name,
            description=role_create.description,
            status=role_create.status
        )
        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        return {
            "success": True,
            "data": {"role": RoleOut.from_orm(new_role)},
            "meta": {
                "message": "Role created successfully",
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred: {str(e)}")



@router.put("/v1/roles/{role_id}", response_model=SuccessResponse, 
description=" Master Admin Login required", 
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
async def update_role(
    role_id: int = Path(..., ge=1),
    role_update: RoleUpdate = Body(...),
    db: Session = Depends(get_db)
):
    try:
        role = db.query(Role).filter(Role.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

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


@router.patch("/v1/roles/{role_id}", response_model=SuccessResponse,  
description=" Master Admin Login required", 
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
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
