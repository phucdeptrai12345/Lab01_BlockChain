"""
Entry point to run all available tests/scripts for determinism and logging.

Runs, in order:
1) Unit tests (unittest discover under tests/unit).
2) Determinism suite (tests/e2e/run_determinism_suite.py).
3) Consensus network smoke (4 node) and 8-node smoke.
4) Full simulation smoke (4 node) and 8-node variant.

Usage:
    python run_all_tests.py
"""

import subprocess
import sys


# Danh sách lệnh cần chạy. Lưu ý: bỏ discover unit vì hiện chưa có TestCase dạng unittest.
COMMANDS = [
    "python tests/e2e/run_determinism_suite.py",
    "python tests/e2e/consensus_network_smoke.py",
    "python tests/e2e/consensus_network_smoke_8nodes.py",
    "python tests/e2e/run_full_simulation.py",
    "python tests/e2e/run_full_simulation_8nodes.py",
]


def run_cmd(cmd: str):
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
