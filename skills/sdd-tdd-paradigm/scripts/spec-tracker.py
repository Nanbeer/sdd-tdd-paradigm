#!/usr/bin/env python3
"""spec-tracker.py - Spec 覆盖率检查工具

扫描测试文件，检查 proposal.md 中每个 Spec 是否被至少一个测试覆盖。
匹配规则：测试文件的注释/docstring/测试名中包含 Spec ID（如 Spec-01、Spec-AA）。

用法：
    python spec-tracker.py check <proposal.md> <tests_dir>
    python spec-tracker.py list-specs <proposal.md>
    python spec-tracker.py list-coverage <proposal.md> <tests_dir>

仅依赖 Python 3 标准库，跨平台。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Windows 默认 stdout 编码（GBK）无法打印 ✓ 等字符，强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 匹配 "### Spec-XX:" / "## Spec-XX:"，ID 为 1 个以上字母数字字符
# 兼容 Spec-1 / Spec-01 / Spec-AA / Spec-100
SPEC_HEADER_RE = re.compile(r"^#{2,3}\s+Spec-(\w+):", re.MULTILINE)
TEST_EXT = (".py", ".js", ".ts", ".go", ".rs", ".java", ".cs", ".rb")


def extract_specs(proposal_file: Path) -> list[str]:
    if not proposal_file.exists():
        print(f"错误：文件不存在 {proposal_file}", file=sys.stderr)
        sys.exit(1)
    text = proposal_file.read_text(encoding="utf-8")
    # 去重并保持出现顺序
    seen: dict[str, None] = {}
    for m in SPEC_HEADER_RE.finditer(text):
        spec_id = f"Spec-{m.group(1)}"
        if spec_id not in seen:
            seen[spec_id] = None
    return list(seen.keys())


def scan_tests(tests_dir: Path, spec_id: str) -> list[str]:
    """在测试目录中搜索包含 spec_id 的测试文件，返回匹配文件路径列表"""
    if not tests_dir.exists():
        print(f"错误：目录不存在 {tests_dir}", file=sys.stderr)
        return []
    matches: list[str] = []
    for p in tests_dir.rglob("*"):
        if not p.is_file() or p.suffix not in TEST_EXT:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if re.search(r'\b' + re.escape(spec_id) + r'\b', text):
            matches.append(str(p))
    return matches


def check_coverage(proposal_file: Path, tests_dir: Path) -> int:
    if not proposal_file.exists():
        print(f"错误：Proposal 文件不存在：{proposal_file}", file=sys.stderr)
        return 1
    if not tests_dir.exists():
        print(f"错误：测试目录不存在：{tests_dir}", file=sys.stderr)
        return 1

    print("Spec 覆盖率报告")
    print("==================")
    print(f"Proposal: {proposal_file}")
    print(f"测试目录: {tests_dir}")
    print()

    specs = extract_specs(proposal_file)
    total = len(specs)
    covered = 0
    missing: list[str] = []

    for spec in specs:
        files = scan_tests(tests_dir, spec)
        if files:
            covered += 1
            print(f"✓ {spec}  已覆盖 by: {', '.join(files)}")
        else:
            missing.append(spec)
            print(f"✗ {spec}  未覆盖 ❌")

    missing_count = total - covered
    pct = (covered * 100 // total) if total > 0 else 0

    print()
    print("结果")
    print("----")
    print(f"总 Spec 数：{total}")
    print(f"已覆盖: {covered}")
    print(f"未覆盖: {missing_count}")
    print(f"覆盖率: {pct}%")

    if missing_count > 0:
        print()
        print("缺失列表:")
        for s in missing:
            print(f"  - {s}")
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="spec-tracker.py",
        description="Spec 覆盖率追踪工具",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="检查覆盖率")
    p_check.add_argument("proposal")
    p_check.add_argument("tests_dir")

    p_list = sub.add_parser("list-specs", help="列出所有 spec")
    p_list.add_argument("proposal")

    p_cov = sub.add_parser("list-coverage", help="输出覆盖详情")
    p_cov.add_argument("proposal")
    p_cov.add_argument("tests_dir")

    args = parser.parse_args()
    if args.cmd == "check":
        sys.exit(check_coverage(Path(args.proposal), Path(args.tests_dir)))
    elif args.cmd == "list-specs":
        for s in extract_specs(Path(args.proposal)):
            print(s)
    elif args.cmd == "list-coverage":
        sys.exit(check_coverage(Path(args.proposal), Path(args.tests_dir)))


if __name__ == "__main__":
    main()
