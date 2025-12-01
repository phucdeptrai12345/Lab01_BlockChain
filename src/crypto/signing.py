from .keys import load_private_key, load_public_key


def sign_message(priv_bytes: bytes, message: bytes) -> bytes:
    # Ký message bằng private key bytes (Ed25519).
    private_key = load_private_key(priv_bytes)
    return private_key.sign(message)


def verify_signature(pub_bytes: bytes, message: bytes, signature: bytes) -> bool:
    #Kiểm tra chữ ký
    public_key = load_public_key(pub_bytes)
    try:
        public_key.verify(signature, message)
        return True
    except Exception:
        return False
