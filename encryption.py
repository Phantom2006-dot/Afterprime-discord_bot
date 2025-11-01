from cryptography.fernet import Fernet
import config
import base64

def get_cipher():
    """
    Returns a Fernet cipher object using the ENCRYPTION_KEY from config.
    If no key is set, generates a new one and prints it for adding to .env.
    """
    # If no key is set, generate a new one
    if not getattr(config, "ENCRYPTION_KEY", None):
        key = Fernet.generate_key()
        print(f"Generated encryption key: {key.decode()}")
        print("Add this to your .env file as ENCRYPTION_KEY (without quotes)")
        return Fernet(key)

    # Clean the key: remove spaces/newlines
    raw_key = config.ENCRYPTION_KEY.strip()
    
    # Ensure key is bytes
    key_bytes = raw_key.encode() if isinstance(raw_key, str) else raw_key

    # Validate that the key decodes to exactly 32 bytes
    try:
        decoded = base64.urlsafe_b64decode(key_bytes)
        if len(decoded) != 32:
            raise ValueError
    except Exception:
        raise ValueError("ENCRYPTION_KEY is invalid. Must be 32 url-safe base64-encoded bytes.")

    return Fernet(key_bytes)


def encrypt_token(token: str) -> str:
    """
    Encrypts a token string and returns a base64-encoded string.
    """
    cipher = get_cipher()
    encrypted = cipher.encrypt(token.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypts a base64-encoded encrypted token string.
    """
    cipher = get_cipher()
    encrypted_bytes = base64.b64decode(encrypted_token.encode())
    decrypted = cipher.decrypt(encrypted_bytes)
    return decrypted.decode()


# Example usage
if __name__ == "__main__":
    test_token = "linkedin_access_token_example"
    encrypted = encrypt_token(test_token)
    print("Encrypted:", encrypted)

    decrypted = decrypt_token(encrypted)
    print("Decrypted:", decrypted)
