import os
from pydantic_settings import BaseSettings
from pydantic import computed_field
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Settings(BaseSettings):
    # Base config
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "t")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "File Management System")
    VERSION: str = "1.0.0"
    DOMAIN: str = "http://localhost:8000"
    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRY: int = int(os.getenv("ACCESS_TOKEN_EXPIRY", 172800))
    REFRESH_TOKEN_EXPIRY: int = int(os.getenv("REFRESH_TOKEN_EXPIRY", 604800))

    # Email
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "your-brevo-api-key")
    SENDER_NAME: str = os.getenv("SENDER_NAME", "File Management System")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "your-resend-api-key")

    # AWS
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "your-bucket-name")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "your-access-key-id")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "your-secret-access-key")

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
    GOOGLE_REDIRECT_URL: str = "http://localhost:8000/api/v1/auth/callback/google"

    FIREBASE_TYPE: str = os.getenv("FIREBASE_TYPE", "service_account")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "your-project-id")
    FIREBASE_PRIVATE_KEY_ID: str = os.getenv("FIREBASE_PRIVATE_KEY_ID", "your-private-key-id")
    FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "your-private-key").replace('\\n', '\n')
    FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "your-client-email")
    FIREBASE_CLIENT_ID: str = os.getenv("FIREBASE_CLIENT_ID", "your-client-id")
    FIREBASE_AUTH_URI: str = os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    FIREBASE_TOKEN_URI: str = os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token")
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: str = os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs")
    FIREBASE_CLIENT_X509_CERT_URL: str = os.getenv("FIREBASE_CLIENT_X509_CERT_URL", "your-client-cert-url")
    FIREBASE_UNIVERSE_DOMAIN: str = os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com")

    @computed_field
    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.REDIS_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
