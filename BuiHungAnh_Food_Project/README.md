# ☕ TÀY COFFEE - Hệ thống Quản lý Bán hàng & Vận hành

Dự án quản lý quán cà phê hiện đại, tập trung vào trải nghiệm người dùng và tính chuyên nghiệp trong vận hành. Hệ thống được xây dựng dựa trên kiến trúc **BCE (Boundary-Control-Entity)** và tuân thủ các nguyên lý **SOLID**.

## 🚀 Hướng dẫn cài đặt nhanh

### 1. Yêu cầu hệ thống
- Python 3.9+
- PostgreSQL 12+
- Git

### 2. Cài đặt môi trường
Mở terminal tại thư mục dự án và chạy các lệnh sau:

```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo (Windows)
.\venv\Scripts\activate
# (macOS/Linux: source venv/bin/activate)

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 3. Thiết lập Cơ sở dữ liệu
1. Tạo một Database mới trong PostgreSQL (ví dụ: `tay_coffee_db`).
2. Import tệp `database_postgres.sql` để khởi tạo cấu trúc bảng và dữ liệu mẫu:
   ```bash
   psql -U postgres -d tay_coffee_db -f database_postgres.sql
   ```

### 4. Cấu hình Biến môi trường
1. Copy file `.env.example` thành `.env`:
   ```bash
   cp .env.example .env
   ```
2. Mở file `.env` và điền đầy đủ các thông tin cấu hình (DB, Mapbox Token, OAuth Keys).

### 5. Chạy ứng dụng
```bash
python main.py
```
Ứng dụng sẽ chạy tại: `http://localhost:5500`

---

## 🔑 Tài khoản đăng nhập (Dữ liệu mẫu)

| Vai trò | Email | Mật khẩu |
| :--- | :--- | :--- |
| **Quản trị (Admin)** | `admin@taycoffee.vn` | `admin123` |
| **Thu ngân (Cashier)** | `cashier@taycoffee.vn` | `cashier123` |
| **Nhân viên (Staff)** | `staff@taycoffee.vn` | `staff123` |

---

## 🛠 Kiến trúc dự án (BCE)
- `boundaries/`: Chứa các API routes và định nghĩa giao diện tương tác.
- `controllers/`: Chứa logic nghiệp vụ (Business Logic).
- `entities/`: Chứa các mô hình dữ liệu (Data Models).
- `interfaces/`: Chứa các Interface và Strategy (SOLID compliance).
- `models/`: Chứa các module tương tác trực tiếp với Database.
- `static/` & `templates/`: Giao diện người dùng (HTML, CSS, JS).

---
*Phát triển bởi Tày Coffee Team*
