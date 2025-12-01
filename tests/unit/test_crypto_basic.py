from src.crypto.keys import generate_keypair
from src.crypto.signing import sign_message, verify_signature
from src.encoding.codec import (
    encode_tx_for_signing,
    encode_header_for_signing,
    encode_vote_for_signing,
)
import json

CHAIN_ID = "test-chain"


def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def test_raw_sign_and_verify():
    print_header("TEST 1 — RAW SIGN / VERIFY")
    priv, pub = generate_keypair()
    msg = b"hello blockchain"
    print("Message:", msg)

    sig = sign_message(priv, msg)
    print("Signature (hex):", sig.hex())

    ok_true = verify_signature(pub, msg, sig)
    ok_false = verify_signature(pub, b"wrong", sig)

    print("Verify with correct msg:", ok_true)
    print("Verify with wrong msg:", ok_false)

    assert ok_true is True
    assert ok_false is False


def test_wrong_public_key_fails():
    print_header("TEST 2 — WRONG PUBLIC KEY MUST FAIL")
    priv1, pub1 = generate_keypair()
    priv2, pub2 = generate_keypair()

    msg = b"test-ctx"
    sig = sign_message(priv1, msg)

    print("Message:", msg)
    print("Signature (signed by priv1):", sig.hex())

    ok_right = verify_signature(pub1, msg, sig)
    ok_wrong = verify_signature(pub2, msg, sig)

    print("Verify with pub1 (correct):", ok_right)
    print("Verify with pub2 (wrong):", ok_wrong)

    assert ok_right is True
    assert ok_wrong is False


def test_domain_separation_tx_header_vote():
    print_header("TEST 3 — DOMAIN SEPARATION FOR TX / HEADER / VOTE")
    priv, pub = generate_keypair()

    tx = {
        "sender": "Alice",
        "key": "Alice/msg",
        "value": "hello",
        "nonce": 1,
    }
    print("TX object:")
    print(json.dumps(tx, indent=4))

    tx_bytes = encode_tx_for_signing(tx, CHAIN_ID)
    header = {
        "height": 1,
        "parent_hash": "0" * 64,
        "state_hash": "1" * 64,
        "proposer": "Alice",
    }
    header_bytes = encode_header_for_signing(header, CHAIN_ID)
    vote_bytes = encode_vote_for_signing(
        validator_id="Alice",
        height=1,
        block_hash="X" * 64,
        phase="prevote",
        chain_id=CHAIN_ID,
    )

    print("TX bytes (for signing):", tx_bytes)
    print("HEADER bytes (for signing):", header_bytes)
    print("VOTE bytes (for signing):", vote_bytes)

    sig = sign_message(priv, tx_bytes)
    print("Signature (over TX context):", sig.hex())

    ok_tx = verify_signature(pub, tx_bytes, sig)
    ok_header = verify_signature(pub, header_bytes, sig)
    ok_vote = verify_signature(pub, vote_bytes, sig)

    print("Verify sig on TX bytes:", ok_tx)
    print("Verify sig on HEADER bytes:", ok_header)
    print("Verify sig on VOTE bytes:", ok_vote)

    assert ok_tx is True
    assert ok_header is False
    assert ok_vote is False


def main():
    print("\n" + "#" * 80)
    print("RUNNING CRYPTO TEST SUITE WITH DETAILED OUTPUT")
    print("#" * 80)

    test_raw_sign_and_verify()
    test_wrong_public_key_fails()
    test_domain_separation_tx_header_vote()

    print("\n" + "#" * 80)
    print("test_crypto_basic: ALL TESTS PASSED SUCCESSFULLY")
    print("#" * 80)


if __name__ == "__main__":
    main()
