"""
Chạy mô phỏng full pipeline với 8 node, 3 block (demo).
Kiểm tra state hash/ledger của tất cả node giống nhau, dùng topo/profile từ thư mục config.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from tests.e2e.run_full_simulation import run_full_sim


def main():
    # Chạy mô phỏng 8 node, 3 block, nạp topo/profile để bám yêu cầu cấu hình từ file
    topo = os.path.join(ROOT, "config", "topology_8nodes_fullmesh.csv")
    profile = os.path.join(ROOT, "config", "link_profile_8nodes_uniform.csv")
    res = run_full_sim(
        num_nodes=8,
        num_blocks=3,
        seed=2025,
        topology_file=topo,
        link_profile_file=profile,
    )
    print("State hashes per node (8):", res["state_hashes"])
    print("All nodes same state hash:", res["all_equal_state"])
    os.makedirs("logs", exist_ok=True)
    with open("logs/full_simulation_8nodes_state_hashes.log", "w", encoding="utf-8") as f:
        f.write(str(res))
    if not res["all_equal_state"]:
        print("Full simulation 8 nodes FAILED")
        sys.exit(1)
    print("Full simulation 8 nodes PASSED")


if __name__ == "__main__":
    main()
