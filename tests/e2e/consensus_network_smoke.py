"""
Chạy một vòng consensus smoke trên NetworkSimulator:
- 4 node, full-mesh, proposer node 0.
- Proposal -> prevote -> precommit -> finalize.
- Kiểm tra chỉ có 1 block được finalize và log deterministic qua 2 lần chạy.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from src.simulator.harness import run_consensus_smoke_simple


def main():
    # Chạy 2 lần với cùng seed để kiểm tra log deterministic (4 node)
    res1 = run_consensus_smoke_simple(seed=2025)
    res2 = run_consensus_smoke_simple(seed=2025)

    logs_equal = res1["network_logs"] == res2["network_logs"] and res1["consensus_logs"] == res2["consensus_logs"]
    finalized_ok = res1["finalized_count"] == res2["finalized_count"] == 4

    # Ghi log ra file để tiện kiểm tra
    os.makedirs("logs", exist_ok=True)
    with open("logs/consensus_network_smoke_run1.log", "w", encoding="utf-8") as f1:
        for entry in res1["network_logs"]:
            f1.write(f"{entry}\n")
        for entry in res1["consensus_logs"]:
            f1.write(f"{entry}\n")
    with open("logs/consensus_network_smoke_run2.log", "w", encoding="utf-8") as f2:
        for entry in res2["network_logs"]:
            f2.write(f"{entry}\n")
        for entry in res2["consensus_logs"]:
            f2.write(f"{entry}\n")

    print("Finalized count run1:", res1["finalized_count"])
    print("Finalized count run2:", res2["finalized_count"])
    print("Logs identical:", logs_equal)
    if not logs_equal or not finalized_ok:
        print("Consensus network smoke FAILED")
        sys.exit(1)
    print("Consensus network smoke PASSED")


if __name__ == "__main__":
    main()

