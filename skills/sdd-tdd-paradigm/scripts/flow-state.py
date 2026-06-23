#!/usr/bin/env python3
"""flow-state.py - 管理 SDD-TDD 开发流程的状态文件

用法：
    python flow-state.py init <task_name>
    python flow-state.py advance
    python flow-state.py update <field> <value>
    python flow-state.py show
    python flow-state.py check-phase <phase_number>
    python flow-state.py grill-complete <phase_number>
    python flow-state.py iron-check <rule_id> pass|fail "<reason>"
    python flow-state.py sync-gate <gate_id> pass|fail <fail_count>
    python flow-state.py verify-record <task_name> pass|fail "<details>"
    python flow-state.py interrupt-pause
    python flow-state.py interrupt-resume

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
        # v2.0 新增字段（向后兼容：旧文件读取时 .get() 取默认值）
        "grilling": {
            "phase1_complete": False,
            "phase2_complete": False,
            "phase1_issues": [],
            "phase2_issues": [],
            "unresolved": [],
        },
        "iron_rules": {
            "r0_compliance": True,
            "r1_to_r5_checks": {},
            "violations": [],
        },
        "sync_gates": {
            "gate_2_to_3": {"passed": False, "fails": 0, "checked_at": ""},
            "gate_3_to_4": {"passed": False, "fails": 0, "checked_at": ""},
            "gate_4_to_5": {"passed": False, "fails": 0, "checked_at": ""},
        },
        "verification": {
            "high_risk_tasks": [],
            "failures": [],
            "last_verification": "",
        },
        "interruption": {
            "paused_at": "",
            "stashed": False,
            "tbd_action": "",
        },
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
    print(f"路径：{state.get('route', 'full')}")
    print(f"当前阶段：Phase {state.get('current_phase')}")
    print(f"已完成阶段：{phases_done}")
    print(f"规格进度：{state.get('specs_done')} / {state.get('specs_total')} specs")
    print(f"必须修复：{state.get('must_fix_done')} / {state.get('must_fix_total')} completed")
    print(f"Review 轮次：{state.get('review_round')}")
    print(f"Review 发现：error={rf.get('error')}, warn={rf.get('warn')}, info={rf.get('info')}")

    # v2.0 新增状态显示
    gr = state.get("grilling")
    if gr:
        p1 = "✓" if gr.get("phase1_complete") else "✗"
        p2 = "✓" if gr.get("phase2_complete") else "✗"
        unresolved = len(gr.get("unresolved", []))
        print(f"Grilling：P1={p1} P2={p2} 悬留={unresolved}")

    ir = state.get("iron_rules")
    if ir:
        violations = len(ir.get("violations", []))
        status = "✓ 无违规" if violations == 0 else f"⚠ {violations} 项违规"
        print(f"铁律合规：{status}")

    sg = state.get("sync_gates")
    if sg:
        gates_ok = sum(1 for g in sg.values() if isinstance(g, dict) and g.get("passed"))
        print(f"同步 Gate：{gates_ok}/3 通过")

    vf = state.get("verification")
    if vf:
        high_risk = len(vf.get("high_risk_tasks", []))
        fails = len(vf.get("failures", []))
        print(f"核验：{high_risk} 高风险任务, {fails} 失败")

    intr = state.get("interruption")
    if intr and intr.get("paused_at"):
        print(f"中断状态：暂停于 {intr['paused_at']}")

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


# ── v2.0 新增子命令 ──────────────────────────────────────────────


def grill_complete(phase: int) -> None:
    """标记 Grilling 阶段完成"""
    if phase not in (1, 2):
        print(f"错误：Grilling 阶段只能是 1 或 2，收到 {phase}", file=sys.stderr)
        sys.exit(1)
    state = read_state()
    ts = get_timestamp()
    gr = state.setdefault("grilling", {})
    key = f"phase{phase}_complete"
    gr[key] = True
    state["updated_at"] = ts
    write_state(state)
    print(f"✓ Grilling Phase {phase} 已标记为完成")


def iron_check(rule_id: str, result: str, reason: str = "") -> None:
    """记录铁律合规检查"""
    if result not in ("pass", "fail"):
        print(f"错误：结果必须是 pass 或 fail，收到 {result}", file=sys.stderr)
        sys.exit(1)
    state = read_state()
    ts = get_timestamp()
    ir = state.setdefault("iron_rules", {})
    checks = ir.setdefault("r1_to_r5_checks", {})
    checks[rule_id] = {"result": result, "reason": reason, "checked_at": ts}
    if result == "fail":
        violations = ir.setdefault("violations", [])
        violations.append({"rule": rule_id, "reason": reason, "at": ts})
    state["updated_at"] = ts
    write_state(state)
    status = "✓ PASS" if result == "pass" else "⚠ FAIL"
    print(f"{status} 铁律 {rule_id}: {reason}" if reason else f"{status} 铁律 {rule_id}")


def sync_gate(gate_id: str, result: str, fail_count: int = 0) -> None:
    """记录文档同步 Gate 结果"""
    valid_gates = ("gate_2_to_3", "gate_3_to_4", "gate_4_to_5")
    if gate_id not in valid_gates:
        print(f"错误：无效的 Gate ID '{gate_id}'，有效值：{', '.join(valid_gates)}", file=sys.stderr)
        sys.exit(1)
    if result not in ("pass", "fail"):
        print(f"错误：结果必须是 pass 或 fail，收到 {result}", file=sys.stderr)
        sys.exit(1)
    state = read_state()
    ts = get_timestamp()
    sg = state.setdefault("sync_gates", {})
    sg[gate_id] = {"passed": result == "pass", "fails": fail_count, "checked_at": ts}
    state["updated_at"] = ts
    write_state(state)
    status = "✓ PASS" if result == "pass" else "⚠ FAIL"
    print(f"{status} 同步 Gate '{gate_id}' (失败项: {fail_count})")


def verify_record(task_name: str, result: str, details: str = "") -> None:
    """记录高风险任务核验结果"""
    if result not in ("pass", "fail"):
        print(f"错误：结果必须是 pass 或 fail，收到 {result}", file=sys.stderr)
        sys.exit(1)
    state = read_state()
    ts = get_timestamp()
    vf = state.setdefault("verification", {})
    high_risk = vf.setdefault("high_risk_tasks", [])
    high_risk.append({"task": task_name, "result": result, "details": details, "verified_at": ts})
    if result == "fail":
        failures = vf.setdefault("failures", [])
        failures.append({"task": task_name, "details": details, "at": ts})
    vf["last_verification"] = ts
    state["updated_at"] = ts
    write_state(state)
    status = "✓ PASS" if result == "pass" else "⚠ FAIL"
    print(f"{status} 核验任务 '{task_name}': {details}" if details else f"{status} 核验任务 '{task_name}'")


def interrupt_pause() -> None:
    """记录流程中断（用户中途追加意见等）"""
    state = read_state()
    ts = get_timestamp()
    intr = state.setdefault("interruption", {})
    intr["paused_at"] = ts
    state["updated_at"] = ts
    write_state(state)
    print(f"✓ 流程已暂停于 {ts}")
    print("  用户确认后运行 interrupt-resume 清除中断状态")


def interrupt_resume() -> None:
    """清除中断状态，继续流程"""
    state = read_state()
    ts = get_timestamp()
    intr = state.setdefault("interruption", {})
    intr["paused_at"] = ""
    intr["stashed"] = False
    intr["tbd_action"] = ""
    state["updated_at"] = ts
    write_state(state)
    print(f"✓ 中断状态已清除，流程可继续")


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

    # v2.0 新增子命令
    p_grill = sub.add_parser("grill-complete", help="标记 Grilling 阶段完成")
    p_grill.add_argument("phase_number", type=int, choices=[1, 2])

    p_iron = sub.add_parser("iron-check", help="记录铁律合规检查")
    p_iron.add_argument("rule_id")
    p_iron.add_argument("result", choices=["pass", "fail"])
    p_iron.add_argument("reason", nargs="?", default="")

    p_sync = sub.add_parser("sync-gate", help="记录文档同步 Gate 结果")
    p_sync.add_argument("gate_id", choices=["gate_2_to_3", "gate_3_to_4", "gate_4_to_5"])
    p_sync.add_argument("result", choices=["pass", "fail"])
    p_sync.add_argument("fail_count", type=int, nargs="?", default=0)

    p_verify = sub.add_parser("verify-record", help="记录高风险任务核验结果")
    p_verify.add_argument("task_name")
    p_verify.add_argument("result", choices=["pass", "fail"])
    p_verify.add_argument("details", nargs="?", default="")

    sub.add_parser("interrupt-pause", help="记录流程中断")
    sub.add_parser("interrupt-resume", help="清除中断状态")

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
    elif args.cmd == "grill-complete":
        grill_complete(args.phase_number)
    elif args.cmd == "iron-check":
        iron_check(args.rule_id, args.result, args.reason)
    elif args.cmd == "sync-gate":
        sync_gate(args.gate_id, args.result, args.fail_count)
    elif args.cmd == "verify-record":
        verify_record(args.task_name, args.result, args.details)
    elif args.cmd == "interrupt-pause":
        interrupt_pause()
    elif args.cmd == "interrupt-resume":
        interrupt_resume()


if __name__ == "__main__":
    main()
