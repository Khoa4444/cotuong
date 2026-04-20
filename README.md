# Dự Án Game Cờ Tướng (Xiangqi Game Project)

Một ứng dụng game Cờ Tướng (Xiangqi) hoàn chỉnh được xây dựng bằng ngôn ngữ lập trình hiện đại, hỗ trợ chơi với máy (AI) hoặc chơi hai người.

## 📌 Tổng Quan Dự Án

Dự án này nhằm tạo ra một môi trường chơi Cờ Tướng trực quan, mượt mà với các thuật toán xử lý nước đi chính xác và giao diện người dùng thân thiện.

## ✨ Tính Năng Chính

- **Chế độ chơi:**
  - **Người vs Người:** Chơi trực tiếp trên cùng một thiết bị.
  - **Người vs Máy (AI):** Tích hợp engine AI với nhiều cấp độ từ Dễ đến Khó.
- **Luật chơi chuẩn:** Áp dụng đầy đủ luật cờ tướng quốc tế (cản chân mã, chặn đường xe, luật lộ mặt tướng...).
- **Tính năng bổ trợ:**
  - Gợi ý nước đi (Hint).
  - Hoàn tác nước đi (Undo/Redo).
  - Lưu và tải ván đấu (Save/Load game).
  - Biên bản ván đấu (Notation) theo định dạng chuẩn.
- **Giao diện:**
  - Đồ họa 2D sắc nét.
  - Hiệu ứng âm thanh khi di chuyển quân và chiếu tướng.

## 📂 Cấu Trúc Thư Mục

```text
├── assets/             # Hình ảnh quân cờ, bàn cờ, âm thanh
├── src/
│   ├── engine/         # Xử lý logic game, thuật toán AI (Minimax, Alpha-Beta)
│   ├── ui/             # Giao diện người dùng (GUI)
│   ├── models/         # Định nghĩa quân cờ (Piece), Bàn cờ (Board)
│   └── utils/          # Các hàm bổ trợ (xử lý file, cấu hình)
├── tests/              # Các kịch bản kiểm thử logic
├── main.py             # File thực thi chính của ứng dụng
└── requirements.txt    # Danh sách thư viện cần thiết
```