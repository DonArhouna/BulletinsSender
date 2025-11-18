from typing import List, Optional, Union
import os
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()


class Settings(BaseSettings):
    """
    Configuration centrale de l'application SendBulletin
    (Chargée automatiquement depuis les variables d'environnement)
    """

    # =========================
    # API
    # =========================
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 jours

    # =========================
    # Serveur
    # =========================
    SERVER_NAME: str = "SendBulletin"
    SERVER_HOST: AnyHttpUrl = "http://localhost"
    PROJECT_NAME: str = "SendBulletin API"

    # =========================
    # CORS
    # =========================
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:8082",
        "http://localhost:8080",  # Ajout sans slash
        "http://localhost:3000",  # Additional React dev server
        "http://localhost:5173",  # Additional Vite dev server
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]):
        """Permet d'accepter la variable sous forme de string dans le .env"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # =========================
    # Base de données
    # =========================
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "sqlite:///./sendbulletin.db"
    )

    # =========================
    # Email
    # =========================
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "smtp")  # smtp | mailjet

    # SMTP (héritage / fallback)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = int(os.getenv("SMTP_PORT", "587"))
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", None)
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", None)

    # Expéditeur par défaut
    EMAILS_FROM_EMAIL: Optional[str] = os.getenv("EMAILS_FROM_EMAIL", None)
    EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME", "SendBulletin Mailer")

    # Mailjet
    MAILJET_API_KEY: Optional[str] = os.getenv("MAILJET_API_KEY")
    MAILJET_API_SECRET: Optional[str] = os.getenv("MAILJET_API_SECRET")
    MAILJET_SENDER_EMAIL: Optional[str] = os.getenv("MAILJET_SENDER_EMAIL")
    MAILJET_SENDER_NAME: Optional[str] = os.getenv("MAILJET_SENDER_NAME", "SendBulletin Mailer")

    # =========================
    # Multi-tenancy (optionnel)
    # =========================
    MULTI_TENANT: bool = True

    class Config:
        case_sensitive = True


# Instance unique des settings
settings = Settings()
