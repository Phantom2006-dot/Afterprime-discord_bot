from cryptography.fernet import Fernet
import config
import base64

def get_cipher():
    if not config.ENCRYPTION_KEY:
        key = Fernet.generate_key()
        print(f"Generated encryption key: {key.decode()}")
        print("Add this to your .env file as ENCRYPTION_KEY")
        return Fernet(key)
    
    key = config.ENCRYPTION_KEY.encode() if isinstance(config.ENCRYPTION_KEY, str) else config.ENCRYPTION_KEY
    return Fernet(key)

def encrypt_token(token: str) -> str:
    cipher = get_cipher()
    encrypted = cipher.encrypt(token.encode())
    return base64.b64encode(encrypted).decode()

def decrypt_token(encrypted_token: str) -> str:
    cipher = get_cipher()
    encrypted = base64.b64decode(encrypted_token.encode())
    decrypted = cipher.decrypt(encrypted)
    return decrypted.decode()
