from datetime import datetime
import re
import uuid
from typing import Optional, Dict, Any, Union, List
import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import Session
from api.v1.models.tenants.tenant import Tenant
from api.v1.models.tenants.tenant_user import TenantUser
from api.v1.models.user.user_auth import User
from core.config import read_config

load_dotenv()
config = read_config()

# ------------------------------------------------- validate username -------------------------------------------------

USERNAME_MIN_LEN = int(config.get("USERNAME_MIN_LEN", 3))
USERNAME_MAX_LEN = int(config.get("USERNAME_MAX_LEN", 30))  

def validate_username(username: str) -> Dict[str, Any]:
    if not username:
        return {"valid": False, "message": "Username cannot be empty"}
    
    if len(username) < USERNAME_MIN_LEN:
        return {"valid": False, "message":f"Username must be at least {USERNAME_MIN_LEN} characters long."}
    
    if len(username) > USERNAME_MAX_LEN:
        return {"valid": False, "message": f"Username cannot exceed {USERNAME_MAX_LEN} characters."}
    
    if not re.match(r'^[a-zA-Z]+$', username):
        return {"valid": False, "message": "Username must contain only alphabets."}
    
    return {"valid": True, "message": "Username is valid"}


#------------------------------------------------- validate email -------------------------------------------------

def validate_email(email: str) -> Dict[str, Any]:
    if not email:
        return {"valid": False, "message": "Email cannot be empty"}
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|org|net)$'
    if not re.match(pattern, email):
        return {"valid": False, "message": "Invalid email format"}
    
    return {"valid": True, "message": "Email is valid"}

#------------------------------------------------- validate phone number -------------------------------------------------

def validate_phone_number(phone: str) -> Dict[str, Any]:
    if not phone:
        return {"valid": False, "message": "Phone number cannot be empty"}

    if not phone.startswith('+'):
        return {
            "valid": False,
            "message": "Country code is missing. Please include it (e.g., +91 for India)"
        }

    pattern = r'^\+[1-9]\d{1,14}$'
    if not re.match(pattern, phone):
        return {
            "valid": False,
            "message": "Invalid phone number."
        }

    return {"valid": True, "message": "Phone number is valid"}

#------------------------------------------------- validate password strength -----------------------------------------

def validate_password_strength(password: str) -> Dict[str, Any]:
    if not password or len(password) < 8:
        return {"valid": False, "message": "Password must be at least 8 characters long"}
    
    if len(password) > 12:
        return {"valid": False, "message": "Password must not exceed 12 characters"}
    
    checks = {
        "has_upper": bool(re.search(r'[A-Z]', password)),
        "has_lower": bool(re.search(r'[a-z]', password)),
        "has_digit": bool(re.search(r'\d', password)),
        "has_special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    }
    
    if not all(checks.values()):
        missing = []
        if not checks["has_upper"]:
            missing.append("uppercase letter")
        if not checks["has_lower"]:
            missing.append("lowercase letter")
        if not checks["has_digit"]:
            missing.append("digit")
        if not checks["has_special"]:
            missing.append("special character")
        
        return {
            "valid": False,
            "message": f"Password must include at least one {', '.join(missing)}"
        }
    
    return {"valid": True, "message": "Password is strong."}
 
#------------------------------------------------- user_id format ------------------------------------------------

def generate_next_user_id(db: Session) -> str:
    last_user = db.query(User).order_by(User.user_id.desc()).first()
    next_id = int(last_user.user_id) + 1 if last_user else 1
    return str(next_id).zfill(5)

#------------------------------------------------- Tenant_id format -------------------------------------------------

def generate_next_tenant_id(db: Session) -> str:
    last_tenant = db.query(Tenant).order_by(Tenant.tenant_id.desc()).first()
    if last_tenant and last_tenant.tenant_id.startswith("T"):
        last_num = int(last_tenant.tenant_id[1:])  
    else:
        last_num = 0
    next_id = last_num + 1
    return f"T{str(next_id).zfill(5)}"  

#------------------------------------------------- Tenant_user_id format -------------------------------------------------

def generate_next_tenant_user_id(db: Session) -> str:
    last_user = (
        db.query(TenantUser)
        .filter(TenantUser.tenant_user_id.like("EMP%"))
        .order_by(TenantUser.tenant_user_id.desc())
        .first()
    )
    if not last_user:
        return "EMP0001"
    last_id = int(last_user.tenant_user_id.replace("EMP", ""))
    return f"EMP{last_id + 1:04d}"


#------------------------------------------------- validate date format -------------------------------------------------

def validate_date_format(date_str: str, format_str: str = "%d-%m-%y") -> Dict[str, Any]:
    try:
        datetime.strptime(date_str, format_str)
        return {"valid": True, "message": "Date format is valid"}
    except (ValueError, TypeError):
        return {"valid": False, "message": "Invalid date format. Please use the format dd-mm-yy"}



