import os
import sys

sys.path.append(os.path.abspath("."))

from src.network.simulator import NetworkSimulator, NetworkConfig


def test_duplicate_delivery():
    # Ép duplicate_rate=1 để chắc chắn tạo bản sao và log duplicate
    cfg = NetworkConfig(
        base_delay_ms=0,
        jitter_ms=0,
        drop_rate=0.0,
        duplicate_rate=1.0,  # force duplicate
        link_bandwidth_bytes_per_ms=1000,
    )
    net = NetworkSimulator(seed=123, config=cfg)
    received = []

    def handler(msg):
        received.append(msg["header_id"])

    net.register_node("A", handler)
    net.register_node("B", handler)

    net.send_header("A", "B", header_id="dup", height=1, payload={})
    net.run_until_idle()
    assert received.count("dup") == 2
    dup_events = [l for l in net.logs() if l["event"] == "duplicate"]
    assert dup_events, "Duplicate event should be logged"


def test_drop_random():
    # Ép drop_rate=1 để đảm bảo gói bị loại và log drop_random
    cfg = NetworkConfig(
        base_delay_ms=0,
        jitter_ms=0,
        drop_rate=1.0,  # force drop
        duplicate_rate=0.0,
    )
    net = NetworkSimulator(seed=5, config=cfg)
    received = []

    def handler(msg):
        received.append(msg)

    net.register_node("A", handler)
    net.register_node("B", handler)

    net.send_header("A", "B", header_id="drop", height=1, payload={})
    net.run_until_idle()
    assert received == []
    drop_events = [l for l in net.logs() if l["event"] == "drop_random"]
    assert drop_events, "Drop event should be logged"


if __name__ == "__main__":
    test_duplicate_delivery()
    test_drop_random()
    print("duplicate/drop tests passed")
