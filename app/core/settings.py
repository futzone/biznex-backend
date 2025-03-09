from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API
    API_V1_STR: str
    BASE_URL: str
    DEBUG: bool = True

    TELEGRAM_BOT_TOKEN: str = "7050861257:AAHZPbtM0-Hfafj2wAKUuRoNOous7uJXgQI"
    TELEGRAM_CHANNEL_ID: str = "-1002415615522"
    FORM_TELEGRAM_BOT_TOKEN: str = "7656382602:AAF8EPLCEv7s7DEVHV5mlffJySRp6X0Hn1A"
    FORM_TELEGRAM_CHANNEL_ID: str = "-1002308430010"

    # PROJECT METADATA
    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str
    PROJECT_VERSION: str

    # POSTGRES CREDENTIALS
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DATABASE: str

    # JWT CONFIG
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # FIREBASE CREDENTIALS
    FIREBASE_TYPE: str
    FIREBASE_PROJECT_ID: str
    FIREBASE_PRIVATE_KEY_ID: str
    FIREBASE_PRIVATE_KEY: str
    FIREBASE_CLIENT_EMAIL: str
    FIREBASE_CLIENT_ID: str
    FIREBASE_AUTH_URI: str
    FIREBASE_TOKEN_URI: str
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: str
    FIREBASE_CLIENT_X509_CERT_URL: str
    FIREBASE_UNIVERSE_DOMAIN: str

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
