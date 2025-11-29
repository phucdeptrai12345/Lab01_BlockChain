import os
import sys

sys.path.append(os.path.abspath("."))

from src.network.simulator import NetworkSimulator, NetworkConfig
from src.simulator.node import SimNode


def main():
    cfg = NetworkConfig(
        base_delay_ms=5,
        jitter_ms=0,
        drop_rate=0.0,
        duplicate_rate=0.0,
        link_bandwidth_bytes_per_ms=100,
    )
    net = NetworkSimulator(seed=1, config=cfg)

    # Three nodes in a line A->B->C
    net.load_topology([("A", "B"), ("B", "C")])

    node_a = SimNode("A", net, peers=["B", "C"])
    node_b = SimNode("B", net, peers=["A", "C"])
    node_c = SimNode("C", net, peers=["A", "B"])

    # A broadcasts header to B (only allowed edge), then B forwards body to C after receiving header
    node_a.broadcast_header("h1", 1, {"hdr": "from A"})
    net.run_until_idle()  # deliver A->B header

    # B got header, now send body to C (header not seen by C yet so will reject)
    node_b.send_body("C", "h1", 1, {"body": "data"})
    net.run_until_idle()

    # Now B forwards header to C, then body again (accepted)
    node_b.network.send_header("B", "C", "h1", 1, {"hdr": "fwd"})
    net.run_until_idle()
    node_b.send_body("C", "h1", 1, {"body": "data"})
    net.run_until_idle()

    print("Inbound A:", node_a.inbound)
    print("Inbound B:", node_b.inbound)
    print("Inbound C:", node_c.inbound)
    for log in net.logs():
        print(log)


if __name__ == "__main__":
    main()

