from dotenv import load_dotenv
from core.phone_config import send_otp_sms
from utils.validators import generate_next_user_id, validate_email, validate_password_strength, validate_phone_number, validate_username
from datetime import datetime, time, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from api.v1.schemas import LoginUser, RegisterUser,OTPVerify, ALLUser, UpdateUser,ForgotPassword,OTPVerifyPreRegister
from auth.auth_handler import signJWT
from core.Email_config import send_email, send_otp_email
from db.session import get_db
from api.v1.models.user.user_auth import OTP, User
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
import random
import re
import os
import bcrypt
import pytz
import phonenumbers


router = APIRouter()
load_dotenv()

utc_now = pytz.utc.localize(datetime.utcnow())
ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

def generate_otp():
    return str(random.randint(1000, 9999))

   
@router.post("/auth/v1/pre-register/email-verification", status_code=status.HTTP_200_OK)
async def pre_register(email: str, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,  detail="Email already registered")

        email_validation = validate_email(email)
        if not email_validation["valid"]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=email_validation["message"])

        otp = generate_otp()
        now = datetime.utcnow()
        expiry = now + timedelta(minutes=5)

        otp_entry = db.query(OTP).filter(and_(
                OTP.email == email,
                OTP.purpose == "register",
                OTP.status == "active",
                OTP.is_verified == False
            )
        ).order_by(OTP.generated_at.desc()).first()

        if otp_entry:
            otp_entry.otp_code = otp
            otp_entry.generated_at = now
            otp_entry.expired_at = expiry
            otp_entry.attempt_count = 0
        else:
            otp_entry = OTP(
                email=email,
                purpose="register",  
                otp_code=otp,
                attempt_count=0,
                is_verified=False,
                generated_at=now,
                expired_at=expiry,
                status="active"
            )
            db.add(otp_entry)

        db.commit()

        await send_otp_email(email, otp)

        return {"msg": "OTP sent to your email for verification"}
    
    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred, please try again.")

@router.post("/auth/v1/pre-register/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(data:OTPVerifyPreRegister, db: Session = Depends(get_db)):
    try:
        email_validation = validate_email(data.email)
        if not email_validation["valid"]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=email_validation["message"])
        
        otp_entry = db.query(OTP).filter(OTP.email == data.email).order_by(OTP.generated_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email does not exits")
        
        if otp_entry.purpose != "register":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

        if otp_entry.expired_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="OTP has expired")
        
        max_attempts = int(os.getenv("PRE_REGISTER_MAX_OTP_ATTEMPT_COUNT", 3))
        if (otp_entry.attempt_count or 0) >= max_attempts:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="You have attempted OTP verification too many times. Please try again later.")

        if otp_entry.otp_code != data.otp_code:
            otp_entry.attempt_count = (otp_entry.attempt_count or 0) + 1
            db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

        otp_entry.is_verified = True
        otp_entry.attempt_count = otp_entry.attempt_count or 0
        db.commit()

        return {"msg": "OTP verified and email is now verified. You can now proceed with registration."}

    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error occurred please try again")

   
@router.post("/auth/v1/register", response_model=None)
def register(user: RegisterUser, db: Session = Depends(get_db)):
    try:
        otp_entry = db.query(OTP).filter(OTP.email == user.user_email, OTP.is_verified == True).first()
        if not otp_entry:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email before registration.")
        
        username_validation = validate_username(user.user_name)
        if not username_validation["valid"]:
            raise HTTPException(status_code=400, detail=username_validation["message"])

        email_validation = validate_email(user.user_email)
        if not email_validation["valid"]:
            raise HTTPException(status_code=400, detail=email_validation["message"])

        phone_validation = validate_phone_number(user.phone)
        if not phone_validation["valid"]:
            raise HTTPException(status_code=400, detail=phone_validation["message"])

        password_validation = validate_password_strength(user.user_password)
        if not password_validation["valid"]:
            raise HTTPException(status_code=400, detail=password_validation["message"])
        
        if user.user_password != user.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        existing_user = db.query(User).filter(User.email == user.user_email).first()
        if existing_user and existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        user_id=generate_next_user_id(db=db)

        hashed_password = bcrypt.hashpw(user.user_password.encode(), bcrypt.gensalt()).decode()

        new_user = User(
            user_id=user_id,
            username=user.user_name,
            email=user.user_email,
            phone_number=user.phone,
            organization_name=user.organization_name,
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
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=f"Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred please try again")


@router.post("/auth/v1/login")
async def login(user: LoginUser, db: Session = Depends(get_db)):
    try:
        login_input = user.email_or_phone

        if validate_email(login_input)["valid"]:
            user_db = db.query(User).filter(User.email == login_input).first()
            email_or_phone = "email"
            otp_entry_data = {
                "email": login_input,
                "phone_number": None
            }
        elif validate_phone_number(login_input)["valid"]:
            user_db = db.query(User).filter(User.phone_number == login_input).first()
            email_or_phone = "phone"
            otp_entry_data = {
                "email": None,
                "phone_number": login_input
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid email or phone format.")

        if not user_db:
            raise HTTPException(status_code=404, detail="User does not exist. Please register.")

        if not bcrypt.checkpw(user.password.encode('utf-8'), user_db.password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid Passwords")

        otp = generate_otp()
        now = datetime.utcnow()
        expiry = now + timedelta(minutes=5)

        existing_otp = db.query(OTP).filter(
            OTP.purpose == "login",
            OTP.is_verified == False,
            (
                (OTP.email == otp_entry_data["email"]) |
                (OTP.phone_number == otp_entry_data["phone_number"])
            ),
            OTP.status == "active"
        ).order_by(OTP.generated_at.desc()).first()

        if existing_otp:
            existing_otp.otp_code = otp
            existing_otp.generated_at = now
            existing_otp.expired_at = expiry
            existing_otp.attempt_count = 0
        else:
            new_otp = OTP(
                **otp_entry_data,
                purpose="login",
                otp_code=otp,
                attempt_count=0,
                is_verified=False,
                generated_at=now,
                expired_at=expiry,
                status="active"
            )
            db.add(new_otp)

        db.commit()

        if email_or_phone == "email":
            await send_otp_email(user_db.email, otp)
            return {"message": "OTP sent successfully to your email"}
        else:
            sms_sent = send_otp_sms(user_db.phone_number, otp)
            if sms_sent:
                return {"message": "OTP sent successfully to your phone"}
            else:
                raise HTTPException(status_code=500, detail="Failed to send OTP via SMS")

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred, please try again.")


@router.post("/auth/v1/verify_login_otp", status_code=status.HTTP_200_OK)
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    try:
        login_input = data.email_or_phone

        if validate_email(login_input)["valid"]:
            user_db = db.query(User).filter(User.email == login_input).first()
        else:
            try:
                parsed_phone = phonenumbers.parse(login_input, None)
                if phonenumbers.is_valid_number(parsed_phone):
                    user_db = db.query(User).filter(User.phone_number == login_input).first()
                else:
                    raise HTTPException(status_code=400, detail="Invalid phone number")
            except:
                raise HTTPException(status_code=400, detail="Invalid email or phone number")

        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        otp_entry = db.query(OTP).filter(
                or_(
                    OTP.email == user_db.email,
                    OTP.phone_number == user_db.phone_number
                ),
                OTP.is_verified == False
            ).order_by(OTP.generated_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=400, detail=f"Invalid OTP.")

        if otp_entry.status in ["used", "expired", "frozen"]:
            raise HTTPException(status_code=400, detail=f"OTP is {otp_entry.status}.")

        if otp_entry.purpose != "login":
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if datetime.utcnow() > otp_entry.expired_at:
            otp_entry.otp_code = None
            otp_entry.status = "expired"
            db.commit()
            raise HTTPException(status_code=400, detail="OTP has expired")
        
        max_attempts = int(os.getenv("LOGIN_MAX_OTP_ATTEMPT_COUNT", 3))
        if otp_entry.otp_code != data.otp_code:
            otp_entry.attempt_count = (otp_entry.attempt_count or 0) + 1
            if otp_entry.attempt_count >= max_attempts:
                otp_entry.status = "frozen"
            db.commit()

            if otp_entry.status == "frozen":
                raise HTTPException(status_code=400, detail="Too many failed attempts. Please try again.")
            raise HTTPException(status_code=400, detail="Invalid OTP")

        otp_entry.is_verified = True
        otp_entry.status = "used"
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
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred. Please try again.{e}")
    

@router.post("/auth/v1/forgot-password/send-link")
async def send_forgot_password_email(email: str, db: Session = Depends(get_db)):

    email_validation = validate_email(email)
    if not email_validation["valid"]:
            raise HTTPException(status_code=400, detail=email_validation["message"])
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with this email does not exist")

    reset_link = f"https://021b-2405-201-37-21d9-5198-9ec5-664-4a64.ngrok-free.app/api/auth/v1/forgot-password"

    email_body = f"""
    <h3>Password Reset Request</h3>
    <p>Click the link below to reset your password:</p>
    <p><a href="{reset_link}" target="_blank">Reset Password</a></p>
    """

    try:
        await send_email(
            subject="Reset Your Password",
            email_to=email,
            body=email_body
        )
        return {"message": "Password reset link sent to your email."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")
    

@router.post("/auth/v1/forgot-password", response_model=None)
async def reset_password(data: ForgotPassword, db: Session = Depends(get_db)):
    try:
        email_validation = validate_email(data.email)
        if not email_validation["valid"]:
            raise HTTPException(status_code=400, detail=email_validation["message"])
            
        user_db = db.query(User).filter(User.email == data.email).first()
        if not user_db:
            raise HTTPException(status_code=404, detail="User not found with this email")


        password_validation = validate_password_strength(data.new_password)
        if not password_validation["valid"]:
            raise HTTPException(status_code=400, detail=password_validation["message"])
            
        if data.new_password != data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        hashed_password = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
        user_db.password_hash = hashed_password
        
        db.commit()
        
        return {"message": "Password has been reset successfully. You can now login with your new password."}

    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error occurred: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred. Please try again: {e}")
    

@router.get("/v1/get_all_users", response_model=None)
def get_all_users(db: Session = Depends(get_db)):
    try:
        users = db.query(User).all()
        return [
            {
                "user_id": usr.user_id,
                "username": usr.username,
                "email": usr.email,
                "phone_number": usr.phone_number,
                "user_type": usr.user_type,
                "is_verified": usr.is_verified,
                "organization_name": usr.organization_name,
                "status": usr.status,
                "created_at": usr.created_at
            }
            for usr in users
        ]
    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred. Please try again. {e}")

# @router.put("/v1/update_user/{user_id}", response_model=None)
# def update_user(user_id: str, user: UpdateUser, db: Session = Depends(get_db)):
#     try:
#         db_user = db.query(User).filter(User.user_id == user_id).first()
        
#         if not db_user:
#             raise HTTPException(status_code=404, detail="User not found")

#         if user.user_name:
#             db_user.username = user.user_name
#         if user.user_email:
#             db_user.email = user.user_email
#         if user.phone:
#             db_user.phone_number = user.phone
#         if user.organization_name:
#             db_user.organization_name = user.organization_name
#         if user.user_password:
#             db_user.password_hash = bcrypt.hashpw(user.user_password.encode(), bcrypt.gensalt()).decode()
#         if user.status:
#             db_user.status = user.status
#         if user.user_type:
#             db_user.user_type = user.user_type

#         db.commit()
#         db.refresh(db_user)
        
#         return {"message": "user updated successfully","user":db_user }
#     except HTTPException as e:
#         raise e
#     except SQLAlchemyError:
#         db.rollback()
#         raise HTTPException(status_code=500, detail="Database error occurred.")
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Unexpected error occurred. Please try again. {e}")


# @router.delete("/v1/delete_user/{user_id}", response_model=None)
# def delete_user(user_id: str, db: Session = Depends(get_db)):
#     try:
#         db_user = db.query(User).filter(User.user_id == user_id).first()

#         if not db_user:
#             raise HTTPException(status_code=404, detail="User not found")

#         db.delete(db_user)
#         db.commit()

#         return  {"message": "user deleted successfully","user":db_user }
#     except HTTPException as e:
#         raise e
#     except SQLAlchemyError:
#         db.rollback()
#         raise HTTPException(status_code=500, detail="Database error occurred.")
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Unexpected error occurred. Please try again. {e}")
    



# @router.post("/auth/v1/pre-register/phone_verify", response_model=None)
# async def pre_register_phone(phone: str, db: Session = Depends(get_db)):
#     try:
#         # Check if phone number already exists
#         existing_user = db.query(User).filter(User.phone_number == phone).first()
#         if existing_user:
#             raise HTTPException(status_code=400, detail="Phone number already registered")

#         # Validate phone number (optional, implement this as needed)
#         phone_validation = validate_phone_number(phone)
#         if not phone_validation["valid"]:
#             raise HTTPException(status_code=400, detail=phone_validation["message"])

#         # Generate OTP
#         otp = generate_otp()
#         now = datetime.utcnow()
#         expiry = now + timedelta(minutes=5)

#         # Check for existing unverified OTP for this number
#         otp_entry = db.query(OTP).filter(and_(
#                 OTP.email == phone,   # In this case, 'email' field is reused to store the phone
#                 OTP.purpose == "register",
#                 OTP.status == "active",
#                 OTP.is_verified == False
#             )
#         ).order_by(OTP.generated_at.desc()).first()

#         if otp_entry:
#             otp_entry.otp_code = otp
#             otp_entry.generated_at = now
#             otp_entry.expired_at = expiry
#             otp_entry.attempt_count = 0
#         else:
#             otp_entry = OTP(
#                 email=phone,  # If you're storing phones in the same field
#                 purpose="register",
#                 otp_code=otp,
#                 attempt_count=0,
#                 is_verified=False,
#                 generated_at=now,
#                 expired_at=expiry,
#                 status="active"
#             )
#             db.add(otp_entry)

#         db.commit()

#         # Send OTP to phone number
#         await send_otp_sms(phone, otp)

#         return {"msg": "OTP sent to your phone for verification"}

#     except HTTPException as e:
#         raise e
#     except SQLAlchemyError:
#         db.rollback()
#         raise HTTPException(status_code=500, detail="Database error occurred.")
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Unexpected error occurred, please try again.")
