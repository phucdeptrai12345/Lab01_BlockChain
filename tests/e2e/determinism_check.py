"""
Run the same deterministic scenario twice and verify:
- Logs are byte-identical.
- Final state hash is identical.

Usage:
    python tests/e2e/determinism_check.py
"""

import json
import os
import sys
from typing import Tuple

sys.path.append(os.path.abspath("."))

from src.crypto.signing import sign_message  # type: ignore
from src.encoding.codec import encode_tx_for_signing
from src.network.simulator import NetworkConfig, NetworkSimulator
from src.state.state import State, apply_transaction


# Fixed Ed25519 test vector (RFC 8032) to avoid nondeterministic key generation.
ALICE_PRIV_HEX = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
ALICE_PUB_HEX = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
CHAIN_ID = "determinism-test"


def run_scenario(log_path: str, seed: int = 42) -> Tuple[str, str]:
    """
    Run a minimal deterministic scenario:
    - Network with A -> B link
    - HEADER then BODY carrying a signed tx
    - Handler on B applies tx to State
    Returns (state_hash, log_path)
    """
    cfg = NetworkConfig(
        base_delay_ms=5,
        jitter_ms=0,
        drop_rate=0.0,
        duplicate_rate=0.0,
        max_inflight_per_sender=4,
        max_inflight_per_link=4,
        max_bytes_inflight_per_link=1024,
        auto_block_inflight_threshold=10,
        auto_block_duration_ms=100,
        link_bandwidth_bytes_per_ms=100,
    )
    net = NetworkSimulator(seed=seed, config=cfg)
    state = State()

    # Prepare deterministic tx + signature
    tx = {
        "sender": "Alice",
        "key": "Alice/message",
        "value": "hello deterministic",
        "nonce": 1,
    }
    msg = encode_tx_for_signing(tx, CHAIN_ID)
    sig = sign_message(bytes.fromhex(ALICE_PRIV_HEX), msg).hex()

    def handler(message):
        # Apply tx only when body arrives
        if message["type"] == "BODY":
            payload = message["payload"]
            ok = apply_transaction(
                state=state,
                tx=payload["tx"],
                chain_id=CHAIN_ID,
                sender_pubkey=bytes.fromhex(payload["pub"]),
                signature=bytes.fromhex(payload["sig"]),
            )
            if not ok:
                raise RuntimeError("apply_transaction failed in deterministic scenario")

    net.register_node("A", handler)
    net.register_node("B", handler)
    net.load_topology([("A", "B")])

    # Send header first, then body with tx
    net.send_header("A", "B", header_id="h1", height=1, payload={"hdr": 1})
    net.send_body(
        "A",
        "B",
        header_id="h1",
        height=1,
        payload={"tx": tx, "sig": sig, "pub": ALICE_PUB_HEX},
    )

    # Deliver all messages
    net.run_until_idle()

    state_hash = state.compute_state_hash()

    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    net.dump_logs(log_path)
    return state_hash, log_path


def compare_logs(log1: str, log2: str) -> bool:
    with open(log1, "rb") as f1, open(log2, "rb") as f2:
        return f1.read() == f2.read()


def main():
    log1 = os.path.join("logs", "determinism_run1.log")
    log2 = os.path.join("logs", "determinism_run2.log")

    state_hash_1, _ = run_scenario(log1, seed=12345)
    state_hash_2, _ = run_scenario(log2, seed=12345)

    logs_equal = compare_logs(log1, log2)
    hashes_equal = state_hash_1 == state_hash_2

    print(f"Final state hash run1: {state_hash_1}")
    print(f"Final state hash run2: {state_hash_2}")
    print(f"Logs identical: {logs_equal}")
    print(f"State hash identical: {hashes_equal}")

    if not (logs_equal and hashes_equal):
        print("Determinism check FAILED")
        sys.exit(1)
    print("Determinism check PASSED")


if __name__ == "__main__":
    main()

