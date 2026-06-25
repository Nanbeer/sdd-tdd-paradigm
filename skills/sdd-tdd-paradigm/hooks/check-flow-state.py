#!/usr/bin/env python3
"""check-flow-state.py — SessionStart Hook：检测 SDD-TDD 流程状态

在 Claude Code SessionStart 时运行，检查项目目录下是否存在
.sdd-tdd/.dev-flow-state.json，若存在则输出状态摘要。

用法（在 settings.json hooks 中配置）:
  "SessionStart": [{
    "matcher": "",
    "hooks": [{
      "type": "command",
      "command": "python .claude/skills/sdd-tdd-paradigm/hooks/check-flow-state.py"
    }]
  }]

或者作为独立工具使用:
  python check-flow-state.py [项目根目录]
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Windows 默认 stdout 编码（GBK）无法打印 ✓ 等字符，强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

STATE_FILE_NAME = ".sdd-tdd/.dev-flow-state.json"

PHASE_NAMES = {
    1: "Explore（探索）",
    2: "Proposal（方案）",
    3: "Apply（TDD 实现）",
    4: "Review（多 Agent 审查）",
    5: "Archive（归档）",
}


def find_state_file(project_root: Path) -> Optional[Path]:
    """在项目根目录下查找状态文件"""
    path = project_root / STATE_FILE_NAME
    return path if path.exists() else None


def format_elapsed(iso8601: str) -> str:
    """计算从给定时间到现在的间隔"""
    try:
        start = datetime.fromisoformat(iso8601.replace("Z", "+00:00"))
        elapsed = datetime.now(timezone.utc) - start
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        if hours > 0:
            return f"{hours} 小时 {minutes} 分钟前"
        elif minutes > 0:
            return f"{minutes} 分钟前"
        else:
            return "刚刚"
    except (ValueError, TypeError):
        return "未知时间"


def main() -> None:
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    state_file = find_state_file(project_root)

    if not state_file:
        # 无 SDD-TDD 流程活跃，安静跳过
        sys.exit(0)

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print("[SDD-TDD] ⚠ 状态文件损坏，无法读取")
        sys.exit(0)

    task = state.get("task", "未知任务")
    phase = state.get("current_phase", 1)
    phase_name = PHASE_NAMES.get(phase, f"Phase {phase}")
    specs_done = state.get("specs_done", 0)
    specs_total = state.get("specs_total", 0)
    grilling = state.get("grilling", {})
    interrupted = state.get("interruption", {}).get("paused_at", "")

    spec_progress = f"{specs_done}/{specs_total}" if specs_total else "N/A"
    grill_p1 = "✓" if grilling.get("phase1_complete") else "✗"
    grill_p2 = "✓" if grilling.get("phase2_complete") else "✗"
    elapsed = format_elapsed(state.get("updated_at", ""))

    # 输出状态摘要（会被注入到系统上下文）
    lines = [
        "",
        "╔══════════════════════════════════════════════════════════╗",
        "║  SDD-TDD 流程活跃 — 上次更新: " + elapsed.ljust(27) + "║",
        "╠══════════════════════════════════════════════════════════╣",
        f"║  任务:   {task[:40].ljust(40)}║",
        f"║  阶段:   Phase {phase} — {phase_name.ljust(30)}║",
        f"║  Grilling: P1={grill_p1}  P2={grill_p2}    Spec 进度: {spec_progress.ljust(10)}║",
    ]

    if interrupted:
        lines.append(f"║  ⚠ 流程已暂停，需用户决策后 resume                          ║")

    lines.append("╚══════════════════════════════════════════════════════════╝")
    lines.append("")

    print("\n".join(lines))

    # 如果有未解决的 grilling 问题，提醒
    unresolved = grilling.get("unresolved", [])
    if unresolved:
        print(f"[SDD-TDD] ⚠ {len(unresolved)} 个 Grilling 悬留问题待解决")

    sys.exit(0)


if __name__ == "__main__":
    main()
