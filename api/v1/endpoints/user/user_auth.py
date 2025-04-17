from datetime import datetime, time, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from api.v1.schemas import LoginUser, RegisterUser,OTPVerify, ALLUser
from auth.auth_handler import signJWT
from core.Email_config import send_otp_email
from db.session import get_db
from api.v1.models.user.user_auth import OTP, User
import random
import re
import bcrypt
from sqlalchemy.exc import SQLAlchemyError
import pytz

router = APIRouter()

utc_now = pytz.utc.localize(datetime.utcnow())
ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

def generate_otp():
    return str(random.randint(1000, 9999))

def validate_email(email):
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_pattern, email)
    
def validate_password(password):
        return len(password) >= 8
    
def validate_phone_number(phone_number):
        phone_pattern = r"^\d{10}$"
        return re.match(phone_pattern, phone_number)

   
@router.post("auth/v1/pre-register/email_verify", response_model=None)
async def pre_register(email: str, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        if not validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        otp = generate_otp()
        now = datetime.utcnow()
        expiry = now + timedelta(minutes=5)

        otp_entry = OTP(
            email=email,
            purpose="register",  
            otp_code=otp,
            attempt_count=0,
            is_verified=False,
            generated_at=now,
            expired_at=expiry
        )

        db.add(otp_entry)
        db.commit()

        await send_otp_email(email, otp)

        return {"msg": "OTP sent to your email for verification"}
    
    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=404, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred please try again")

@router.post("/auth/v1/pre-register/verify-otp")
async def verify_otp(data:OTPVerify, db: Session = Depends(get_db)):
    try:
        otp_entry = db.query(OTP).filter(OTP.email == data.email).order_by(OTP.generated_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=404, detail="OTP not found")
        
        if otp_entry.purpose != "register":
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if otp_entry.expired_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP has expired")

        if otp_entry.otp_code != data.otp_code:
            otp_entry.attempt_count = (otp_entry.attempt_count or 0) + 1
            db.commit()
            raise HTTPException(status_code=400, detail="Invalid OTP")

        otp_entry.is_verified = True
        otp_entry.attempt_count = otp_entry.attempt_count or 0
        db.commit()

        return {"msg": "OTP verified and email is now verified. You can now proceed with registration."}

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=404, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred please try again")

   
@router.post("/auth/v1/register", response_model=None)
def register(user: RegisterUser, db: Session = Depends(get_db)):
    try:
        otp_entry = db.query(OTP).filter(OTP.email == user.user_email, OTP.is_verified == True).first()
        if not otp_entry:
            raise HTTPException(status_code=400, detail="Please verify your email before registration.")

        if user.user_password != user.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        if not validate_email(user.user_email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        if not validate_phone_number(user.phone):
            raise HTTPException(status_code=400, detail="Phone number must be 10 digits")

        if not validate_password(user.user_password):
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

        existing_user = db.query(User).filter(User.email == user.user_email).first()
        if existing_user and existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = bcrypt.hashpw(user.user_password.encode(), bcrypt.gensalt()).decode()

        new_user = User(
            username=user.user_name,
            email=user.user_email,
            phone_number=user.phone,
            password_hash=hashed_password,
            user_type=user.user_type,
            status=user.status,
            created_at=datetime.utcnow(),
            is_verified=True 
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {"message": "Registration successful","new_user": new_user.email,}

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=404, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred please try again")


@router.post("/auth/v1/login")
async def login(user: LoginUser, db: Session = Depends(get_db)):
    try:
        user_db = db.query(User).filter(User.email == user.email).first()
        if not user_db:
            raise HTTPException(status_code=404, detail="User does not exist. Please register.")

        if not bcrypt.checkpw(user.password.encode('utf-8'), user_db.password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Passwords do not match")

        otp = generate_otp()
        now = datetime.utcnow()
        expiry = now + timedelta(minutes=5)

        otp_entry = OTP(
            email=user.email,
            purpose="login",  
            otp_code=otp,
            attempt_count=0,
            is_verified=False,
            generated_at=now,
            expired_at=expiry
        )

        db.add(otp_entry)
        db.commit()

        await send_otp_email(user.email, otp)

        return {"message":"otp send successfully"}
    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=404, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred please try again")


@router.post("/auth/v1/verify_login_otp", status_code=status.HTTP_200_OK)
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    try:
        user_db = db.query(User).filter(User.email == data.email).first()
        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        otp_entry = db.query(OTP).filter(
            OTP.email == user_db.email,
            OTP.is_verified == False
        ).order_by(OTP.generated_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=404, detail="No active OTP found")

        if otp_entry.purpose != "login":
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if datetime.utcnow() > otp_entry.expired_at:
            otp_entry.otp_code = None
            db.commit()
            raise HTTPException(status_code=400, detail="OTP has expired")

        if otp_entry.otp_code != data.otp_code:
            otp_entry.attempt_count = (otp_entry.attempt_count or 0) + 1
            db.commit()

            if otp_entry.attempt_count >= 3:
                raise HTTPException(status_code=400, detail="Too many failed attempts. OTP locked.")
            raise HTTPException(status_code=400, detail="Invalid OTP")


        otp_entry.is_verified = True
        db.commit()

        token, exp = signJWT(user_db.user_id, user_db.user_type)

        return {
            "msg": "OTP verified successfully, login successful",
            "username": user_db.username,
            "email": user_db.email,
            "phone_number": user_db.phone_number,
            "user_type": user_db.user_type,
            "is_verified": user_db.is_verified,
            "token": token,
            "expires_at": exp,
            "created_at": user_db.created_at,    
            
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error occurred. Please try again.")
    
    
@router.get("/v1/get_all_users", response_model=List[ALLUser])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users  


# @router.get("/v1/auth/resend-otp/{email}")
# async def resend_otp(email: str, db: Session = Depends(get_db)):
#     try:
#         user = db.query(User).filter(User.email == email).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         db.query(OTP).filter(OTP.email == user.email, OTP.is_verified == False).update({OTP.otp_code: None})
#         db.commit()

#         otp_code = generate_otp()
#         now = datetime.utcnow()

#         db.add(OTP(
#             user_id=user.user_id,
#             otp_code=otp_code,
#             attempt_count=0,
#             is_verified=False,
#             generated_at=now,
#             expired_at=now + timedelta(minutes=5)
#         ))
#         db.commit()

#         await send_otp_email(email, otp_code)

#         return {"msg": "OTP resent successfully"}

#     except HTTPException as e:
#         raise e
#     except SQLAlchemyError:
#         db.rollback()
#         raise HTTPException(status_code=404, detail="Database error occurred.")
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Unexpected error occurred please try again")
