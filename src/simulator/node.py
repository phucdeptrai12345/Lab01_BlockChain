from typing import Dict, List, Any

from src.network.simulator import NetworkSimulator


class SimNode:

    def __init__(self, node_id: str, network: NetworkSimulator, peers: List[str]):
        self.node_id = node_id
        self.network = network
        self.peers = peers
        self.inbound: List[Dict[str, Any]] = []
        self.network.register_node(node_id, self.on_message)

    def on_message(self, msg: Dict[str, Any]) -> None:
        self.inbound.append(msg)

    def broadcast_header(self, header_id: str, height: int, payload: Dict[str, Any]) -> None:
        for peer in self.peers:
            if peer == self.node_id:
                continue
            self.network.send_header(self.node_id, peer, header_id, height, payload)

    def send_body(self, peer: str, header_id: str, height: int, payload: Dict[str, Any]) -> None:
        self.network.send_body(self.node_id, peer, header_id, height, payload)
