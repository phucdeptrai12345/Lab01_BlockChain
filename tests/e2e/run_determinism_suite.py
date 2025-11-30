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

    # So sánh file log nếu tồn tại
    from pathlib import Path
    import filecmp

    pairs = [
        ("logs/determinism_run1.log", "logs/determinism_run2.log"),
        ("logs/consensus_network_smoke_run1.log", "logs/consensus_network_smoke_run2.log"),
        ("logs/consensus_network_smoke_8_run1.log", "logs/consensus_network_smoke_8_run2.log"),
    ]
    for a, b in pairs:
        pa, pb = Path(a), Path(b)
        if pa.exists() and pb.exists():
            same = filecmp.cmp(pa, pb, shallow=False)
            print(f"Diff {a} vs {b}: {'IDENTICAL' if same else 'DIFFERENT'}")
            if not same:
                sys.exit(1)
    print("Determinism suite PASSED.")


if __name__ == "__main__":
    main()
