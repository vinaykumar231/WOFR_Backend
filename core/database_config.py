import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from functools import lru_cache

load_dotenv()

class Settings(BaseSettings):

    DEV_DATABASE_URL: str = os.getenv("DEV_DATABASE_URL")
    PROD_DATABASE_URL: str = os.getenv("PROD_DATABASE_URL")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    class Config:
        env_file = ".env"
        case_sensitive = True


class DevelopmentSettings(Settings):
    DEBUG: bool = True

    @property
    def DATABASE_URL(self) -> str:
        return self.DEV_DATABASE_URL


class ProductionSettings(Settings):
    DEBUG: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return self.PROD_DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "dev")
    if environment.lower() == "prod":
        return ProductionSettings()
    return DevelopmentSettings()
