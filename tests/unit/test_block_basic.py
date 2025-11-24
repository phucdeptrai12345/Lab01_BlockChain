from src.crypto.keys import generate_keypair
from src.simulator.block import (
    BlockHeader, Block,
    compute_block_hash,
    sign_block_header,
    verify_block_header,
    validate_block,
)


def main():
    chain_id = "test-chain"
    priv, pub = generate_keypair()

    # Tạo header giả
    header = BlockHeader(
        height=1,
        parent_hash="0" * 64,
        state_hash="abcd1234",
        proposer=pub.hex(),
    )

    # Tạo block
    block = Block(header=header, transactions=[])

    # Ký header
    sign_block_header(header, chain_id, priv)

    # Verify chữ ký
    ok = verify_block_header(header, chain_id, pub)
    print("Header signature OK:", ok)

    # Validate block (height + parent_hash)
    valid = validate_block(block, expected_height=1, expected_parent_hash="0" * 64)
    print("Block structure OK:", valid)

    # Hash block
    h = compute_block_hash(header)
    print("Block hash:", h)


if __name__ == "__main__":
    main()