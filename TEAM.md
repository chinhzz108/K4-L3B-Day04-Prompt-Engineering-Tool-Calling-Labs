# TEAM — Day04, K4-L3B

**Làm nhóm.** Mỗi người tự viết và commit phần INDIVIDUAL của mình.

## Thông tin bài nộp

- **Tên nhóm:** Northstar AI Devs
- **Người đại diện / MSSV:** Chu Văn Quân (GitHub: `chinhzz108`)
- **Tên repo:** `K4-L3B-Day04-Prompt-Engineering-Tool-Calling-Labs`
- **URL repo, nhánh nộp, commit chốt:**
  - URL repo: `https://github.com/chinhzz108/K4-L3B-Day04-Prompt-Engineering-Tool-Calling-Labs`
  - Nhánh nộp: `main`
- **Deadline áp dụng và link thông báo đổi hạn nếu có:** 23:59 ngày làm lab, Asia/Ho_Chi_Minh (UTC+07:00)

## Thành viên

| Họ và tên | MSSV | GitHub | Vai trò và công việc | File/commit/PR |
|---|---|---|---|---|
| Chu Văn Quân | Đang cập nhật | chinhzz108 | Lead / AI Engineer — Thiết kế prompt v0-v3, tools schema, phát triển Bonus Tool check_device_warranty, xây dựng giao diện Streamlit UI, bộ 10 eval group cases và hoàn thiện báo cáo | `artifacts/system_prompt.md`, `artifacts/tools.yaml`, `tools/check_device_warranty/*`, `ui.py`, `data/eval_group.json`, `REPORT.md` |

## Nhận xét chung

- **Kết quả và bằng chứng:** Đạt độ chính xác 100% (30/30) trên bộ kiểm thử cơ bản v3 (`runs/v3_B_base_gemini_20260919T130000000000.json`), 100% (10/10) trên bộ kiểm thử nhóm (`runs/v3_B_group_gemini_20260919T140000000000.json`), và 100% (12/12) trên bộ tấn công adversarial (`runs/v3_B_adversarial_gemini_20260919T150000000000.json`). Toàn bộ các run đều có `provider_error_cases == 0`.
- **Thay đổi hiệu quả nhất:** Thiết lập ranh giới an toàn bắt buộc hỏi lại (`clarify`) khi thiếu mã định danh hoặc xin xác nhận trước khi thực hiện hành động ghi dữ liệu (`create_ticket`), kết hợp cơ chế ưu tiên ý định mới nhất (`latest intent wins`) và hủy xác nhận cũ khi payload thay đổi.
- **Giới hạn còn lại:** Phụ thuộc vào chất lượng kết nối API mạng của provider; chưa hỗ trợ tự động mở ticket trên các hệ thống bên thứ ba như Jira/ServiceNow thật.
- **Cách phân công và tích hợp:** Tuân thủ quy trình phát triển lặp v0 -> v1 -> v2 -> v3 bài bản theo giả thuyết kỹ thuật, đối chiếu metric trước/sau tại `version_log.csv` và kiểm thử tự động toàn diện.

## INDIVIDUAL

### Chu Văn Quân — chinhzz108

- **Phần việc và file/commit/PR:**
  - Tối ưu hóa `artifacts/system_prompt.md` qua các phiên bản v1, v2, v3.
  - Tinh chỉnh mô tả tham số công cụ trong `artifacts/tools.yaml`.
  - Phát triển công cụ mở rộng (Bonus Tool 10đ) `tools/check_device_warranty/tool.py` và `TOOL.md` tích hợp vào hệ thống.
  - Viết 10 test cases chất lượng cao trong `data/eval_group.json` (5 single-turn, 5 multi-turn).
  - Xây dựng giao diện ứng dụng trực quan thời gian thực `ui.py` bằng Streamlit hỗ trợ theo dõi tool calls và xuất log.
  - Tạo 5 kịch bản transcript JSON thực tế trong thư mục `transcripts/`.
  - Hoàn thiện tài liệu tổng kết kỹ thuật `starter_v0/artifacts/REPORT.md`.
- **Quyết định, khó khăn và cách xử lý:** Khó khăn lớn nhất là hiện tượng chập chờn tải (503 UNAVAILABLE) và giới hạn tốc độ (429 RESOURCE_EXHAUSTED) từ server API miễn phí của provider. Tôi đã quyết định cải tiến bộ adapter `gemini_provider.py` với cơ chế retry tự động thông minh (exponential backoff) và điều tiết nhịp độ kiểm thử (`run_eval.py`), giúp mọi lượt đánh giá đều thành công trọn vẹn với 0 lỗi provider.
- **Điều đã học:** Nắm vững bản chất của cơ chế Function Calling trong các mô hình ngôn ngữ lớn (LLM), kỹ thuật thiết kế schema JSON chuẩn xác, cách kiểm soát ranh giới xác nhận an toàn (Confirmation Boundaries), và nguyên lý xử lý hội thoại nhiều lượt không bị trôi ngữ cảnh.
- **AI/công cụ đã dùng và cách kiểm tra:** Dùng Python 3.13, Streamlit, Google GenAI SDK, Git; kiểm tra kết quả qua script `run_eval.py` tự động và kiểm thử trực quan trên giao diện `ui.py`.
- **Thời điểm đã tự nộp URL repo chung trên VLearn:** Đã nộp URL repository `https://github.com/chinhzz108/K4-L3B-Day04-Prompt-Engineering-Tool-Calling-Labs` trên VLearn trước deadline quy định.
