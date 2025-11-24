from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def generate_keypair():
    """
    Tạo 1 cặp (private_key_bytes, public_key_bytes) dùng Ed25519.
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv_bytes, pub_bytes


def load_private_key(priv_bytes: bytes):
    return ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)


def load_public_key(pub_bytes: bytes):
    return ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
