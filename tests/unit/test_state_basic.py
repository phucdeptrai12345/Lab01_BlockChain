from src.state.state import State, apply_transaction
from src.crypto.keys import generate_keypair
from src.crypto.signing import sign_message
from src.encoding.codec import encode_tx_for_signing
import json

CHAIN_ID = "test-chain"


def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_state(state: State, label: str):
    print(f"\n--- STATE SNAPSHOT: {label} ---")
    print("data:")
    for k, v in state.data.items():
        print(f"  {k} = {v}")
    print("nonces:", state.nonces)
    print("-----------------------------\n")


def sign_tx(tx, priv):
    msg = encode_tx_for_signing(tx, CHAIN_ID)
    return sign_message(priv, msg)


def test_valid_tx_updates_state_and_nonce():
    print_header("TEST 1 — VALID TX UPDATES STATE AND NONCE")
    priv, pub = generate_keypair()
    state = State()

    tx = {
        "sender": "Alice",
        "key": "Alice/msg",
        "value": "hello",
        "nonce": 1,
    }
    print("TX (valid):")
    print(json.dumps(tx, indent=4))

    sig = sign_tx(tx, priv)
    print("Applying transaction with correct signature...")
    ok = apply_transaction(state, tx, CHAIN_ID, pub, sig)
    print("Apply result:", ok)

    print_state(state, "After valid tx")

    assert ok is True
    assert state.get("Alice/msg") == "hello"
    assert state.nonces["Alice"] == 1


def test_wrong_signature_rejected():
    print_header("TEST 2 — WRONG SIGNATURE MUST BE REJECTED")
    priv1, pub1 = generate_keypair()
    priv2, pub2 = generate_keypair()
    state = State()

    tx = {
        "sender": "Alice",
        "key": "Alice/msg",
        "value": "data",
        "nonce": 1,
    }
    print("TX (wrong signature):")
    print(json.dumps(tx, indent=4))

    sig = sign_tx(tx, priv2)  # ký bằng khóa khác
    print("Applying transaction signed by WRONG private key...")
    ok = apply_transaction(state, tx, CHAIN_ID, pub1, sig)
    print("Apply result:", ok)

    print_state(state, "After wrong-signature tx")

    assert ok is False
    assert state.get("Alice/msg") is None


def test_wrong_owner_rejected():
    print_header("TEST 3 — WRONG OWNER / KEY PREFIX MUST BE REJECTED")
    priv, pub = generate_keypair()
    state = State()

    tx = {
        "sender": "Alice",
        "key": "Bob/msg",  # Alice cố sửa key của Bob
        "value": "hack",
        "nonce": 1,
    }
    print("TX (ownership violation):")
    print(json.dumps(tx, indent=4))

    sig = sign_tx(tx, priv)
    print("Applying tx where Alice tries to modify Bob/... key...")
    ok = apply_transaction(state, tx, CHAIN_ID, pub, sig)
    print("Apply result:", ok)

    print_state(state, "After ownership-violation tx")

    assert ok is False
    assert state.get("Bob/msg") is None


def test_replay_nonce_rejected():
    print_header("TEST 4 — REPLAY ATTACK (SAME NONCE) MUST BE REJECTED")
    priv, pub = generate_keypair()
    state = State()

    tx1 = {"sender": "Alice", "key": "Alice/a", "value": "1", "nonce": 1}
    print("TX1 (first time, valid):")
    print(json.dumps(tx1, indent=4))

    sig1 = sign_tx(tx1, priv)
    ok1 = apply_transaction(state, tx1, CHAIN_ID, pub, sig1)
    print("Apply first time result:", ok1)
    print_state(state, "After first valid tx")

    print("Replaying SAME tx (same nonce = 1)...")
    sig1_replay = sign_tx(tx1, priv)
    ok2 = apply_transaction(state, tx1, CHAIN_ID, pub, sig1_replay)
    print("Apply replay result:", ok2)
    print_state(state, "After replay attempt")

    assert ok1 is True
    assert ok2 is False
    assert state.nonces["Alice"] == 1
    assert state.get("Alice/a") == "1"


def test_out_of_order_nonce_rejected():
    print_header("TEST 5 — OUT-OF-ORDER NONCE MUST BE REJECTED")
    priv, pub = generate_keypair()
    state = State()

    tx1 = {"sender": "Alice", "key": "Alice/a", "value": "1", "nonce": 1}
    print("TX1 (nonce=1, valid):")
    print(json.dumps(tx1, indent=4))

    sig1 = sign_tx(tx1, priv)
    ok1 = apply_transaction(state, tx1, CHAIN_ID, pub, sig1)
    print("Apply nonce=1 result:", ok1)
    print_state(state, "After nonce=1")

    tx2 = {"sender": "Alice", "key": "Alice/a", "value": "2", "nonce": 3}
    print("TX2 (nonce=3, skipping 2, should fail):")
    print(json.dumps(tx2, indent=4))
    sig2 = sign_tx(tx2, priv)
    ok2 = apply_transaction(state, tx2, CHAIN_ID, pub, sig2)
    print("Apply nonce=3 result:", ok2)
    print_state(state, "After out-of-order nonce attempt")

    assert ok1 is True
    assert ok2 is False
    assert state.get("Alice/a") == "1"


def main():
    print("\n" + "-" * 80)
    print("RUNNING STATE TEST SUITE WITH DETAILED OUTPUT")
    print("-" * 80)

    test_valid_tx_updates_state_and_nonce()
    test_wrong_signature_rejected()
    test_wrong_owner_rejected()
    test_replay_nonce_rejected()
    test_out_of_order_nonce_rejected()

    print("\n" + "-" * 80)
    print("test_state_basic: ALL TESTS PASSED SUCCESSFULLY")
    print("-" * 80)


if __name__ == "__main__":
    main()
