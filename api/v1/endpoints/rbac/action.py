from fastapi import APIRouter, Body, Depends, Query, Path, HTTPException,status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional, Literal
from api.v1.models.rbac.action import Action
from api.v1.schemas.rbac_schemas import ActionOut, StatusUpdate, SuccessResponse, StatusEnum, ActionUpdate
from auth.auth_bearer import JWTBearer, get_master_admin
from db.session import get_db
from utils.helper_function import paginate, sort_items, SortOrder
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

@router.get("/v1/actions", response_model=SuccessResponse, 
description=" Master Admin Login required", 
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
async def list_actions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[StatusEnum] = Query(None),
    action_name: Optional[str] = Query(None),
    sort_by: Literal["action_id", "action_name"] = "action_id",
    order: SortOrder = SortOrder.ASC,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Action)

        if status_filter:
            query = query.filter(Action.status == status_filter)

        if action_name:
            query = query.filter(func.lower(Action.action_name) == action_name.lower())

        all_actions = query.all()
        sorted_actions = sort_items(all_actions, sort_by, order)

        actions_out = [ActionOut.from_orm(action) for action in sorted_actions]
        paginated = paginate(actions_out, page, limit)

        return {
            "success": True,
            "data": {"actions": paginated["items"]},
            "meta": paginated["meta"]
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred please try again.")
    
@router.put("/v1/actions/{action_id}", response_model=SuccessResponse, 
description=" Master Admin Login required", 
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
async def update_action(
    action_id: int = Path(..., ge=1),
    action_data: ActionUpdate = Depends(),
    db: Session = Depends(get_db)
):
    try:
        action = db.query(Action).filter(Action.action_id == action_id).first()
        if not action:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

        for field, value in action_data.dict(exclude_unset=True).items():
            setattr(action, field, value)

        db.commit()
        db.refresh(action)

        return {
            "success": True,
            "data": {"action": ActionOut.from_orm(action)},
            "meta": {
                "message": f"Action with ID {action_id} updated successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred please try again")
    

@router.patch("/v1/actions/{action_id}", response_model=SuccessResponse, 
description=" Master Admin Login required",
dependencies=[Depends(JWTBearer()), Depends(get_master_admin)]
)
async def update_action_status(
    action_id: int = Path(..., ge=1),
    status_update: StatusUpdate = Body(...),
    db: Session = Depends(get_db)
):
    try:
        action = db.query(Action).filter(Action.action_id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")

        new_status = status_update.status
        if new_status not in StatusEnum.__members__:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid status value")

        action.status = new_status
        action.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(action)

        return {
            "success": True,
            "data": {"action": ActionOut.from_orm(action)},
            "meta": {
                "message": f"Status of action ID {action_id} updated successfully ",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except HTTPException as e:                                                                                         
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")
