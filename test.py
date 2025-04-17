from core.config import get_settings

settings = get_settings()

print(settings.SECRET)      
print(settings.ENVIRONMENT)      
print(settings.DEV_DATABASE_URL) 
