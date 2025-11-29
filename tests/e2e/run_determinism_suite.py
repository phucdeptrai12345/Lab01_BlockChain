"""
Chạy toàn bộ các bài kiểm tra determinism cho mục 8:
- determinism_check (tx/state)
- determinism_consensus_network (consensus+network smoke)

Sử dụng:
    python tests/e2e/run_determinism_suite.py
"""

import subprocess
import sys


def run_cmd(cmd: str) -> None:
    print(f"==> Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[FAIL] {cmd}")
        sys.exit(result.returncode)
    print(f"[OK] {cmd}\n")


def main():
    commands = [
        "python tests/e2e/determinism_check.py",
        "python tests/e2e/determinism_consensus_network.py",
    ]
    for cmd in commands:
        run_cmd(cmd)
    print("Determinism suite PASSED.")


if __name__ == "__main__":
    main()

