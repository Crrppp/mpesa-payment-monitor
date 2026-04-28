import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

    # PostgreSQL (Aiven)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "avnadmin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "defaultdb")

    # Encryption
    FERNET_KEY = os.getenv("FERNET_KEY", "").encode()

    # Daraja
    CONSUMER_KEY = os.getenv("CONSUMER_KEY", "")
    CONSUMER_SECRET = os.getenv("CONSUMER_SECRET", "")
    PASSKEY = os.getenv("PASSKEY", "")
    BUSINESS_SHORTCODE = os.getenv("BUSINESS_SHORTCODE", "174379")