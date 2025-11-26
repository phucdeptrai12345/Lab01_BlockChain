import hashlib
from typing import Dict, Any, Optional

# Import các hàm từ module của bạn
from src.encoding.codec import canonical_json, encode_tx_for_signing
from src.crypto.signing import verify_signature

class State:
    def __init__(self):
        # Lưu dữ liệu ứng dụng (Ví dụ: "Alice/balance": 100)
        self.data: Dict[str, Any] = {}
        
        # Lưu nonce của từng tài khoản để chống Replay Attack
        # Dạng: {"Alice_Pubkey_Hex": 5} -> Giao dịch tiếp theo phải có nonce = 6
        self.nonces: Dict[str, int] = {}

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value

    # Logic xử lý Nonce
    def get_nonce(self, sender: str) -> int:
        """Lấy nonce hiện tại của sender. Nếu chưa có thì trả về 0."""
        return self.nonces.get(sender, 0)

    def increment_nonce(self, sender: str):
        """Tăng nonce của sender lên 1 sau khi giao dịch thành công."""
        current = self.get_nonce(sender)
        self.nonces[sender] = current + 1

    # Logic Copy trạng thái
    def copy(self):
        """
        Tạo ra một bản sao (clone) của State hiện tại.
        Dùng khi Node muốn chạy thử một Block mới nhận được.
        Nếu Block hợp lệ -> Gán bản copy này thành bản chính.
        Nếu Block lỗi -> Vứt bản copy đi, bản chính vẫn an toàn.
        """
        new_state = State()
        new_state.data = self.data.copy()
        new_state.nonces = self.nonces.copy()
        return new_state

    def compute_state_hash(self) -> str:
        """
        Tính Hash đại diện cho toàn bộ trạng thái (Data + Nonce).
        """
        # Gộp cả data và nonces vào để hash, đảm bảo sự toàn vẹn
        snapshot = {
            "data": self.data,
            "nonces": self.nonces
        }
        state_bytes = canonical_json(snapshot)
        return hashlib.sha256(state_bytes).hexdigest()


def apply_transaction(state: State, tx: dict, chain_id: str) -> bool:
    """
    Áp dụng 1 transaction vào state.
    Trả về True nếu thành công, False nếu lỗi.
    """
    try:
        sender_hex = tx["sender"]       # Public key dạng Hex
        signature_hex = tx["signature"] # Chữ ký dạng Hex
        
        # Verify chữ ký
        # Convert hex sang bytes để thư viện crypto xử lý
        sender_pubkey_bytes = bytes.fromhex(sender_hex)
        signature_bytes = bytes.fromhex(signature_hex)
        
        # Tạo lại thông điệp gốc đã ký (gồm prefix TX:...)
        msg = encode_tx_for_signing(tx, chain_id)
        
        if not verify_signature(sender_pubkey_bytes, msg, signature_bytes):
            print(f"[State] Invalid signature from {sender_hex[:8]}")
            return False

        # Check Nonce (Replay Attack check)
        # Nonce trong Tx phải lớn hơn nonce hiện tại đúng 1 đơn vị
        expected_nonce = state.get_nonce(sender_hex) + 1
        if tx["nonce"] != expected_nonce:
            print(f"[State] Invalid nonce. Expected {expected_nonce}, got {tx['nonce']}")
            return False

        # Check Ownership (Application Logic check)"
        key = tx["key"]
        if not key.startswith(sender_hex + "/"):
            print(f"[State] Ownership violation. Sender {sender_hex[:8]} cannot touch {key}")
            return False

        # Nếu mọi thứ OK -> Cập nhật State
        state.set(key, tx["value"])
        state.increment_nonce(sender_hex)
        return True

    except Exception as e:
        print(f"[State] Exception applying tx: {e}")
        return False