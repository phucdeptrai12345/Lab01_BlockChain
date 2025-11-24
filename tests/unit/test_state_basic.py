from src.state.state import State, apply_transaction
from src.crypto.keys import generate_keypair
from src.crypto.signing import sign_message
from src.encoding.codec import encode_tx_for_signing


def main():
    chain_id = "test-chain"
    priv, pub = generate_keypair()
    state = State()

    tx_ok = {
        "sender": "Alice",
        "key": "Alice/message",
        "value": "hello",
        "nonce": 1,
    }

    msg_ok = encode_tx_for_signing(tx_ok, chain_id)
    sig_ok = sign_message(priv, msg_ok)

    ok = apply_transaction(state, tx_ok, chain_id, pub, sig_ok)
    print("Apply ok tx:", ok)
    print("State now:", state.data)
    print("State hash:", state.compute_state_hash())

    # Thử transaction sai ownership
    tx_bad = {
        "sender": "Alice",
        "key": "Bob/message",
        "value": "hack",
        "nonce": 2,
    }
    msg_bad = encode_tx_for_signing(tx_bad, chain_id)
    sig_bad = sign_message(priv, msg_bad)

    ok2 = apply_transaction(state, tx_bad, chain_id, pub, sig_bad)
    print("Apply bad tx:", ok2)
    print("State after bad:", state.data)


if __name__ == "__main__":
    main()
