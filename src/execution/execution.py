from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple
import json
import hashlib

# Kiểu cho hook xác minh chữ ký:
VerifyFn = Callable[[bytes, bytes, bytes], bool]


def deterministic_encode(obj: Any) -> bytes:
    """
    Mã hóa byte xác định cho các đối tượng có thể tuần tự hóa thành JSON.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def hexify(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@dataclass(frozen=True)
class Transaction:
    sender: str              # định danh chuẩn của người gửi (ví dụ: hex của khóa công khai)
    key: str                 # khóa trạng thái cần sửa đổi
    value: Any               # giá trị mới (có thể tuần tự hóa)
    signature: bytes         # byte thô của chữ ký (ngữ nghĩa được xác minh bởi verify_fn)
    pubkey: bytes            # byte thô của khóa công khai của người gửi (cho verify_fn)
    meta: Dict[str, Any] = None

    def to_signing_bytes(self, chain_id: str) -> bytes:
        """
        Trả về các byte phải được ký/xác minh cho giao dịch này,
        sử dụng phân tách miền 'TX:chain_id'.
        Mã hóa các trường một cách xác định.
        """
        payload = {
            "domain": f"TX:{chain_id}",
            "sender": self.sender,
            "key": self.key,
            "value": self.value,
            "meta": self.meta or {}
        }
        return deterministic_encode(payload)


@dataclass
class Block:
    height: int
    parent_hash: str             # chuỗi hex
    txs: List[Transaction]
    proposer: str                # id của người đề xuất (proposer)
    state_root: Optional[str] = None


class ExecutionError(Exception):
    pass


class ExecutionState:
    """
    Trạng thái thực thi xác định.
    - state: bản đồ Dict[str, Any]
    - ledger: danh sách các tiêu đề block đã được hoàn tất (chỉ giữ thông tin tối thiểu)
    - logger_fn: hàm gọi lại tùy chọn để ghi lại các sự kiện (msg: str)
    """

    def __init__(self, chain_id: str, logger_fn: Optional[Callable[[str], None]] = None):
        self.chain_id = chain_id
        self.state: Dict[str, Any] = {}
        self.ledger: List[Dict[str, Any]] = []
        self.logger = logger_fn or (lambda msg: None)

    def apply_transaction(self, tx: Transaction, verify_fn: Optional[VerifyFn] = None, require_signature: bool = True):
        """
        Áp dụng một giao dịch đơn lẻ một cách xác định.
        - Nếu verify_fn được cung cấp và require_signature là True: xác minh chữ ký bằng TX:chain_id
        - Nếu xác minh thất bại -> raise ExecutionError
        - Giao dịch chỉ ảnh hưởng đến các khóa thuộc về người gửi (giả định của lab được xử lý bên ngoài).
        """
        self.logger(f"apply_tx: {tx.sender} -> {tx.key}")

        if require_signature:
            if verify_fn is None:
                raise ExecutionError("Cần chữ ký nhưng không cung cấp hàm xác minh")
            msg = tx.to_signing_bytes(self.chain_id)
            ok = verify_fn(msg, tx.signature, tx.pubkey)
            if not ok:
                self.logger("chữ ký không hợp lệ")
                raise ExecutionError("Chữ ký không hợp lệ")

        self.state[tx.key] = tx.value
        self.logger(f"state_update: {tx.key} = {tx.value}")

    def apply_block(self, block: Block, verify_fn: Optional[VerifyFn] = None, require_signature: bool = True) -> str:
        """
        Áp dụng một block (danh sách giao dịch có thứ tự) một cách xác định:
        - Xác minh và thực thi từng tx theo thứ tự.
        - Tính toán state_root sau khi áp dụng.
        - Thêm tiêu đề vào sổ cái (ledger) và trả về hex state_root.
        """
        self.logger(f"apply_block: height={block.height} parent={block.parent_hash} txs={len(block.txs)}")
    
        for tx in block.txs:
            self.apply_transaction(tx, verify_fn=verify_fn, require_signature=require_signature)
        # Tính toán gốc trạng thái
        state_root = self.compute_state_root()
        block.state_root = state_root
        # Ghi lại thông tin tiêu đề tối thiểu
        header = {
            "height": block.height,
            "parent_hash": block.parent_hash,
            "state_root": state_root,
            "proposer": block.proposer
        }
        self.ledger.append(header)
        self.logger(f"block_finalized: height={block.height} state_root={state_root}")
        return state_root

    def compute_state_root(self) -> str:
        """
        Gốc Merkle-like xác định trên các lá khóa/giá trị đã được sắp xếp.
        Mã hóa lá: hash(deterministic_encode([key, value]))
        Cây: nối từng cặp left||right (không có dấu phân cách) và băm cho đến khi còn một gốc.
        Nếu không có lá -> băm của các byte rỗng.
        Trả về chuỗi hex của gốc.
        """
        # Xây dựng danh sách các mục đã sắp xếp theo khóa
        items = sorted(self.state.items(), key=lambda kv: kv[0])
        if not items:
            root = hashlib.sha256(b"").hexdigest()
            self.logger(f"state_root(empty) = {root}")
            return root

        leaves: List[bytes] = []
        for k, v in items:
            leaf_bytes = deterministic_encode([k, v])
            leaf_hash = hashlib.sha256(leaf_bytes).digest()
            leaves.append(leaf_hash)

        # Xây dựng cây nhị phân
        while len(leaves) > 1:
            next_level: List[bytes] = []
            for i in range(0, len(leaves), 2):
                left = leaves[i]
                if i + 1 < len(leaves):
                    right = leaves[i + 1]
                else:
                    right = left
                combined = left + right
                next_level.append(hashlib.sha256(combined).digest())
            leaves = next_level

        root_hex = leaves[0].hex()
        self.logger(f"state_root = {root_hex}")
        return root_hex

    def snapshot(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "state": dict(self.state),
            "ledger": list(self.ledger)
        }

    def load_snapshot(self, snap: Dict[str, Any]):
        self.chain_id = snap["chain_id"]
        self.state = dict(snap["state"])
        self.ledger = list(snap["ledger"])

    def get_state(self) -> Dict[str, Any]:
        return dict(self.state)

    def get_ledger(self) -> List[Dict[str, Any]]:
        return list(self.ledger)