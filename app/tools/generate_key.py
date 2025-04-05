from cryptography.fernet import Fernet

# Генерация нового ключа
key = Fernet.generate_key()

# Вывод ключа в консоль
print("Generated encryption key:", key.decode())