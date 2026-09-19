from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from tools._shared import ROOT, err

ASSETS_FILE = ROOT / "helpdesk_data" / "assets.json"


def check_device_warranty(asset_id: str = "") -> dict[str, Any]:
    """Tra cứu tình trạng bảo hành và hợp đồng dịch vụ SLA của thiết bị phần cứng."""
    try:
        norm_id = (asset_id or "").strip().upper()
        if not norm_id:
            return {
                "tool": "check_device_warranty",
                "error": "missing_asset_id",
                "message": "Asset ID is required to check warranty status.",
            }

        data = json.loads(ASSETS_FILE.read_text(encoding="utf-8"))
        for item in data.get("assets", []):
            if item["asset_id"].strip().upper() == norm_id:
                warranty_until = item.get("warranty_until", "")
                is_active = False
                days_remaining = 0
                if warranty_until:
                    try:
                        exp_date = datetime.strptime(warranty_until, "%Y-%m-%d").date()
                        now_date = datetime.now().date()
                        days_remaining = (exp_date - now_date).days
                        is_active = days_remaining > 0
                    except Exception:
                        pass

                sla_tier = "Standard Next-Business-Day (NBD)" if item.get("type") == "laptop" else "Critical 4-Hour On-Site"
                return {
                    "tool": "check_device_warranty",
                    "asset_id": item["asset_id"],
                    "manufacturer": item.get("manufacturer"),
                    "model": item.get("model"),
                    "warranty_until": warranty_until,
                    "warranty_status": "active" if is_active else "expired",
                    "days_remaining": max(0, days_remaining),
                    "sla_tier": sla_tier,
                    "service_provider": f"{item.get('manufacturer')} Enterprise Support Care",
                    "replacement_eligible": is_active,
                }

        return {
            "tool": "check_device_warranty",
            "asset_id": norm_id,
            "error": "not_found",
            "message": f"Asset {norm_id} not found in inventory.",
        }
    except Exception as exc:
        return err("check_device_warranty", exc)
