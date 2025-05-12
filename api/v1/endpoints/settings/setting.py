from fastapi import APIRouter, Depends, HTTPException,status
from pydantic import BaseModel
from auth.auth_bearer import JWTBearer, get_master_admin
from core.config import read_config, update_config


router = APIRouter()

@router.get("/config-values", status_code=status.HTTP_200_OK,  dependencies=[Depends(JWTBearer()), Depends(get_master_admin)])
def get_config_values():
    return read_config()

class ConfigUpdateRequest(BaseModel):
    key: str
    value: str

@router.put("/config-values", status_code=status.HTTP_200_OK,  dependencies=[Depends(JWTBearer()), Depends(get_master_admin)])
def update_config_values(payload: ConfigUpdateRequest):
    try:
        updated = update_config(payload.key, payload.value)
        return {"message": "Config updated successfully", "updated_config": updated}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    