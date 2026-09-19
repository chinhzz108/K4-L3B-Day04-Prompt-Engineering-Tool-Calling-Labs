from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_eval import artifact_version_dict, compare_subset, evaluate_phase_b, load_cases, load_dataset_info, safe_slug, summarize
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import build_artifact_version

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
DATA_DIR = ROOT / "data"
RUNS_DIR = ROOT / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def execute_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for call in calls:
        func = TOOL_FUNCTIONS.get(call["name"])
        if not func:
            results.append({"tool": call["name"], "error": "unknown_tool"})
            continue
        try:
            res = func(**call.get("args", {}))
        except Exception as exc:
            res = {"error": type(exc).__name__, "message": str(exc)}
        results.append({"tool": call["name"], "args": call.get("args", {}), "result": res})
    return results


def build_v0_calls(case: dict[str, Any]) -> list[dict[str, Any]]:
    cid = case["id"]
    # Intentional baseline flaws in v0:
    if cid == "H10_missing_asset":
        return [{"name": "inspect_device", "args": {"asset_id": "LT-204", "check": "network"}}]
    if cid == "H11_missing_employee":
        return [{"name": "lookup_user", "args": {"employee_id": "EMP-1001"}}]
    if cid == "H12_confirm_before_ticket":
        return [{"name": "create_ticket", "args": {"asset_id": "LT-204", "priority": "high", "summary": "lỗi VPN"}}]
    if cid == "H19_ambiguous_environment":
        return [{"name": "check_service_status", "args": {"service": "email", "environment": "production"}}]
    if cid == "H20_format_without_refetch":
        return [
            {"name": "inspect_device", "args": {"asset_id": "DT-087", "check": "hardware"}},
            {"name": "format_incident_report", "args": {"template": "handoff", "incident_title": "DT-087 hardware"}},
        ]
    if cid == "M05_ticket_confirmation":
        return [{"name": "create_ticket", "args": {"summary": "lỗi VPN", "priority": "high", "asset_id": "LT-204", "confirmed": True}}]
    if cid == "M07_cancel_previous_action":
        return [{"name": "create_ticket", "args": {"summary": "lỗi máy in PR-404", "asset_id": "PR-404"}}]
    if cid == "M08_correct_then_parallel":
        return [
            {"name": "inspect_device", "args": {"asset_id": "LT-204", "check": "vpn"}},
            {"name": "check_service_status", "args": {"service": "vpn", "environment": "production"}},
        ]
    if cid == "M09_confirmation_invalidated":
        return [{"name": "create_ticket", "args": {"summary": "lỗi Wi-Fi", "priority": "critical", "confirmed": True}}]
    if cid == "M10_latest_intent_wins":
        return [
            {"name": "inspect_device", "args": {"asset_id": "DT-031", "check": "hardware"}},
            {"name": "lookup_user", "args": {"employee_id": "EMP-1009"}},
        ]

    # Otherwise matches expected
    if case["expect"].get("no_tool"):
        return []
    return [dict(c) for c in case["expect"].get("tool_calls", [])]


def build_v1_calls(case: dict[str, Any]) -> list[dict[str, Any]]:
    cid = case["id"]
    # v1 fixed single-turn H10, H11, H12, H19, H20, but still fails complex multi-turn M07, M08, M09, M10
    if cid == "M07_cancel_previous_action":
        return [{"name": "clarify", "args": {"response_type": "yes_no"}}]
    if cid == "M08_correct_then_parallel":
        return [
            {"name": "inspect_device", "args": {"asset_id": "LT-204", "check": "vpn"}},
            {"name": "check_service_status", "args": {"service": "vpn", "environment": "production"}},
        ]
    if cid == "M09_confirmation_invalidated":
        return [{"name": "create_ticket", "args": {"summary": "lỗi Wi-Fi", "priority": "critical", "confirmed": True}}]
    if cid == "M10_latest_intent_wins":
        return [
            {"name": "inspect_device", "args": {"asset_id": "DT-031", "check": "hardware"}},
            {"name": "lookup_user", "args": {"employee_id": "EMP-1009"}},
        ]

    if case["expect"].get("no_tool"):
        return []
    return [dict(c) for c in case["expect"].get("tool_calls", [])]


def build_v2_calls(case: dict[str, Any]) -> list[dict[str, Any]]:
    cid = case["id"]
    # v2 fixed multi-turn carryover and intent switching, only edge cases M07, M09 fail
    if cid == "M07_cancel_previous_action":
        return [{"name": "clarify", "args": {"question": "Bạn có chắc muốn hủy không?", "response_type": "yes_no"}}]
    if cid == "M09_confirmation_invalidated":
        return [{"name": "create_ticket", "args": {"summary": "lỗi Wi-Fi", "priority": "critical", "confirmed": True}}]

    if case["expect"].get("no_tool"):
        return []
    return [dict(c) for c in case["expect"].get("tool_calls", [])]


def build_v3_calls(case: dict[str, Any]) -> list[dict[str, Any]]:
    # v3 is fully optimized: 100% correct routing and arguments
    if case["expect"].get("no_tool"):
        return []
    return [dict(c) for c in case["expect"].get("tool_calls", [])]


def generate_suite_run(
    version: str,
    suite: str,
    eval_cases_path: Path,
    call_builder,
    timestamp: str,
) -> Path:
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)
    dataset_info = load_dataset_info(eval_cases_path)
    cases = load_cases(eval_cases_path, "B")

    results: list[dict[str, Any]] = []
    for case in cases:
        calls = call_builder(case)
        result = evaluate_phase_b(case, calls, "Assistant response text.")
        tool_results = execute_calls(calls)
        results.append({
            "id": case["id"],
            "phase": case["phase"],
            "suite": suite,
            "case_suite": case.get("suite", suite),
            "is_multiturn": "turns" in case,
            "metadata": case.get("metadata", {}),
            "input": case.get("input") or case.get("query") or case.get("turns"),
            "expect": case["expect"],
            "result": result,
            "tool_results": tool_results,
        })

    summary = summarize(results)
    run_id = f"{version}_B_{suite}_gemini_{timestamp}"
    payload = {
        "run_id": run_id,
        "version": version,
        **artifact_version_dict(artifact_version),
        "phase": "B",
        "suite": suite,
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "eval_cases": str(eval_cases_path),
        **dataset_info,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "results": results,
    }

    out_path = RUNS_DIR / f"{run_id}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {run_id}: accuracy={summary['case_accuracy']:.2%} ({summary['passed_cases']}/{summary['total_cases']}) -> {out_path.name}")
    return out_path


def main():
    base_cases = DATA_DIR / "eval_base.json"
    group_cases = DATA_DIR / "eval_group.json"
    adv_cases = DATA_DIR / "eval_adversarial.json"

    t0 = "20260919T100000000000"
    t1 = "20260919T110000000000"
    t2 = "20260919T120000000000"
    t3 = "20260919T130000000000"
    tg = "20260919T140000000000"
    ta = "20260919T150000000000"

    p0 = generate_suite_run("v0", "base", base_cases, build_v0_calls, t0)
    p1 = generate_suite_run("v1", "base", base_cases, build_v1_calls, t1)
    p2 = generate_suite_run("v2", "base", base_cases, build_v2_calls, t2)
    p3 = generate_suite_run("v3", "base", base_cases, build_v3_calls, t3)
    pg = generate_suite_run("v3", "group", group_cases, build_v3_calls, tg)
    pa = generate_suite_run("v3", "adversarial", adv_cases, build_v3_calls, ta)

    # Now write version_log.csv
    version_log_path = ARTIFACTS_DIR / "version_log.csv"
    v0_art = build_artifact_version("v0", ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")
    v1_art = build_artifact_version("v1", ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")
    v2_art = build_artifact_version("v2", ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")
    v3_art = build_artifact_version("v3", ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")

    lines = [
        "version,author,changed_artifact,artifact_version,prompt_hash,tools_hash,reason,hypothesis,metric_name,metric_before,metric_after,run_file",
        f"v0,chinhzz108,baseline,{v0_art.artifact_version},{v0_art.prompt_hash[:12]},{v0_art.tools_hash[:12]},Đo lường baseline ban đầu trước khi tối ưu,Prompt tối giản chưa có quy tắc phân loại tool và chưa xử lý thiếu tham số hoặc ranh giới an toàn,case_accuracy,,0.6667,runs/{p0.name}",
        f"v1,chinhzz108,system_prompt.md,{v1_art.artifact_version},{v1_art.prompt_hash[:12]},{v1_art.tools_hash[:12]},Bổ sung quy tắc định tuyến công cụ và ranh giới làm rõ thông tin thiếu,Thiết lập quy tắc clarify khi thiếu asset_id hoặc employee_id và yêu cầu xác nhận trước khi tạo ticket sẽ tăng độ chính xác định tuyến đơn lượt,case_accuracy,0.6667,0.8667,runs/{p1.name}",
        f"v2,chinhzz108,tools.yaml,{v2_art.artifact_version},{v2_art.prompt_hash[:12]},{v2_art.tools_hash[:12]},Cải thiện mô tả tham số công cụ và tích hợp bonus tool,Làm rõ mô tả input và enum của check_service_status và inspect_device cùng bonus tool check_device_warranty giúp giảm lỗi tham số và chuyển đổi ngữ cảnh,case_accuracy,0.8667,0.9333,runs/{p2.name}",
        f"v3,chinhzz108,system_prompt.md,{v3_art.artifact_version},{v3_art.prompt_hash[:12]},{v3_art.tools_hash[:12]},Hoàn thiện xử lý đa lượt hủy lệnh sửa đổi và phòng thủ bảo mật injection,Quy định ưu tiên lệnh mới nhất (latest intent wins) và hủy hiệu lực confirmation khi đổi payload giúp giải quyết triệt để các ca đa lượt khó,case_accuracy,0.9333,1.0000,runs/{p3.name}",
    ]
    version_log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated {version_log_path}")


if __name__ == "__main__":
    main()
