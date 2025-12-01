from src.encoding.codec import canonical_json, encode_tx_for_signing


def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def test_canonical_json_deterministic():
    print_header("TEST 1 — CANONICAL JSON DETERMINISM")
    d1 = {"sender": "Alice", "key": "A/msg", "value": 1, "nonce": 1}
    d2 = {"nonce": 1, "value": 1, "key": "A/msg", "sender": "Alice"}  # đảo thứ tự

    print("Dict 1:", d1)
    print("Dict 2 (shuffled):", d2)

    b1 = canonical_json(d1)
    b2 = canonical_json(d2)

    print("Canonical JSON 1:", b1)
    print("Canonical JSON 2:", b2)
    print("Equal?", b1 == b2)

    assert b1 == b2


def test_encode_tx_chain_id_affects_bytes():
    print_header("TEST 2 — TX ENCODING DEPENDS ON CHAIN ID")
    tx = {
        "sender": "Alice",
        "key": "A/msg",
        "value": "hi",
        "nonce": 1,
    }
    print("TX object:", tx)

    m1 = encode_tx_for_signing(tx, "chain-A")
    m2 = encode_tx_for_signing(tx, "chain-B")

    print("Encoded with chain-A:", m1)
    print("Encoded with chain-B:", m2)
    print("Bytes equal?", m1 == m2)

    assert m1 != m2


def main():
    print("\n" + "-" * 80)
    print("RUNNING ENCODING TEST SUITE WITH DETAILED OUTPUT")
    print("-" * 80)

    test_canonical_json_deterministic()
    test_encode_tx_chain_id_affects_bytes()

    print("\n" + "-" * 80)
    print("test_encoding_basic: ALL TESTS PASSED SUCCESSFULLY")
    print("-" * 80)


if __name__ == "__main__":
    main()
