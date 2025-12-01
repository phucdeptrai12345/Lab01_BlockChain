# Cấu trúc thư mục `config/`

- `topology_*.csv`: mô tả danh sách cạnh có hướng (sender,receiver) cho `NetworkSimulator.load_topology_from_file`. Mỗi dòng: `sender,receiver`. Dòng bắt đầu `#` sẽ bị bỏ qua. Nếu không nạp file, simulator mặc định full-mesh.  
  - `topology_8nodes_fullmesh.csv`: đủ tất cả cặp 8 nút (không self-loop).  
  - `topology_8nodes_ring.csv`: vòng 8 nút hai chiều.
- `link_profile_*.csv`: tham số đường truyền per-link cho `NetworkSimulator.load_link_profile_from_file`. Mỗi dòng: `sender,receiver,base_delay_ms,jitter_ms,bandwidth_bytes_per_ms,drop_rate`. Các trường cuối có thể bỏ trống để dùng mặc định từ `NetworkConfig`.
- `*.gitkeep`: giúp giữ thư mục trong repo khi không có file khác.

Ví dụ sử dụng:
```python
from src.network.simulator import NetworkSimulator
sim = NetworkSimulator(seed=0)
sim.load_topology_from_file("config/topology_8nodes_ring.csv")
sim.load_link_profile_from_file("config/link_profile_8nodes_uniform.csv")
```

Các file mẫu bên dưới đủ để chạy thử mô phỏng 4/8 node trong phần test hiện tại.
