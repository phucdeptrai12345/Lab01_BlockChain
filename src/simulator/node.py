from typing import Dict, List, Any

from src.network.simulator import NetworkSimulator


class SimNode:
    """
    Minimal node wrapper to show integration with NetworkSimulator.
    This does NOT implement consensus; it only demonstrates send/receive wiring.
    Dùng để ví dụ cách đăng ký handler và broadcast header/body.
    Mỗi node tự lưu inbound messages để người dùng kiểm tra.
    """

    def __init__(self, node_id: str, network: NetworkSimulator, peers: List[str]):
        self.node_id = node_id
        self.network = network
        self.peers = peers
        self.inbound: List[Dict[str, Any]] = []

        # Register message handler
        self.network.register_node(node_id, self.on_message)

    def on_message(self, msg: Dict[str, Any]) -> None:
        # Store inbound for inspection; real consensus would process here.
        self.inbound.append(msg)

    def broadcast_header(self, header_id: str, height: int, payload: Dict[str, Any]) -> None:
        for peer in self.peers:
            if peer == self.node_id:
                continue
            self.network.send_header(self.node_id, peer, header_id, height, payload)

    def send_body(self, peer: str, header_id: str, height: int, payload: Dict[str, Any]) -> None:
        self.network.send_body(self.node_id, peer, header_id, height, payload)
