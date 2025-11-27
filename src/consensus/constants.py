import enum

# Các trạng thái (Steps) của một vòng đồng thuận
class ConsensusStep(enum.Enum):
    PROPOSE = "PROPOSE"     # Giai đoạn đề xuất khối mới
    PREVOTE = "PREVOTE"     # Giai đoạn bỏ phiếu lần 1 (xác nhận đề xuất có hợp lệ không)
    PRECOMMIT = "PRECOMMIT" # Giai đoạn bỏ phiếu lần 2 (cam kết ghi vào blockchain)
    COMMIT = "COMMIT"       # Giai đoạn hoàn tất (đã ghi vào chain - tuỳ chọn thêm để rõ ràng)

# Thời gian chờ (Timeouts) - đơn vị: giây
# Cần điều chỉnh tuỳ thuộc vào độ trễ mạng thực tế
TIMEOUT_PROPOSE = 3.0
TIMEOUT_PREVOTE = 2.0
TIMEOUT_PRECOMMIT = 2.0