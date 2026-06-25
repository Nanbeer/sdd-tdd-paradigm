#!/usr/bin/env python3
"""write-decision-memory.py — Post-Archive Hook：将关键决策写入 Memory

在 Archive 完成后运行，提取 archive 条目中的关键决策和 Grilling 结论，
写入 Claude Code 的 Memory 系统（~/.claude/projects/*/memory/），
使未来 Explore 阶段可以自动检索历史决策。

用法（在 settings.json hooks 中配置）:
  "PostToolUse": [{
    "matcher": "Write(archive/**)",
    "hooks": [{
      "type": "command",
      "command": "python .claude/skills/sdd-tdd-paradigm/hooks/write-decision-memory.py \"$FILE_PATH\""
    }]
  }]

或手动调用:
  python write-decision-memory.py archive/2026-06-22_user-auth.md [项目根目录]
"""

import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Windows 默认 stdout 编码（GBK）无法打印特殊字符，强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def extract_decisions(archive_content: str) -> Tuple[List[Dict[str, str]], List[str]]:
    """从归档内容中提取关键决策"""
    decisions = []

    # 提取"方案选择"中的决策
    for m in re.finditer(
        r"###\s+采纳方案.*?(?=###|\Z)",
        archive_content,
        re.DOTALL,
    ):
        block = m.group()
        choice = re.search(r"\*\*选择\*\*[：:]\s*(.+?)(?:\n|$)", block)
        reason = re.search(r"\*\*理由\*\*[：:]\s*(.+?)(?:\n\n|\n###|\Z)", block, re.DOTALL)

        # 提取决策条目
        for dm in re.finditer(r"-\s*Decision-\d+[：:]\s*(.+?)(?:\n|$)", block):
            decisions.append({
                "content": dm.group(1).strip(),
                "context": choice.group(1).strip() if choice else "",
                "rationale": reason.group(1).strip().replace("\n", " ") if reason else "",
            })

    # 提取"学到了什么"中的关键发现
    learnings = []
    for m in re.finditer(
        r"##\s+学到了什么.*?(?=##|\Z)",
        archive_content,
        re.DOTALL,
    ):
        block = m.group()
        for lm in re.finditer(r"-\s*\*\*(?:假设|验证|发现|建议)\d*\*\*[：:]\s*(.+?)(?:\n|$)", block):
            learnings.append(lm.group(1).strip())
        for lm in re.finditer(r"-\s*(.+?(?:bcrypt|性能|延迟|QPS|P99|race condition).+?)(?:\n|$)", block):
            learnings.append(lm.group(1).strip())

    # 提取"Grilling 逼出的边界"（v2.0 新增）
    for m in re.finditer(
        r"###\s+🔥\s*Grilling.*?(?=###|\Z)",
        archive_content,
        re.DOTALL,
    ):
        block = m.group()
        for bm in re.finditer(r"-\s*\*\*(?:边界|反例|假设)\d*\*\*[：:]\s*(.+?)(?:\n|$)", block):
            decisions.append({
                "content": f"[Grilling 发现] {bm.group(1).strip()}",
                "context": "来自 Grilling 追问",
                "rationale": "通过 Grilling 协议验证",
            })

    return decisions, learnings


def generate_memory_entry(
    title: str, decision: Dict[str, str], tags: List[str]
) -> str:
    """生成 Memory 文件内容"""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower().strip())[:60]

    return f"""---
name: {slug}
description: {decision['content'][:100]}
metadata:
  type: project
  tags: {json.dumps(tags)}
  archived_at: {ts}
---

## 决策

{decision['content']}

## 背景

{decision['context']}

## 理由

{decision['rationale']}

## 来源

自动从 SDD-TDD Archive 导入。
"""


def main() -> None:
    archive_path = sys.argv[1] if len(sys.argv) > 1 else ""
    project_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()

    if not archive_path:
        print("[SDD-TDD Memory] 错误：未提供 archive 路径")
        sys.exit(1)

    archive_file = project_root / archive_path
    if not archive_file.exists():
        print(f"[SDD-TDD Memory] 错误：归档文件不存在 {archive_file}")
        sys.exit(1)

    content = archive_file.read_text(encoding="utf-8")
    decisions, learnings = extract_decisions(content)

    if not decisions:
        print("[SDD-TDD Memory] 信息：未在归档中找到可提取的决策")
        sys.exit(0)

    # 检查 Memory 目录
    memory_base = project_root / ".claude" / "memory"
    memory_base.mkdir(parents=True, exist_ok=True)

    # 提取标签
    tags_section = re.search(r"##\s+标签.*?(?=##|\Z)", content, re.DOTALL)
    tags = []
    if tags_section:
        for tag_m in re.finditer(r"`(.+?)`", tags_section.group()):
            tags.append(tag_m.group(1))

    # 提取任务名
    task_match = re.search(r"#\s+Task[：:]\s*(.+?)(?:\n|$)", content)
    task_name = task_match.group(1).strip() if task_match else archive_path

    written = 0
    for decision in decisions:
        title = f"sdd-tdd-decision-{task_name}-{uuid.uuid4().hex[:8]}"
        entry = generate_memory_entry(title, decision, tags)
        mem_file = memory_base / f"{title}.md"
        mem_file.write_text(entry, encoding="utf-8")
        written += 1

    print(f"[SDD-TDD Memory] ✓ 已将 {written} 条决策写入 Memory ({memory_base})")
    if learnings:
        print(f"[SDD-TDD Memory]   同时发现 {len(learnings)} 条技术发现（未单独写入，保留在归档中）")

    sys.exit(0)


if __name__ == "__main__":
    main()
