"""
Cấu hình hệ thống Web ComfyUI Bot.
Chỉnh sửa file này khi chuyển từ dev (1 GPU) sang production (2 GPU).
"""

import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# ComfyUI Servers
# DEV  (4090) : chỉ 1 server
# PROD (5090) : bỏ comment dòng gpu2
# ============================================================
COMFYUI_SERVERS = [
    {"id": "gpu1", "url": "http://127.0.0.1:8288", "name": "GPU #1"},
    # {"id": "gpu2", "url": "http://127.0.0.1:8288", "name": "RTX 5090 #2"},
]

# ============================================================
# Paths
# ============================================================
WORKFLOW_PATH = os.path.join(BASE_DIR, "FULLHD_6S_Loop_API.json")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "comfybot.db")

# ============================================================
# JWT Authentication
# ============================================================
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# ============================================================
# Default Admin (tự tạo lần đầu chạy)
# ============================================================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # ⚠️ Đổi trong production!

# ============================================================
# Workflow defaults (cố định — không cho user thay đổi)
# ============================================================
WORKFLOW_DEFAULTS = {
    "width": 1920,
    "height": 1088,
    "length": 73,  # frames
}
