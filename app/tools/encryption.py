from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из .env
load_dotenv()

# Получение ключа из переменной окружения
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY").encode()

def encrypt_data(data: str) -> str:
    fernet = Fernet(ENCRYPTION_KEY)
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()

def decrypt_data(encrypted_data: str) -> str:
    fernet = Fernet(ENCRYPTION_KEY)
    decrypted = fernet.decrypt(encrypted_data.encode())
    return decrypted.decode()