"""
Determinism check cho consensus smoke qua mạng:
- Chạy run_consensus_smoke_simple 2 lần với cùng seed.
- So sánh network_logs, consensus_logs và finalized_count.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from src.simulator.harness import run_consensus_smoke_simple


def main():
    res1 = run_consensus_smoke_simple(seed=777)
    res2 = run_consensus_smoke_simple(seed=777)

    same_network = res1["network_logs"] == res2["network_logs"]
    same_consensus = res1["consensus_logs"] == res2["consensus_logs"]
    same_finalized = res1["finalized_count"] == res2["finalized_count"] == 4

    print("Network logs identical:", same_network)
    print("Consensus logs identical:", same_consensus)
    print("Finalized counts:", res1["finalized_count"], res2["finalized_count"])

    if not (same_network and same_consensus and same_finalized):
        print("Determinism consensus network FAILED")
        sys.exit(1)
    print("Determinism consensus network PASSED")


if __name__ == "__main__":
    main()

