#!/usr/bin/env python3
"""grill-check.py - Grilling G4 退出条件机械校验（可选脚本）

用法：
    python grill-check.py check <grill_log.md>
    python grill-check.py list-fuzzy <grill_log.md>
    python grill-check.py list-decisions <grill_log.md>

校验 Grilling Protocol 的 G4 退出条件是否满足：
1. 所有模糊词已被逼出具体定义
2. 每个关键决策点至少有 1 个反例被回答
3. 用户给出"可证伪"的依据
4. 主 agent 已确认无遗漏

仅依赖 Python 3 标准库，跨平台（Windows/PowerShell、Linux、macOS）。
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

# Windows 默认 stdout 编码可能无法打印 ✓ 等字符，强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ── 模糊词列表 ──────────────────────────────────────────────
FUZZY_PATTERNS = [
    (r"一般来说|通常|大部分情况|一般情况下", "无具体反例/边界定义"),
    (r"性能[会很应该]?[好快高]|应该够[快用]", "无具体性能指标（QPS/P99/ms）"),
    (r"差不多|大概|几个|一些|若干", "无精确数字或范围"),
    (r"后续[可以再]?优化|以后再说|暂时先|先这样", "推迟优化但未说明现在不做的代价"),
    (r"用户[一般应该]?不会|正常情况下", "无用户行为依据/兜底措施"),
    (r"复用现有逻辑|参考现有实现|类似[已有]?", "未指明具体代码位置"),
    (r"我们假设|假设.*成立|假定", "假设未经验证/反例未讨论"),
]


def extract_grill_log(path: str) -> str:
    """读取 grilling 日志"""
    p = Path(path)
    if not p.exists():
        print(f"错误：文件不存在 {path}", file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8")


def find_fuzzy_words(text: str) -> List[Dict[str, str]]:
    """查找所有模糊词出现位置"""
    findings = []
    for pattern, concern in FUZZY_PATTERNS:
        for m in re.finditer(pattern, text):
            # 提取上下文（前后 30 字符）
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            context = text[start:end].replace("\n", " ").strip()
            findings.append({
                "pattern": pattern,
                "match": m.group(),
                "concern": concern,
                "context": f"...{context}...",
            })
    return findings


def find_counter_examples(text: str) -> List[str]:
    """查找反例标记"""
    # 查找反例相关的描述
    patterns = [
        r"反例\s*[:：]\s*(.+?)(?:\n|$)",
        r"这种情况怎么办\s*[:：]\s*(.+?)(?:\n|$)",
        r"如果.{1,30}怎么办",
        r"兜底\s*[:：]\s*(.+?)(?:\n|$)",
    ]
    results = []
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            results.append(m.group().strip())
    return results


def find_decisions(text: str) -> List[str]:
    """提取关键决策点"""
    decisions = []
    for m in re.finditer(r"决策点?\s*\d+\s*[:：]\s*(.+?)(?:\n|$)", text):
        decisions.append(m.group().strip())
    return decisions


def check_exit_conditions(text: str) -> Dict[str, Any]:
    """检查 G4 退出条件"""
    fuzzy = find_fuzzy_words(text)
    counter_examples = find_counter_examples(text)
    decisions = find_decisions(text)

    result = {
        "g4_1_fuzzy_resolved": len(fuzzy) == 0,
        "g4_2_counter_examples": len(counter_examples) > 0,
        "g4_3_verifiable": False,  # 需要人工判断
        "g4_4_confirmed": False,   # 需要人工判断
        "fuzzy_count": len(fuzzy),
        "fuzzy_items": fuzzy,
        "counter_example_count": len(counter_examples),
        "counter_examples": counter_examples,
        "decision_count": len(decisions),
        "decisions": decisions,
    }

    # G4.1: 检查是否所有模糊词已被解决
    # 如果文本末尾有"所有模糊词已解决"或类似的确认标记
    if re.search(r"模糊词.*已.*[解决清除处理]|所有.*模糊.*已|fuzzy.*resolved", text, re.IGNORECASE):
        result["g4_1_fuzzy_resolved"] = True
        result["fuzzy_count"] = max(0, result["fuzzy_count"] - len(fuzzy))

    # G4.3: 检查是否有可证伪依据（代码引用/测试场景/数据）
    if re.search(r"(?:文件[:：]|行[:：]\d+|测试场景[:：]|基准测试|benchmark|QPS|P99)", text):
        result["g4_3_verifiable"] = True

    # G4.4: 检查是否有"无遗漏"确认
    if re.search(r"无遗漏|已确认.*完整|确认.*无.*遗漏|grilling.*完成", text):
        result["g4_4_confirmed"] = True

    return result


def cmd_check(args) -> None:
    """检查 grilling 退出条件"""
    text = extract_grill_log(args.grill_log)
    result = check_exit_conditions(text)

    print("Grilling G4 退出条件检查")
    print("========================")
    print(f"G4.1 模糊词已解决: {'✓' if result['g4_1_fuzzy_resolved'] else '✗'} ({result['fuzzy_count']} 个模糊词)")
    print(f"G4.2 有反例讨论: {'✓' if result['g4_2_counter_examples'] else '✗'} ({result['counter_example_count']} 个反例)")
    print(f"G4.3 可证伪依据: {'✓' if result['g4_3_verifiable'] else '✗'} (需人工确认)")
    print(f"G4.4 无遗漏确认: {'✓' if result['g4_4_confirmed'] else '✗'} (需人工确认)")
    print()

    if result["fuzzy_items"]:
        print(f"⚠ 未解决的模糊词 ({len(result['fuzzy_items'])} 个):")
        for item in result["fuzzy_items"]:
            print(f"  - '{item['match']}' → {item['concern']}")
            print(f"    上下文: {item['context']}")
        print()

    if result["counter_examples"]:
        print(f"✓ 已讨论的反例 ({len(result['counter_examples'])} 个):")
        for ce in result["counter_examples"]:
            print(f"  - {ce}")
        print()

    all_pass = all([
        result["g4_1_fuzzy_resolved"],
        result["g4_2_counter_examples"],
        result["g4_3_verifiable"],
        result["g4_4_confirmed"],
    ])

    if all_pass:
        print("✓ 所有 G4 退出条件均满足（机械检查）。请主 agent 做最终人工确认。")
        sys.exit(0)
    else:
        print("✗ G4 退出条件未完全满足。请继续 Grilling。")
        sys.exit(1)


def cmd_list_fuzzy(args) -> None:
    """列出所有模糊词"""
    text = extract_grill_log(args.grill_log)
    fuzzy = find_fuzzy_words(text)
    if not fuzzy:
        print("✓ 未检测到模糊词")
        return
    print(f"检测到 {len(fuzzy)} 个模糊词:")
    for item in fuzzy:
        print(f"  '{item['match']}' → {item['concern']}")


def cmd_list_decisions(args) -> None:
    """列出所有关键决策点"""
    text = extract_grill_log(args.grill_log)
    decisions = find_decisions(text)
    if not decisions:
        print("未检测到关键决策点")
        return
    print(f"检测到 {len(decisions)} 个关键决策点:")
    for d in decisions:
        print(f"  - {d}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="grill-check.py",
        description="Grilling G4 退出条件机械校验（可选工具）",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="检查 G4 退出条件")
    p_check.add_argument("grill_log")

    p_fuzzy = sub.add_parser("list-fuzzy", help="列出所有模糊词")
    p_fuzzy.add_argument("grill_log")

    p_decisions = sub.add_parser("list-decisions", help="列出所有关键决策点")
    p_decisions.add_argument("grill_log")

    args = parser.parse_args()
    if args.cmd == "check":
        cmd_check(args)
    elif args.cmd == "list-fuzzy":
        cmd_list_fuzzy(args)
    elif args.cmd == "list-decisions":
        cmd_list_decisions(args)


if __name__ == "__main__":
    main()
