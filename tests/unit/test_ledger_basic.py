import sys, os
sys.path.append(os.path.abspath("."))

from src.crypto.keys import generate_keypair
from src.simulator.block import BlockHeader, Block, compute_block_hash, sign_block_header
from src.simulator.ledger import Ledger

CHAIN_ID = "test-chain"


def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def make_block(height, parent_hash, state_hash, priv):
    header = BlockHeader(
        height=height,
        parent_hash=parent_hash,
        state_hash=state_hash,
        proposer="validator-1",
        signature="",
    )
    block = Block(header=header, transactions=[])
    sign_block_header(header, CHAIN_ID, priv)
    return block


def print_ledger(ledger: Ledger, label: str):
    print(f"\n--- LEDGER SNAPSHOT: {label} ---")
    print("Height:", ledger.height())
    print("Last hash:", ledger.last_hash())
    print("Blocks:")
    for i, blk in enumerate(ledger.all_blocks()):
        h = compute_block_hash(blk.header)
        print(f"  idx={i}, height={blk.header.height}, hash={h}")
    print("-------------------------------\n")


def test_empty_ledger_defaults():
    print_header("TEST 1 — EMPTY LEDGER DEFAULTS")
    ledger = Ledger()
    print_ledger(ledger, "Initial empty ledger")

    assert ledger.height() == 0
    assert ledger.last_hash() == "0" * 64
    assert ledger.all_blocks() == []


def test_append_valid_blocks_and_parent_check():
    print_header("TEST 2 — APPEND VALID BLOCKS WITH CORRECT PARENT")
    priv, pub = generate_keypair()
    ledger = Ledger()

    b1 = make_block(1, "0" * 64, "1" * 64, priv)
    print("Appending block #1 (height=1, parent=0*64)...")
    ok1 = ledger.append_finalized_block(b1)
    print("Append result:", ok1)
    print_ledger(ledger, "After block #1")

    h1 = compute_block_hash(b1.header)
    assert ok1 is True
    assert ledger.height() == 1
    assert ledger.last_hash() == h1

    b2 = make_block(2, h1, "2" * 64, priv)
    print("Appending block #2 (height=2, parent=hash(block1))...")
    ok2 = ledger.append_finalized_block(b2)
    print("Append result:", ok2)
    print_ledger(ledger, "After block #2")

    h2 = compute_block_hash(b2.header)
    assert ok2 is True
    assert ledger.height() == 2
    assert ledger.last_hash() == h2


def test_append_block_with_wrong_parent_fails():
    print_header("TEST 3 — APPEND BLOCK WITH WRONG PARENT MUST FAIL")
    priv, pub = generate_keypair()
    ledger = Ledger()

    b1 = make_block(1, "0" * 64, "1" * 64, priv)
    print("Appending block #1 (valid)...")
    assert ledger.append_finalized_block(b1) is True
    print_ledger(ledger, "After valid block #1")

    b2 = make_block(2, "9" * 64, "2" * 64, priv)
    print("Appending block #2 with WRONG parenthash=9*64...")
    ok2 = ledger.append_finalized_block(b2)
    print("Append result:", ok2)
    print_ledger(ledger, "After wrong-parent block attempt")

    assert ok2 is False
    assert ledger.height() == 1  # không tăng


def main():
    print("\n" + "#" * 80)
    print("RUNNING LEDGER TEST SUITE WITH DETAILED OUTPUT")
    print("#" * 80)

    test_empty_ledger_defaults()
    test_append_valid_blocks_and_parent_check()
    test_append_block_with_wrong_parent_fails()

    print("\n" + "#" * 80)
    print("test_ledger_basic: ALL TESTS PASSED SUCCESSFULLY")
    print("#" * 80)


if __name__ == "__main__":
    main()
