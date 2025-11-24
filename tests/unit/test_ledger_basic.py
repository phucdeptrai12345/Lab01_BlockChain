import sys, os
sys.path.append(os.path.abspath("."))

from src.crypto.keys import generate_keypair
from src.state.state import State
from src.simulator.block import BlockHeader, Block, compute_block_hash, sign_block_header
from src.simulator.ledger import Ledger


def main():
    chain_id = "test-chain"
    priv, pub = generate_keypair()

    # khởi tạo ledger rỗng
    ledger = Ledger()
    print("Initial height:", ledger.height())
    print("Initial last_hash:", ledger.last_hash())

    # tạo state giả + state_hash
    state = State()
    state.set("Alice/message", "hello")
    state_hash = state.compute_state_hash()

    # tạo block #1
    header1 = BlockHeader(
        height=1,
        parent_hash=ledger.last_hash(),  # "0"*64 cho genesis parent
        state_hash=state_hash,
        proposer=pub.hex(),
    )
    block1 = Block(header=header1, transactions=[])
    sign_block_header(header1, chain_id, priv)

    # giả sử consensus đã final block1 -> append vào ledger
    ledger.append_finalized_block(block1)

    print("After 1st block - height:", ledger.height())
    print("Last hash:", ledger.last_hash())
    print("Last block height:", ledger.last_block().header.height)


if __name__ == "__main__":
    main()
