# Hướng dẫn cài đặt Cloudflare Tunnel — ComfyUI Bot

## Mục tiêu

Expose ComfyUI trên PC (127.0.0.1:8188) ra internet qua URL `https://comfyuibot.dpdns.org` để Web App trên Railway gọi được.

---

## Bước 1: Cài cloudflared trên Windows

### Cách 1: winget (khuyên dùng)
```powershell
winget install --id Cloudflare.cloudflared
```

### Cách 2: Tải trực tiếp
- [Download cloudflared-windows-amd64.msi](https://github.com/cloudflare/cloudflared/releases/latest)
- Chạy file `.msi` để cài

### Kiểm tra
```powershell
cloudflared --version
```

---

## Bước 2: Login Cloudflare

```powershell
cloudflared login
```
- Trình duyệt mở ra → chọn domain `dpdns.org` (hoặc domain chứa subdomain bạn dùng)
- Authorize → file credentials lưu tự động

---

## Bước 3: Tạo Tunnel

```powershell
cloudflared tunnel create comfyui
```

Output sẽ cho bạn **Tunnel ID**, ví dụ: `a1b2c3d4-e5f6-...`

---

## Bước 4: Cấu hình Tunnel

Tạo file config tại `C:\Users\<YOUR_USER>\.cloudflared\config.yml`:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: C:\Users\<YOUR_USER>\.cloudflared\<TUNNEL_ID>.json

ingress:
  - hostname: comfyuibot.dpdns.org
    service: http://127.0.0.1:8188
    originRequest:
      noTLSVerify: true
      connectTimeout: 60s
  - service: http_status:404
```

> ⚠️ Thay `<TUNNEL_ID>` và `<YOUR_USER>` bằng giá trị thực.

---

## Bước 5: Tạo DNS Record

```powershell
cloudflared tunnel route dns comfyui comfyuibot.dpdns.org
```

Lệnh này tạo `CNAME` record trỏ `comfyuibot.dpdns.org` → tunnel.

---

## Bước 6: Chạy Tunnel

```powershell
cloudflared tunnel run comfyui
```

### Test
Mở trình duyệt → `https://comfyuibot.dpdns.org/system_stats`
- Nếu thấy JSON stats → ✅ Tunnel hoạt động!

---

## Bước 7 (Tùy chọn): Cài Windows Service

Để tunnel tự khởi động khi mở máy:

```powershell
# Chạy với quyền Administrator
cloudflared service install
```

Hoặc chạy thủ công mỗi lần:
```powershell
cloudflared tunnel run comfyui
```

---

## Bước 8 (Khuyên dùng): Bảo mật với Cloudflare Access

### Option A: Service Token (cho Web App)
1. Vào [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com)
2. **Access** → **Service Auth** → **Create Service Token**
3. Lưu `Client ID` và `Client Secret`
4. Trên Railway, set env vars:
   ```
   CF_ACCESS_CLIENT_ID=<client-id>
   CF_ACCESS_CLIENT_SECRET=<client-secret>
   ```

### Option B: Application Policy
1. **Access** → **Applications** → **Add an Application**
2. Type: **Self-hosted**
3. Domain: `comfyuibot.dpdns.org`
4. Policy: cho phép Service Token HOẶC email bạn

> 💡 Nếu không cần bảo mật cao, bạn có thể bỏ qua bước 8. Tunnel vẫn hoạt động bình thường.

---

## Troubleshooting

| Vấn đề | Giải pháp |
|--------|-----------|
| `ERR connection refused` | ComfyUI chưa chạy. Khởi động ComfyUI trước → `127.0.0.1:8188` |
| `502 Bad Gateway` | ComfyUI đang load model, đợi vài phút |
| `ERR tunnel not found` | Chạy lại `cloudflared tunnel run comfyui` |
| WebSocket lỗi | Kiểm tra Cloudflare dashboard → Tunnel settings → Enable WebSocket |
| DNS chưa resolve | Đợi 1-5 phút sau khi `route dns`, hoặc check DNS Cloudflare dashboard |
