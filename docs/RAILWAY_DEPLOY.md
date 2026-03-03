# Hướng dẫn Deploy lên Railway.app

## Bước 1: Push code lên GitHub

```powershell
cd comfyui_bot
git add -A
git commit -m "feat: cloud deploy support (env vars, Dockerfile, Railway config)"
git push origin main
```

---

## Bước 2: Tạo project trên Railway

1. Vào [railway.app](https://railway.app) → **New Project**
2. Chọn **Deploy from GitHub repo**
3. Chọn repo `pearhoang/comfyui_bot`
4. Railway tự detect `Dockerfile` và bắt đầu build

---

## Bước 3: Cấu hình Environment Variables

Trong Railway project → **Variables** → thêm:

| Variable | Value |
|----------|-------|
| `COMFYUI_BASE_URL` | `https://comfyuibot.dpdns.org` |
| `JWT_SECRET` | *(random string dài ≥32 ký tự)* |
| `ADMIN_PASSWORD` | *(mật khẩu mạnh)* |
| `PORT` | `8000` |

### Nếu bật Cloudflare Access (tùy chọn):
| Variable | Value |
|----------|-------|
| `CF_ACCESS_CLIENT_ID` | *(từ Cloudflare Zero Trust)* |
| `CF_ACCESS_CLIENT_SECRET` | *(từ Cloudflare Zero Trust)* |

> 💡 Tạo JWT_SECRET nhanh: `python -c "import secrets; print(secrets.token_hex(32))"`

---

## Bước 4: Custom Domain (tùy chọn)

Nếu bạn muốn Web App có domain riêng (VD: `app.dpdns.org`):

1. Railway → **Settings** → **Networking** → **Custom Domain**
2. Thêm: `app.dpdns.org`
3. Railway cho bạn CNAME value → thêm CNAME record trong Cloudflare DNS

---

## Bước 5: Verify

1. Railway auto-deploy sau mỗi `git push`
2. Truy cập URL Railway (hoặc custom domain)
3. Login với `admin` / `<ADMIN_PASSWORD đã set>`
4. Upload ảnh → Job sẽ được gửi qua tunnel tới ComfyUI trên PC

---

## Lưu ý quan trọng

> ⚠️ **ComfyUI phải đang chạy trên PC** + **Cloudflare Tunnel phải đang chạy** để jobs render được.

> ⚠️ SQLite DB nằm trong container Railway. Nếu redeploy, **DB sẽ reset**. Để giữ data, cần mount Railway Volume hoặc chuyển sang PostgreSQL sau này.

---

## Kiến trúc hoàn chỉnh

```
User (trình duyệt)
  │
  ▼
Railway Web App (FastAPI, port 8000)
  │  https://app.dpdns.org hoặc Railway URL
  │
  │ gọi REST + WebSocket
  ▼
Cloudflare Tunnel
  │  https://comfyuibot.dpdns.org
  │
  │ (encrypted, qua Cloudflare network)
  ▼
PC của bạn → cloudflared → ComfyUI (127.0.0.1:8188)
```
