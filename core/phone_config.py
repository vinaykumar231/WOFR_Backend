import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()  

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

def send_otp_sms(phone_number: str, otp: str):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=f"Your WOFR login OTP is {otp}. It is valid for 5 mins. Do not share this code with anyone."
        )
        return True
    except Exception as e:
        print(f"SMS Error: {e}")
        return False



# for get trail number
# client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# # Step 1: List available numbers
# available_numbers = client.available_phone_numbers("US").local.list(sms_enabled=True, limit=1)

# if available_numbers:
#     number = available_numbers[0].phone_number
#     print("Buying trial number:", number)

#     # Step 2: Buy the number (register to your account)
#     purchased_number = client.incoming_phone_numbers.create(phone_number=number)
#     print(f"Purchased trial number: {purchased_number.phone_number}")
# else:
#     print("No numbers available.")

