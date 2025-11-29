from dataclasses import dataclass, field
from typing import List, Dict, Any
import hashlib

from src.encoding.codec import canonical_json, encode_header_for_signing
from src.crypto.signing import sign_message, verify_signature


# -----------------------------
# Block Header
# -----------------------------
@dataclass
class BlockHeader:
    height: int
    parent_hash: str
    state_hash: str
    proposer: str  # proposer public key hex or node id
    signature: str = ""  # hex encoded signature


# -----------------------------
# Block
# -----------------------------
@dataclass
class Block:
    header: BlockHeader
    transactions: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def hash(self) -> str:
        return compute_block_hash(self.header)


# -----------------------------
# Compute block hash
# -----------------------------
def compute_block_hash(header: BlockHeader) -> str:
    """
    Hash the block header (deterministic).
    """
    header_dict = {
        "height": header.height,
        "parent_hash": header.parent_hash,
        "state_hash": header.state_hash,
        "proposer": header.proposer,
        "signature": header.signature,
    }

    h = hashlib.sha256(canonical_json(header_dict)).hexdigest()
    return h


# -----------------------------
# Sign block header
# -----------------------------
def sign_block_header(header: BlockHeader, chain_id: str, privkey_bytes: bytes) -> None:
    """
    Sign the block header IN-PLACE.
    """
    # Prepare message for signing
    header_dict = {
        "height": header.height,
        "parent_hash": header.parent_hash,
        "state_hash": header.state_hash,
        "proposer": header.proposer,
    }
    msg = encode_header_for_signing(header_dict, chain_id)

    sig = sign_message(privkey_bytes, msg)
    header.signature = sig.hex()


# -----------------------------
# Verify block header signature
# -----------------------------
def verify_block_header(header: BlockHeader, chain_id: str, pubkey_bytes: bytes) -> bool:
    """
    Verify: height, parent_hash, state_hash, proposer are signed correctly.
    """
    header_dict = {
        "height": header.height,
        "parent_hash": header.parent_hash,
        "state_hash": header.state_hash,
        "proposer": header.proposer,
    }
    msg = encode_header_for_signing(header_dict, chain_id)
    sig_bytes = bytes.fromhex(header.signature)

    return verify_signature(pubkey_bytes, msg, sig_bytes)


# -----------------------------
# Validate block structure
# -----------------------------
def validate_block(block: Block, expected_height: int, expected_parent_hash: str) -> bool:
    """
    Basic validation:
    - correct height
    - correct parent hash
    - has signature
    """
    header = block.header

    if header.height != expected_height:
        print("Invalid block height")
        return False
    
    if header.parent_hash != expected_parent_hash:
        print("Invalid parent hash")
        return False
    
    if not header.signature:
        print("Missing block signature")
        return False

    return True
