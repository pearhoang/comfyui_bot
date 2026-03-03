# WORKLOG

## 2026-03-03 — Initial Build

- Phân tích workflow `FULLHD_6S_Loop_API.json`, xác định 7 node cần mapping
- Tạo implementation plan, review + approve bởi user
- Triển khai backend: 8 files Python (config, models, database, auth, comfyui_client, load_balancer, main, requirements.txt)
- Triển khai frontend: 3 files (index.html, style.css, app.js)
- Cài dependencies, khởi động server thành công
- Test: login API OK, giao diện login + dashboard hiển thị đúng
- ComfyUI server hiện OFFLINE (chưa bật trên máy dev) — dự kiến

## 2026-03-03 — Cloud Deploy Setup

- Sửa `config.py`: env vars (`COMFYUI_BASE_URL`, `ADMIN_PASSWORD`, `JWT_SECRET`), port 8188
- Sửa `comfyui_client.py`: thêm Cloudflare Access headers cho tất cả HTTP + WebSocket calls
- Sửa `main.py`: đọc PORT từ env var cho Railway
- Tạo `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `railway.json`
- Tạo `.env.example` với template env vars
- Tạo docs: `CLOUDFLARE_TUNNEL_SETUP.md`, `RAILWAY_DEPLOY.md`
- Cập nhật `PROJECT_CONTEXT.md`, `DECISIONS.md`
