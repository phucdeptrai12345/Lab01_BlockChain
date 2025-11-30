"""
Điểm chạy chung cho các script kiểm thử determinism và logging.
Thứ tự chạy:
1) Determinism suite (tx/state + consensus/network).
2) Consensus network smoke (4 node) và 8-node.
3) Full simulation smoke (4 node) và 8-node.

Sử dụng:
    python tests/run_all_tests.py
"""

import subprocess
import sys

# Danh sách lệnh cần chạy. Lưu ý: bỏ discover unit vì hiện chưa có TestCase unittest.
COMMANDS = [
    "python tests/e2e/run_determinism_suite.py",
    "python tests/e2e/consensus_network_smoke.py",
    "python tests/e2e/consensus_network_smoke_8nodes.py",
    "python tests/e2e/run_full_simulation.py",
    "python tests/e2e/run_full_simulation_8nodes.py",
]


def run_cmd(cmd: str):
    # Chạy lệnh shell; lỗi thì dừng ngay
    print(f"==> Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[FAIL] {cmd}")
        sys.exit(result.returncode)
    print(f"[OK] {cmd}\n")


def main():
    for cmd in COMMANDS:
        run_cmd(cmd)
    print("All tests completed successfully.")


if __name__ == "__main__":
    main()

