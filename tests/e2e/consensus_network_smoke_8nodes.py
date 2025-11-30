"""
Smoke + determinism check cho 8 node (mục 5 yêu cầu tối thiểu 8 node).
Chạy 2 lần với cùng seed, so sánh network_logs và consensus_logs, finalized_count phải bằng 8.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from src.simulator.harness import run_consensus_smoke_simple


def main():
    res1 = run_consensus_smoke_simple(num_nodes=8, seed=8888)
    res2 = run_consensus_smoke_simple(num_nodes=8, seed=8888)

    # Ghi log ra file
    os.makedirs("logs", exist_ok=True)
    with open("logs/consensus_network_smoke_8_run1.log", "w", encoding="utf-8") as f1:
        for entry in res1["network_logs"]:
            f1.write(f"{entry}\n")
        for entry in res1["consensus_logs"]:
            f1.write(f"{entry}\n")
    with open("logs/consensus_network_smoke_8_run2.log", "w", encoding="utf-8") as f2:
        for entry in res2["network_logs"]:
            f2.write(f"{entry}\n")
        for entry in res2["consensus_logs"]:
            f2.write(f"{entry}\n")

    same_network = res1["network_logs"] == res2["network_logs"]
    same_consensus = res1["consensus_logs"] == res2["consensus_logs"]
    same_finalized = res1["finalized_count"] == res2["finalized_count"] == 8

    print("Network logs identical:", same_network)
    print("Consensus logs identical:", same_consensus)
    print("Finalized counts:", res1["finalized_count"], res2["finalized_count"])

    if not (same_network and same_consensus and same_finalized):
        print("Consensus network smoke 8 nodes FAILED")
        sys.exit(1)
    print("Consensus network smoke 8 nodes PASSED")


if __name__ == "__main__":
    main()
