# DECISIONS LOG

| Decision                   | Reason                                          | Impact         | Date       |
| -------------------------- | ----------------------------------------------- | -------------- | ---------- |
| FastAPI thay Flask         | Async, WS native, performance tốt hơn           | Backend core   | 2026-03-03 |
| SQLite thay PostgreSQL     | Đơn giản, không cần setup, đủ cho scale nhỏ-vừa | Database       | 2026-03-03 |
| JWT auth thay session      | Stateless, dễ scale, WS compatible              | Auth           | 2026-03-03 |
| Round-robin load balancing | Đơn giản, fair cho 2 GPU cùng spec              | GPU scheduling | 2026-03-03 |
| Resolution cố định Full HD | User yêu cầu, giảm phức tạp UI                  | UI             | 2026-03-03 |
| Prompt/Seed ẩn khỏi UI     | User yêu cầu, giữ UI tối giản                   | UI             | 2026-03-03 |
| Dark theme + glassmorphism | Phù hợp AI/video context, modern                | Design         | 2026-03-03 |
