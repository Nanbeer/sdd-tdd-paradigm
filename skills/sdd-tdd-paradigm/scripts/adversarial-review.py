#!/usr/bin/env python3
"""adversarial-review.py - 对抗验证编排脚本

收集多个审查子 agent 的 review-*.json，识别：
    1. 多证据确认的 finding（>= 2 个不同 agent 对同一文件报告 ERROR）
    2. 单 agent 的 ERROR finding（需要对抗验证/反驳）
    3. 汇总分类结果

输入：.sdd-tdd/ 下的 review-*.json 文件
输出：.sdd-tdd/review_summary.json

用法：
    python adversarial-review.py collect <review_dir>
    python adversarial-review.py show-pending
    python adversarial-review.py record-refutation <finding_id> <refuted|confirmed|uncertain> <理由>

仅依赖 Python 3 标准库，跨平台。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows 默认 stdout 编码（GBK）无法打印 ✓ 等字符，强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

STATE_DIR = Path(".sdd-tdd")
SUMMARY_FILE = STATE_DIR / "review_summary.json"


def get_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def collect_findings(review_dir: Path) -> None:
    if not review_dir.exists():
        print(f"错误：Review 目录不存在 {review_dir}", file=sys.stderr)
        sys.exit(1)

    review_files = sorted(review_dir.glob("review-*.json"))
    if not review_files:
        print(f"警告：未找到 review-*.json 文件于 {review_dir}")
        return

    all_findings: list[dict] = []
    err_count = warn_count = info_count = 0

    for rf in review_files:
        try:
            data = json.loads(rf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"警告：跳过无法解析的文件 {rf}: {e}", file=sys.stderr)
            continue
        agent = data.get("agent", "unknown")
        for f in data.get("findings", []):
            f = dict(f)
            f["source_agent"] = agent
            all_findings.append(f)
            sev = f.get("severity", "INFO")
            if sev == "ERROR":
                err_count += 1
            elif sev == "WARN":
                warn_count += 1
            else:
                info_count += 1

    # 按 file 分组找多证据确认：同一 file 下 >=2 个不同 agent 的 ERROR
    # （不再要求 file:line 精确匹配，因为不同 agent 引用同一 bug 时行范围常不同）
    file_err_agents: dict[str, set[str]] = {}
    file_err_findings: dict[str, list[dict]] = {}
    for f in all_findings:
        if f.get("severity") != "ERROR":
            continue
        key = f.get("file", "")
        if key not in file_err_agents:
            file_err_agents[key] = set()
            file_err_findings[key] = []
        file_err_agents[key].add(f.get("source_agent", "unknown"))
        file_err_findings[key].append(f)

    multi_evidence = []
    needs_refutation = []
    seen_ids: set[str] = set()
    for f in all_findings:
        if f.get("severity") != "ERROR":
            continue
        fid = f.get("id", "")
        if fid in seen_ids:
            continue
        seen_ids.add(fid)
        key = f.get("file", "")
        agent_count = len(file_err_agents.get(key, set()))
        if agent_count >= 2:
            entry = dict(f)
            entry["verdict"] = "must_fix_multi_evidence"
            entry["confirming_agents"] = sorted(file_err_agents.get(key, set()))
            multi_evidence.append(entry)
        else:
            entry = dict(f)
            entry["verdict"] = "needs_refutation"
            needs_refutation.append(entry)

    ts = get_timestamp()
    summary = {
        "findings": all_findings,
        "multi_evidence_confirmed": multi_evidence,
        "needs_refutation": needs_refutation,
        "summary": {
            "total": len(all_findings),
            "error": err_count,
            "warn": warn_count,
            "info": info_count,
            "multi_evidence_count": len(multi_evidence),
            "needs_refutation_count": len(needs_refutation),
            "refuted": 0,
            "confirmed": 0,
            "uncertain": 0,
        },
        "generated_at": ts,
    }

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"✓ 已生成 Review 汇总：{SUMMARY_FILE}")
    print()
    print("Findings 统计:")
    print(f"  总数: {summary['summary']['total']}")
    print(f"  ERROR: {err_count}")
    print(f"  WARN: {warn_count}")
    print(f"  INFO: {info_count}")
    print()
    print("分类:")
    print(f"  多证据确认（必改）: {summary['summary']['multi_evidence_count']}")
    print(f"  需对抗验证: {summary['summary']['needs_refutation_count']}")


def show_pending() -> None:
    if not SUMMARY_FILE.exists():
        print(f"错误：汇总文件不存在 {SUMMARY_FILE}", file=sys.stderr)
        print(f"请先运行：python adversarial-review.py collect <review_dir>", file=sys.stderr)
        sys.exit(1)
    data = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
    pending = data.get("needs_refutation", [])
    print(f"待对抗验证的 findings: {len(pending)}")
    print("=======================")
    print()
    for f in pending:
        # 已记录反驳结果的跳过
        if "refutation_verdict" in f:
            continue
        print(f"Finding: {f.get('id')} [{f.get('severity')}]")
        print(f"位置: {f.get('file')}:{f.get('line')}")
        print(f"问题: {f.get('issue')}")
        print(f"证据: {f.get('evidence')}")
        print()


def record_refutation(finding_id: str, verdict: str, reason: str) -> None:
    if verdict not in ("refuted", "confirmed", "uncertain"):
        print("错误：verdict 必须是 refuted|confirmed|uncertain", file=sys.stderr)
        sys.exit(1)
    if not SUMMARY_FILE.exists():
        print(f"错误：汇总文件不存在 {SUMMARY_FILE}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
    ts = get_timestamp()

    found = False
    for f in data.get("needs_refutation", []):
        if f.get("id") == finding_id:
            f["refutation_verdict"] = verdict
            f["refutation_reason"] = reason
            f["refuted_at"] = ts
            found = True
            break

    if not found:
        print(f"错误：未找到 finding ID {finding_id}", file=sys.stderr)
        sys.exit(1)

    # 重算统计
    refuted = sum(
        1 for f in data["needs_refutation"] if f.get("refutation_verdict") == "refuted"
    )
    confirmed = sum(
        1 for f in data["needs_refutation"] if f.get("refutation_verdict") == "confirmed"
    )
    uncertain = sum(
        1 for f in data["needs_refutation"] if f.get("refutation_verdict") == "uncertain"
    )
    data["summary"]["refuted"] = refuted
    data["summary"]["confirmed"] = confirmed
    data["summary"]["uncertain"] = uncertain

    SUMMARY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✓ {finding_id} marked as {verdict}")
    print(f"  原因: {reason}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="adversarial-review.py",
        description="SDD-TDD 对抗验证编排工具",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_collect = sub.add_parser("collect", help="收集 review-*.json 并生成汇总")
    p_collect.add_argument("review_dir")

    sub.add_parser("show-pending", help="显示待反驳的 findings")

    p_record = sub.add_parser("record-refutation", help="记录反驳结果")
    p_record.add_argument("finding_id")
    p_record.add_argument("verdict", choices=["refuted", "confirmed", "uncertain"])
    p_record.add_argument("reason")

    args = parser.parse_args()
    if args.cmd == "collect":
        collect_findings(Path(args.review_dir))
    elif args.cmd == "show-pending":
        show_pending()
    elif args.cmd == "record-refutation":
        record_refutation(args.finding_id, args.verdict, args.reason)


if __name__ == "__main__":
    main()
