#!/usr/bin/env python3
"""flow-state.py - 管理 SDD-TDD 开发流程的状态文件

用法：
    python flow-state.py init <task_name>
    python flow-state.py advance
    python flow-state.py update <field> <value>
    python flow-state.py show
    python flow-state.py check-phase <phase_number>

仅依赖 Python 3 标准库，跨平台（Windows/PowerShell、Linux、macOS）。
"""

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
STATE_FILE = STATE_DIR / ".dev-flow-state.json"
LAST_PHASE = 5  # Phase 5 (Archive) 是最后阶段


def get_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_state() -> dict:
    if not STATE_FILE.exists():
        print(f"错误：状态文件不存在 {STATE_FILE}", file=sys.stderr)
        print("请先运行：python flow-state.py init <task_name>", file=sys.stderr)
        sys.exit(1)
    with STATE_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def write_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    tmp.replace(STATE_FILE)


def init_state(task_name: str) -> None:
    if STATE_FILE.exists():
        print(f"警告：状态文件已存在 {STATE_FILE}")
        print(f"如需重新开始，请先删除：删除 {STATE_FILE}")
        sys.exit(1)

    ts = get_timestamp()
    state = {
        "task": task_name,
        "route": "full",
        "current_phase": 1,
        "phases_done": [],
        "base_commit": "",
        "explore_path": f"{STATE_DIR.name}/explore_report.md",
        "explore_path": f"{STATE_DIR.name}/explore_report.md",
        "proposal_path": f"{STATE_DIR.name}/proposal.md",
        "apply_log_path": f"{STATE_DIR.name}/apply_log.md",
        "review_report_path": f"{STATE_DIR.name}/review_report.md",
        "specs_total": 0,
        "specs_done": 0,
        "review_findings": {"error": 0, "warn": 0, "info": 0},
        "must_fix_total": 0,
        "must_fix_done": 0,
        "review_round": 0,
        "archive_path": "",
        "started_at": ts,
        "updated_at": ts,
    }
    write_state(state)
    print(f"✓ 已初始化状态：{STATE_FILE}")
    print(f"  任务：{task_name}")
    print("  当前阶段：Phase 1 (Explore)")


def advance_phase() -> None:
    state = read_state()
    current = state["current_phase"]
    ts = get_timestamp()
    new_phase = current + 1

    # 推进前把当前阶段记入 phases_done
    done = list(state.get("phases_done", []))
    if current not in done:
        done.append(current)

    if new_phase > LAST_PHASE:
        print(f"✓ 流程已完成（Phase {LAST_PHASE}: Archive 是最后一步）")
        state["phases_done"] = done
        state["updated_at"] = ts
        write_state(state)
        return

    state["current_phase"] = new_phase
    state["phases_done"] = done
    state["updated_at"] = ts
    write_state(state)
    print(f"✓ 已推进到 Phase {new_phase}")
    print(f"  已完成阶段：{', '.join(str(p) for p in done)}")


def update_field(field: str, value: str) -> None:
    state = read_state()
    ts = get_timestamp()

    # 尝试把 value 转成数字/布尔，否则保留字符串
    parsed: object = value
    if value.lstrip("-").isdigit():
        parsed = int(value)
    elif value in ("true", "false"):
        parsed = value == "true"

    # review_findings 等嵌套字段用点号路径，如 review_findings.error
    if "." in field:
        parts = field.split(".")
        node = state
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = parsed
    else:
        state[field] = parsed

    state["updated_at"] = ts
    write_state(state)
    print(f"✓ 已更新：{field} = {parsed}")


def show_state() -> None:
    if not STATE_FILE.exists():
        print(f"状态文件不存在：{STATE_FILE}")
        return
    state = read_state()
    phases_done = ", ".join(str(p) for p in state.get("phases_done", [])) or "无"
    rf = state.get("review_findings", {})
    print("SDD-TDD 流程状态")
    print("================")
    print(f"任务：{state.get('task')}")
    print(f"当前阶段：Phase {state.get('current_phase')}")
    print(f"已完成阶段：{phases_done}")
    print(f"规格进度：{state.get('specs_done')} / {state.get('specs_total')} specs")
    print(f"必须修复：{state.get('must_fix_done')} / {state.get('must_fix_total')} completed")
    print(f"Review 轮次：{state.get('review_round')}")
    print(f"Review 发现：error={rf.get('error')}, warn={rf.get('warn')}, info={rf.get('info')}")
    print(f"开始时间：{state.get('started_at')}")
    print(f"最后更新：{state.get('updated_at')}")
    print(f"状态文件：{STATE_FILE}")


def check_phase(target: int) -> None:
    """供 agent 脚本判断阶段状态：active/done/pending"""
    if not STATE_FILE.exists():
        print("error")
        sys.exit(1)
    state = read_state()
    current = state["current_phase"]
    if current == target:
        print("active")
    elif current > target:
        print("done")
    else:
        print("pending")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="flow-state.py",
        description="SDD-TDD 流程状态管理工具",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="初始化新流程")
    p_init.add_argument("task_name")

    sub.add_parser("advance", help="推进到下一阶段")

    p_update = sub.add_parser("update", help="更新状态字段（支持点号路径如 review_findings.error）")
    p_update.add_argument("field")
    p_update.add_argument("value")

    sub.add_parser("show", help="显示当前状态")

    p_check = sub.add_parser("check-phase", help="检查阶段状态（active/done/pending）")
    p_check.add_argument("phase_number", type=int)

    args = parser.parse_args()
    if args.cmd == "init":
        init_state(args.task_name)
    elif args.cmd == "advance":
        advance_phase()
    elif args.cmd == "update":
        update_field(args.field, args.value)
    elif args.cmd == "show":
        show_state()
    elif args.cmd == "check-phase":
        check_phase(args.phase_number)


if __name__ == "__main__":
    main()
