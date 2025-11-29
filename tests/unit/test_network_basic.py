import os
import sys

sys.path.append(os.path.abspath("."))

from src.network.simulator import NetworkSimulator, NetworkConfig


def main():
    # Deterministic run
    cfg = NetworkConfig(
        base_delay_ms=10,
        jitter_ms=0,
        drop_rate=0.0,
        duplicate_rate=0.0,
        max_inflight_per_sender=4,
        max_inflight_per_link=2,
    )
    net = NetworkSimulator(seed=42, config=cfg)

    delivered = []

    def handler(msg):
        delivered.append(msg)

    net.register_node("A", handler)
    net.register_node("B", handler)

    # Restrict topology: only A->B allowed (B->A will drop)
    net.load_topology([("A", "B")])

    # This should drop because topology disallows B->A
    net.send_header("B", "A", header_id="z0", height=0, payload={"hdr": 0})

    # Body without header -> rejected and not delivered
    net.send_body("A", "B", header_id="h1", height=1, payload={"body": 123})

    # Send header then deliver it
    net.send_header("A", "B", header_id="h1", height=1, payload={"hdr": 1})
    net.run_until_idle()

    # Now body is allowed (header seen)
    net.send_body("A", "B", header_id="h1", height=1, payload={"body": 123})
    net.run_until_idle()

    # Block the link and see drop
    net.block_link("A", "B")
    net.send_header("A", "B", header_id="h2", height=2, payload={"hdr": 2})
    net.advance_time(50)
    net.unblock_link("A", "B")

    print("Delivered messages:", delivered)
    print("Logs:", net.logs())


if __name__ == "__main__":
    main()
