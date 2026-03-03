# PROJECT CONTEXT — Web ComfyUI Bot

## Mô tả

Hệ thống web tự động hóa workflow WAN 2.2 Image-to-Video trên ComfyUI.
Nhiều user có thể submit job tạo video từ ảnh qua trình duyệt.

## Kiến trúc

- **Frontend**: HTML/CSS/JS (dark theme, glassmorphism)
- **Backend**: FastAPI + SQLite + JWT auth
- **GPU**: Round-robin load balancer cho multi-GPU (dev: 1x 4090, prod: 2x 5090)
- **ComfyUI**: API server, không expose trực tiếp

## Config mấu chốt

- Dev: `config.py` → 1 server `:8188`
- Prod: bỏ comment gpu2 trong `config.py` → thêm `:8288`
- Admin mặc định: `admin` / `admin123` (đổi trong production!)

## Workflow

- File: `FULLHD_6S_Loop_API.json`
- Resolution: cố định 1920×1088
- Prompt/Seed: cố định/random, không expose UI
