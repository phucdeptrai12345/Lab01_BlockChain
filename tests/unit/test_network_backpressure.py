import os
import sys

sys.path.append(os.path.abspath("."))

from src.network.simulator import NetworkSimulator, NetworkConfig


def main():
    # Demo backpressure + auto-block: cấu hình bandwidth nhỏ, threshold thấp
    cfg = NetworkConfig(
        base_delay_ms=10,
        jitter_ms=0,
        drop_rate=0.0,
        duplicate_rate=0.0,
        max_inflight_per_sender=10,
        max_inflight_per_link=10,
        max_bytes_inflight_per_link=300,  # small to trigger queue
        auto_block_inflight_threshold=2,  # block when 2nd in flight
        auto_block_duration_ms=50,
    )
    net = NetworkSimulator(seed=7, config=cfg)

    delivered = []

    def handler(msg):
        delivered.append((msg["type"], msg["header_id"]))

    net.register_node("A", handler)
    net.register_node("B", handler)

    # Backpressure: gói đầu đi qua, gói thứ hai bị queue tới khi link rảnh
    net.send_header("A", "B", header_id="h1", height=1, payload={"data": "x" * 50})
    net.send_header("A", "B", header_id="h1b", height=1, payload={"data": "y" * 50})
    net.run_until_idle()

    # Auto block: inflight thứ hai trên link kích hoạt auto block, gói tiếp bị chặn
    net.send_header("A", "B", header_id="h2", height=2, payload={"data": "a" * 10})
    net.send_header("A", "B", header_id="h3", height=3, payload={"data": "b" * 10})  # should auto-block
    net.run_until_idle()  # deliver h2

    # Hết thời gian block, gửi lại để xác nhận auto-unblock
    net.advance_time(60)
    net.send_header("A", "B", header_id="h4", height=4, payload={"data": "c" * 10})
    net.run_until_idle()

    print("Delivered:", delivered)
    for log in net.logs():
        print(log)


if __name__ == "__main__":
    main()
