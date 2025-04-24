import pytz
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import bcrypt
from pydantic import EmailStr, BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone


load_dotenv()


######################################################################################################################
                # For sending Email
#######################################################################################################################

async def send_email(subject, email_to, body):
    # Set up the SMTP server
    smtp_server = os.getenv("smtp_server_name")
    smtp_port = os.getenv("smtp_port_name")
    smtp_username = os.getenv("smtp_username_name")  
    smtp_password = os.getenv("smtp_password_name") 
    try:
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  
        server.login(smtp_username, smtp_password)  
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email_to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server.sendmail(smtp_username, email_to, msg.as_string())
        server.quit()

    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

############################################################################################################

async def send_otp_email(user_email: str, otp_code: str, purpose:str):

    utc_now = datetime.now(timezone.utc)  
    expiry_time_utc = utc_now + timedelta(minutes=5)
    formatted_expiry = expiry_time_utc.strftime('%d %b %Y')

    body = f"""
    <h3>OTP Verification for {purpose} process</h3>
    <p>Your One-Time Password (OTP):</p>
    <h2 style="color: #2e6c80;">{otp_code}</h2>
    <p>This OTP is valid for only 5 minutes (<b>{formatted_expiry}</b>) .</p>
    <p style="color: #cc0000;"><strong>Do not share this OTP with anyone.</strong> It is confidential and only intended for you.</p>
    
    """

    try:
        await send_email(
            subject=f"Your OTP Code for {purpose}",
            email_to=user_email,
            body=body
        )
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP. Please try again later.")
