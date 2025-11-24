from src.crypto.keys import generate_keypair
from src.crypto.signing import sign_message, verify_signature


def main():
    priv, pub = generate_keypair()
    msg = b"hello blockchain"
    sig = sign_message(priv, msg)

    print("Signature OK:", verify_signature(pub, msg, sig))
    print("Signature FAIL:", verify_signature(pub, b"wrong", sig))


if __name__ == "__main__":
    main()
