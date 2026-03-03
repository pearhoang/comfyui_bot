# PROJECT CONTEXT — Web ComfyUI Bot

## Mô tả

Hệ thống web tự động hóa workflow WAN 2.2 Image-to-Video trên ComfyUI.
Nhiều user có thể submit job tạo video từ ảnh qua trình duyệt.

## Kiến trúc

- **Frontend**: HTML/CSS/JS (dark theme, glassmorphism)
- **Backend**: FastAPI + SQLite + JWT auth
- **GPU**: Round-robin load balancer cho multi-GPU (dev: 1x 4090, prod: 2x 5090)
- **ComfyUI**: API server, không expose trực tiếp
- **Deploy**: Railway.app (cloud) + Cloudflare Tunnel (PC → internet)

## Kiến trúc Deploy

```
User → Railway Web App (FastAPI) → Cloudflare Tunnel → PC (ComfyUI :8188)
```

- Web App chạy trên Railway.app
- ComfyUI chạy trên PC, expose qua Cloudflare Tunnel tại `https://comfyuibot.dpdns.org`
- Backend gọi ComfyUI qua COMFYUI_BASE_URL (env var)
- Frontend chỉ nói chuyện với backend, không gọi trực tiếp ComfyUI

## Config mấu chốt

- Dev: `config.py` → mặc định `http://127.0.0.1:8188`
- Prod: env `COMFYUI_BASE_URL=https://comfyuibot.dpdns.org`
- Admin: env `ADMIN_USERNAME` + `ADMIN_PASSWORD`
- JWT: env `JWT_SECRET` (BẮT BUỘC cố định trong production)
- Cloudflare Access: env `CF_ACCESS_CLIENT_ID` + `CF_ACCESS_CLIENT_SECRET` (tùy chọn)

## Workflow

- File: `FULLHD_6S_Loop_API.json`
- Resolution: cố định 1920×1088
- Prompt/Seed: cố định/random, không expose UI
