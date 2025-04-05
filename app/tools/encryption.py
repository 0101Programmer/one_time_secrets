from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os
from typing import Optional

# Загрузка переменных окружения из .env
load_dotenv()

# Получение ключа из переменной окружения
ENCRYPTION_KEY: bytes = os.getenv("ENCRYPTION_KEY").encode()


def encrypt_data(data: Optional[str]) -> Optional[str]:
    """
    Шифрует строку с использованием Fernet.

    Параметры:
        - data (Optional[str]): Данные для шифрования.

    Возвращает:
        - Optional[str]: Зашифрованные данные или None, если входные данные равны None.
    """
    if data is None:
        return None  # Если данные отсутствуют, возвращаем None

    fernet = Fernet(ENCRYPTION_KEY)
    encrypted = fernet.encrypt(data.encode())  # Шифруем данные
    return encrypted.decode()  # Возвращаем зашифрованные данные как строку


def decrypt_data(encrypted_data: Optional[str]) -> Optional[str]:
    """
    Дешифрует строку с использованием Fernet.

    Параметры:
        - encrypted_data (Optional[str]): Зашифрованные данные.

    Возвращает:
        - Optional[str]: Расшифрованные данные или None, если входные данные равны None.
    """
    if encrypted_data is None:
        return None  # Если данные отсутствуют, возвращаем None

    fernet = Fernet(ENCRYPTION_KEY)
    decrypted = fernet.decrypt(encrypted_data.encode())  # Дешифруем данные
    return decrypted.decode()  # Возвращаем расшифрованные данные как строку