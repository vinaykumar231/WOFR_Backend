from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Query,status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from api.v1.schemas.rbac_schemas import ModuleOut, ModuleUpdate, StatusUpdate, SuccessResponse, StatusEnum
from api.v1.models.rbac.module import Module
from auth.auth_bearer import get_master_admin  # optional if using auth
from db.session import get_db
from utils.helper_function import SortOrder, filter_items, paginate, sort_items
from fastapi import HTTPException, Path, Body
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()
load_dotenv()

@router.get("/v1/modules", response_model=SuccessResponse)
async def list_modules(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[StatusEnum] = Query(None),
    module_name: Optional[str] = Query(None),
    sort_by: Literal["module_id", "module_name"] = "module_name",
    order: SortOrder = SortOrder.ASC,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Module)

        if status_filter:
            query = query.filter(Module.status == status_filter)

        if module_name:
            # Case-insensitive match using lower() from both sides
            query = query.filter(func.lower(Module.module_name) == module_name.lower())

        all_modules = query.all()
        sorted_modules = sort_items(all_modules, sort_by, order)

        # Convert to Pydantic models
        modules_out = [ModuleOut.from_orm(module) for module in sorted_modules]

        paginated = paginate(modules_out, page, limit)

        return {
            "success": True,
            "data": {"modules": paginated["items"]},
            "meta": paginated["meta"],
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error occurred, please try again.")


@router.put("/v1/modules/{module_id}", response_model=SuccessResponse)
async def update_module(
    module_id: int = Path(..., ge=1),
    module_update: ModuleUpdate = Body(...),
    db: Session = Depends(get_db),
):
    try:
        module = db.query(Module).filter(Module.module_id == module_id).first()
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

        if module_update.module_name is not None:
            module.module_name = module_update.module_name
        if module_update.description is not None:
            module.description = module_update.description
        if module_update.status is not None:
            module.status = module_update.status

        db.commit()
        db.refresh(module)

        return {
            "success": True,
            "data": {"module": ModuleOut.from_orm(module)},
        }
    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred please try again")


@router.patch("/modules/{module_id}")
async def update_module_status(
    module_id: int = Path(..., title="Module ID"),
    status_update: StatusUpdate = Body(...),  
    db: Session = Depends(get_db)
):
    try:
        module = db.query(Module).filter(Module.module_id == module_id).first()
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

        module.status = status_update.status
        module.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(module)

        return {
            "success": True,
            "data": {"module": ModuleOut.from_orm(module)},
            "meta": {
                "message": f"Status of module ID {module_id} updated successfully",
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