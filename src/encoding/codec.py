import json


def canonical_json(data: dict) -> bytes:
    """
    Encode dict -> JSON bytes với key sorted, không khoảng trắng thừa.
    Đảm bảo deterministic giữa các node.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")
def encode_tx_for_signing(tx: dict, chain_id: str) -> bytes:
    """
    Tạo bytes để ký transaction, có domain: TX:chain_id
    """
    payload = {
        "chain_id": chain_id,
        "type": "TX",
        "sender": tx["sender"],
        "key": tx["key"],
        "value": tx["value"],
        "nonce": tx["nonce"],
    }
    return b"TX:" + chain_id.encode() + b"|" + canonical_json(payload)


def encode_header_for_signing(header: dict, chain_id: str) -> bytes:
    """
    Domain HEADER:chain_id
    """
    payload = {
        "chain_id": chain_id,
        "type": "HEADER",
        "height": header["height"],
        "parent_hash": header["parent_hash"],
        "state_hash": header["state_hash"],
        "proposer": header["proposer"],
    }
    return b"HEADER:" + chain_id.encode() + b"|" + canonical_json(payload)


def encode_vote_for_signing(vote: dict, chain_id: str) -> bytes:
    """
    Domain VOTE:chain_id
    """
    payload = {
        "chain_id": chain_id,
        "type": "VOTE",
        "height": vote["height"],
        "block_hash": vote["block_hash"],
        "phase": vote["phase"],  # "PREVOTE" / "PRECOMMIT"
        "voter": vote["voter"],
    }
    return b"VOTE:" + chain_id.encode() + b"|" + canonical_json(payload)
