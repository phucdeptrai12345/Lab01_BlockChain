## Mô tả ngắn
Mã nguồn mô phỏng một blockchain tối giản với mạng không tin cậy, đồng thuận 2 pha (Prevote/Precommit) và thực thi trạng thái xác định. Đã có các kịch bản determinism, smoke test mạng/consensus, và mô phỏng pipeline đơn giản nhiều block.

## Yêu cầu hệ thống
- Python 3.10+ (đang dùng 3.13)
- Thư viện: `cryptography` (cài qua `pip install -r requirements.txt`)

## Cấu trúc thư mục
- `src/`
  - `network/` – NetworkSimulator (delay/drop/dup, backpressure, auto block, topo/profile từ file)
  - `consensus/` – Controller/helper tối giản, engine đếm quorum, hằng số
  - `execution/` – ExecutionState/Transaction/Block áp dụng tx, tính state_root
  - `simulator/` – Node/harness demo gửi header/body/vote
  - `state/`, `crypto/`, `encoding/` – mã hóa canonical JSON, ký/verify Ed25519, hash state
- `tests/`
  - `unit/` – script + TestCase kiểm tra crypto/encoding/state/block/ledger/network
  - `e2e/` – determinism, smoke consensus, full simulation, test coverage bổ sung
  - `run_all_tests.py` – entrypoint chạy toàn bộ các script E2E chính
- `logs/` – log được ghi khi chạy các script E2E (tự tạo nếu chưa có)
- `config/` – file topo/profile mẫu (`topology_sample.csv`, `link_profile_sample.csv`)

## Cách chạy nhanh
1. Cài thư viện:
   ```bash
   pip install -r requirements.txt
   ```
2. Chạy toàn bộ test/script chính:
   ```bash
   python tests/run_all_tests.py
   ```
   (bao gồm determinism suite, coverage adversarial, smoke consensus 4/8 node, full simulation 4/8 node)

3. Chạy riêng từng kịch bản determinism:
   ```bash
   python tests/e2e/run_determinism_suite.py
   ```
   - So sánh log/state tx (`determinism_check`) và consensus+network (`determinism_consensus_network`), diff các cặp log trong `logs/`.

4. Smoke consensus qua mạng:
   ```bash
   python tests/e2e/consensus_network_smoke.py         # 4 node
   python tests/e2e/consensus_network_smoke_8nodes.py  # 8 node
   ```
   Ghi log vào `logs/consensus_network_smoke*_run*.log`.

5. Full simulation pipeline (đơn giản, bỏ qua ký/verify vote):
   ```bash
   python tests/e2e/run_full_simulation.py        # 4 node, 3 block
   python tests/e2e/run_full_simulation_8nodes.py # 8 node, 3 block
   ```
   Ghi state/ledger vào `logs/full_simulation*_state_hashes.log`.

6. Test coverage bổ sung (adversarial cases):
   ```bash
   python tests/e2e/test_consensus_coverage.py
   ```
   Kiểm tra: hai proposal cùng height, vote invalid, replay tx, vote trễ không phá safety.

## Cấu hình mẫu (config/)
- `config/topology_sample.csv`: danh sách edge (sender,receiver) để nạp topo qua `load_topology_from_file`.
- `config/link_profile_sample.csv`: cấu hình delay/jitter/bandwidth/drop cho từng link, dùng `load_link_profile_from_file`.
