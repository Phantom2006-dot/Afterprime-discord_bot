from cryptography.fernet import Fernet
import config
import base64
import os

def get_cipher():
    """
    Returns a Fernet cipher object using the ENCRYPTION_KEY from config.
    """
    # Debug: Check if key is loaded
    raw_key = getattr(config, "ENCRYPTION_KEY", None)
    
    if not raw_key:
        # Generate a new key if none exists
        key = Fernet.generate_key()
        print(f"❌ No ENCRYPTION_KEY found in config!")
        print(f"✅ Generated new encryption key: {key.decode()}")
        print("📝 Add this to your .env file as ENCRYPTION_KEY (without quotes)")
        return Fernet(key)

    # Clean the key: remove spaces, newlines, quotes
    raw_key = raw_key.strip().strip('"').strip("'")
    
    # Debug output
    print(f"🔑 Raw ENCRYPTION_KEY: '{raw_key}'")
    print(f"📏 Key length: {len(raw_key)}")
    
    # Ensure key is bytes
    if isinstance(raw_key, str):
        key_bytes = raw_key.encode('utf-8')
    else:
        key_bytes = raw_key

    # Validate and create Fernet instance
    try:
        # Fernet will validate the key format
        cipher = Fernet(key_bytes)
        
        # Test the key with a simple encryption/decryption
        test_data = b"test"
        encrypted = cipher.encrypt(test_data)
        decrypted = cipher.decrypt(encrypted)
        
        if decrypted == test_data:
            print("✅ Fernet key validation PASSED")
            return cipher
        else:
            raise ValueError("Fernet key test encryption/decryption failed")
            
    except Exception as e:
        print(f"❌ Fernet key validation FAILED: {e}")
        
        # Try to generate a valid key from the existing one
        try:
            # If the key is close but not quite right, try padding
            if len(key_bytes) < 32:
                # Pad with = to make 32 bytes when decoded
                key_bytes += b'=' * (32 - len(key_bytes))
            elif len(key_bytes) > 32:
                # Truncate to 32 bytes
                key_bytes = key_bytes[:32]
                
            # Ensure it's URL-safe base64
            decoded = base64.urlsafe_b64decode(key_bytes + b'=' * (4 - len(key_bytes) % 4))
            if len(decoded) == 32:
                new_key = base64.urlsafe_b64encode(decoded)
                print(f"🔄 Attempting auto-fixed key: {new_key.decode()}")
                return Fernet(new_key)
        except Exception as fix_error:
            print(f"❌ Auto-fix failed: {fix_error}")
        
        # Generate a new key as fallback
        new_key = Fernet.generate_key()
        print(f"🆕 Generated replacement key: {new_key.decode()}")
        print("💡 Update your .env file with this new ENCRYPTION_KEY")
        return Fernet(new_key)


def encrypt_token(token: str) -> str:
    """
    Encrypts a token string and returns a URL-safe base64-encoded string.
    """
    try:
        cipher = get_cipher()
        encrypted = cipher.encrypt(token.encode('utf-8'))
        # Use URL-safe base64 encoding for storage
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        raise


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypts a URL-safe base64-encoded encrypted token string.
    """
    try:
        cipher = get_cipher()
        # Use URL-safe base64 decoding
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode('utf-8'))
        decrypted = cipher.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"❌ Decryption error: {e}")
        raise


def test_encryption():
    """Test the encryption/decryption cycle"""
    try:
        test_token = "test_linkedin_access_token_123"
        print("🧪 Testing encryption system...")
        print(f"📤 Original token: {test_token}")
        
        encrypted = encrypt_token(test_token)
        print(f"🔒 Encrypted: {encrypted}")
        
        decrypted = decrypt_token(encrypted)
        print(f"🔓 Decrypted: {decrypted}")
        
        if test_token == decrypted:
            print("✅ Encryption test PASSED - System is working!")
            return True
        else:
            print("❌ Encryption test FAILED - Tokens don't match!")
            return False
    except Exception as e:
        print(f"💥 Encryption test ERROR: {e}")
        return False


# Generate a valid Fernet key if run directly
if __name__ == "__main__":
    print("🔐 Social Army Encryption Module")
    print("=" * 50)
    
    # Test current setup
    test_encryption()
    
    # Offer to generate a new key
    print("\n" + "=" * 50)
    generate_new = input("Generate a new Fernet key? (y/n): ")
    if generate_new.lower() == 'y':
        new_key = Fernet.generate_key()
        print(f"\n🎉 Your new ENCRYPTION_KEY:")
        print(f"ENCRYPTION_KEY={new_key.decode()}")
        print(f"\n💡 Copy this to your .env file and restart the server.")
