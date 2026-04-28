import hashlib
import bcrypt
from cryptography.fernet import Fernet
from config import Config

cipher = Fernet(Config.FERNET_KEY)


def encrypt_phone(phone: str) -> str:
    return cipher.encrypt(phone.encode()).decode()


def decrypt_phone(encrypted: str) -> str:
    return cipher.decrypt(encrypted.encode()).decode()


def hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def mask_phone(phone: str) -> str:
    if len(phone) >= 10:
        return phone[:4] + "****" + phone[-3:]
    return "****"