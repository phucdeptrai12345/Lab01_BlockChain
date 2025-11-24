from src.encoding.codec import encode_tx_for_signing


def main():
    tx = {
        "sender": "Alice",
        "key": "Alice/message",
        "value": "hello",
        "nonce": 1,
    }
    msg = encode_tx_for_signing(tx, "test-chain")
    print(msg)


if __name__ == "__main__":
    main()
