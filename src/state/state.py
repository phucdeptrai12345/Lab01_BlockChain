import hashlib
from src.encoding.codec import canonical_json, encode_tx_for_signing
from src.crypto.signing import verify_signature


class State:
    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def compute_state_hash(self) -> str:
        """
        Hash toàn bộ state bằng canonical JSON + SHA-256.
        """
        state_bytes = canonical_json(self.data)
        return hashlib.sha256(state_bytes).hexdigest()


def apply_transaction(state: State, tx: dict, chain_id: str,
                      sender_pubkey: bytes, signature: bytes) -> bool:
    """
    Áp dụng 1 transaction vào state nếu:
    - chữ ký hợp lệ
    - key thuộc về sender (vd: "Alice/..." chỉ Alice sửa)
    """
    # 1. Verify chữ ký
    msg = encode_tx_for_signing(tx, chain_id)
    if not verify_signature(sender_pubkey, msg, signature):
        print("Invalid tx signature, reject")
        return False

    sender = tx["sender"]
    key = tx["key"]
    value = tx["value"]

    # 2. Rule ownership: key phải bắt đầu bằng "sender/"
    if not key.startswith(sender + "/"):
        print("Ownership violation, reject")
        return False

    # 3. Cập nhật state
    state.set(key, value)
    return True
