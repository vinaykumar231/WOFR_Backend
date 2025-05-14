from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.auth_handler import decodeJWT
from db.session import get_db
from sqlalchemy.orm import Session
from typing import Optional
from api.v1.models.user import User
from jwt import PyJWTError


# user_ops = User()

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authorization code.")

    @staticmethod
    def verify_jwt(jwt_token: str) -> bool:
        try:
            payload = decodeJWT(jwt_token)
            return payload is not None
        except Exception as e:
            print(str(e))
            return False


def get_user_id_from_token(token: str = Depends(JWTBearer())):
    payload = decodeJWT(token)

    if payload:
        return payload.get("user_id")
    else:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invalid or expired token")
    

def get_master_admin(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type != "master_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def get_super_admin(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def get_admin(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def get_employee(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type != "employee":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def get_master_admin_or_super_admin(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type not in ["master_admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def get_super_admin_or_admin(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type != ["super_admin", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def get_super_admin_or_employee(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type not in ["super_admin","employee"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def get_admin_or_employee(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type != ["admin", "employee"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def get_super_admin_or_admin_or_employee(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type != ["super_admin", "admin", "employee"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def get_master_admin_super_admin_or_admin__employee(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type not in ["master_admin", "super_admin", "admin", "employee"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return user

def login_required(user_id: int = Depends(get_user_id_from_token), db: Session = Depends(get_db)) -> Optional[User]:
   
    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

def get_current_user(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)) -> Optional[User]:
    try:
        payload = decodeJWT(token)
        if payload:
            user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

