from src.crypto.keys import generate_keypair
from src.simulator.block import (
    BlockHeader,
    Block,
    compute_block_hash,
    sign_block_header,
    verify_block_header,
    validate_block,
)
import json

CHAIN_ID = "test-chain"


def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def make_block(height, parent_hash, state_hash, priv):
    header = BlockHeader(
        height=height,
        parent_hash=parent_hash,
        state_hash=state_hash,
        proposer="validator-1",
        signature="",
    )
    block = Block(header=header, transactions=[])
    sign_block_header(header, CHAIN_ID, priv)
    return block


def test_block_header_signature_ok():
    print_header("TEST 1 — VERIFY CORRECT BLOCK SIGNATURE")
    priv, pub = generate_keypair()
    block = make_block(1, "0" * 64, "1" * 64, priv)

    print("Block Header:")
    print(json.dumps(block.header.__dict__, indent=4))

    ok = verify_block_header(block.header, CHAIN_ID, pub)
    print(f"Signature verification result: {ok}")
    assert ok is True


def test_block_header_tamper_after_sign_fails():
    print_header("TEST 2 — TAMPERED BLOCK MUST FAIL SIGNATURE CHECK")
    priv, pub = generate_keypair()
    block = make_block(1, "0" * 64, "1" * 64, priv)

    print("Original state_hash:", block.header.state_hash)
    block.header.state_hash = "9" * 64
    print("Tampered state_hash:", block.header.state_hash)

    ok = verify_block_header(block.header, CHAIN_ID, pub)
    print(f"Signature verification result after tampering: {ok}")
    assert ok is False


def test_validate_block_height_and_parent():
    print_header("TEST 3 — VALIDATE BLOCK HEIGHT AND PARENT HASH")
    priv, pub = generate_keypair()
    block = make_block(1, "0" * 64, "1" * 64, priv)

    print("Expecting: height=1, parent=0*64 → VALID")
    assert validate_block(block, expected_height=1, expected_parent_hash="0" * 64)

    print("Expecting: wrong height → INVALID")
    assert not validate_block(block, expected_height=2, expected_parent_hash="0" * 64)

    print("Expecting: wrong parent_hash → INVALID")
    assert not validate_block(block, expected_height=1, expected_parent_hash="x" * 64)


def test_block_hash_deterministic():
    print_header("TEST 4 — DETERMINISTIC BLOCK HASH CHECK")
    priv, pub = generate_keypair()

    b1 = make_block(1, "0" * 64, "1" * 64, priv)
    b2 = make_block(1, "0" * 64, "1" * 64, priv)

    h1 = compute_block_hash(b1.header)
    h2 = compute_block_hash(b2.header)

    print(f"Hash 1: {h1}")
    print(f"Hash 2: {h2}")
    print("Hashes match?" , h1 == h2)

    assert h1 == h2


def main():
    print("\n" + "#" * 80)
    print("RUNNING BLOCK TEST SUITE WITH DETAILED OUTPUT")
    print("#" * 80)

    test_block_header_signature_ok()
    test_block_header_tamper_after_sign_fails()
    test_validate_block_height_and_parent()
    test_block_hash_deterministic()

    print("\n" + "#" * 80)
    print("test_block_basic: ALL TESTS PASSED SUCCESSFULLY")
    print("#" * 80)


if __name__ == "__main__":
    main()
