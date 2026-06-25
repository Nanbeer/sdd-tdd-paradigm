#!/usr/bin/env python3
"""phase-guard.py — PreToolUse Hook：SDD-TDD 阶段门禁

在每次 Edit/Write 等修改类工具调用前运行，检查当前 SDD-TDD 阶段
是否允许此操作。违规时输出警告（不阻塞），提醒对应的铁律编号。

用法（在 settings.json hooks 中配置）:
  "PreToolUse": [{
    "matcher": "Edit|Write",
    "hooks": [{
      "type": "command",
      "command": "python .claude/skills/sdd-tdd-paradigm/hooks/phase-guard.py \"$TOOL_NAME\" \"$FILE_PATH\""
    }]
  }]

环境变量（由 Claude Code 注入）:
  CLAUDE_PROJECT_DIR — 项目根目录
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

# Windows 默认 stdout 编码（GBK）无法打印特殊字符，强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

STATE_FILE_NAME = ".sdd-tdd/.dev-flow-state.json"
SDD_TDD_DIR = ".sdd-tdd"

# 每个阶段允许的操作
PHASE_PERMISSIONS = {
    1: {  # Explore: 只读
        "allow_tools": {"Read", "Glob", "Grep", "Bash", "Agent"},
        "allow_paths": [],
        "rule": "R1 — 事实先于讨论。Explore 阶段只能读代码，不能修改。",
    },
    2: {  # Proposal: 只写 proposal.md
        "allow_tools": {"Read", "Glob", "Grep", "Bash", "Agent", "Write", "Edit"},
        "allow_paths": [".sdd-tdd/"],
        "rule": "R2 — 场景先于代码。Proposal 阶段只能写 .sdd-tdd/ 下文档，不能改源码。",
    },
    3: {  # Apply: TDD，允许写代码和测试
        "allow_tools": {"Read", "Glob", "Grep", "Bash", "Agent", "Write", "Edit"},
        "allow_paths": [],
        "rule": None,  # 全放开
    },
    4: {  # Review: 只允许 Mini-Apply 修改
        "allow_tools": {"Read", "Glob", "Grep", "Bash", "Agent", "Write", "Edit"},
        "allow_paths": [],
        "rule": "R4 — 规范高于代码。Review 阶段只能修改 Must-Fix 文件。",
    },
    5: {  # Archive: 只写 archive 和 .sdd-tdd
        "allow_tools": {"Read", "Glob", "Grep", "Bash", "Agent", "Write", "Edit"},
        "allow_paths": [".sdd-tdd/", "archive/"],
        "rule": "Archive 阶段只能写归档文件。",
    },
}


def find_state_file(project_root: Path) -> Optional[Path]:
    path = project_root / STATE_FILE_NAME
    return path if path.exists() else None


def main() -> None:
    tool_name = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CLAUDE_TOOL_NAME", "")
    file_path = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("CLAUDE_FILE_PATH", "")
    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))

    state_file = find_state_file(project_root)
    if not state_file:
        sys.exit(0)  # 无活跃流程，不限制

    # 只有修改类工具需要检查
    if tool_name not in ("Write", "Edit", "NotebookEdit"):
        sys.exit(0)

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    phase = state.get("current_phase", 0)
    if phase not in PHASE_PERMISSIONS:
        sys.exit(0)

    perm = PHASE_PERMISSIONS[phase]
    if perm["rule"] is None:
        sys.exit(0)  # 该阶段无限制

    # 检查路径是否在允许范围内
    if perm["allow_paths"] and file_path:
        path_str = str(file_path).replace("\\", "/")
        allowed = any(path_str.startswith(p) for p in perm["allow_paths"])
        if allowed:
            sys.exit(0)  # 路径在白名单内

    # 检查是否写的是 .sdd-tdd 目录下的文件
    if file_path and SDD_TDD_DIR in str(file_path).replace("\\", "/"):
        sys.exit(0)  # .sdd-tdd 下的文件始终允许

    # 违规警告
    task = state.get("task", "未知")
    phase_name = {1: "Explore", 2: "Proposal", 3: "Apply", 4: "Review", 5: "Archive"}.get(phase, str(phase))

    print(f"\n[SDD-TDD Phase Guard] ⚠ 阶段门禁提醒", file=sys.stderr)
    print(f"  任务: {task}", file=sys.stderr)
    print(f"  当前阶段: Phase {phase} ({phase_name})", file=sys.stderr)
    print(f"  铁律: {perm['rule']}", file=sys.stderr)
    print(f"  即将使用: {tool_name} 操作 {file_path}", file=sys.stderr)
    print(f"  → 此操作可能不符合当前阶段。请确认是否继续。\n", file=sys.stderr)

    # 注意：不阻塞（exit 0），只输出警告到 stderr
    # 如果需要硬阻塞，将 exit code 改为 1
    sys.exit(0)


if __name__ == "__main__":
    main()
