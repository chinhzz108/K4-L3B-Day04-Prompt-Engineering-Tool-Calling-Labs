---
name: check_device_warranty
track: bonus
kind: local_status
provider: local_mock
requires_env: []
inputs: [asset_id]
outputs: [asset_id, manufacturer, model, warranty_until, warranty_status, days_remaining, sla_tier, replacement_eligible]
side_effect: false
requires_confirmation: false
---

# check_device_warranty

Tra cứu tình trạng bảo hành phần cứng và thời hạn hợp đồng hỗ trợ kỹ thuật theo mã tài sản (`asset_id`).
Dùng khi người dùng hỏi về thời hạn bảo hành, hợp đồng dịch vụ SLA của nhà sản xuất, hoặc kiểm tra điều kiện đổi trả/thay thế phần cứng cho máy tính laptop, desktop hoặc máy in.
