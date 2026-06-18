#!/bin/bash
# spec-tracker.sh - Spec 覆盖率检查工具
#
# 扫描测试文件，检查每个 Spec 是否被至少一个测试 case 覆盖。
# 匹配规则：测试用例的 docstring 或注释中包含 Spec-XX 编号。
#
# 用法：
#   spec-tracker.sh check <proposal.md> <tests_dir>
#   spec-tracker.sh list-specs <proposal.md>            # 列出所有 spec
#   spec-tracker.sh list-coverage <proposal.md> <tests_dir>

set -euo pipefail

extract_specs() {
    local proposal_file="$1"

    if [[ ! -f "$proposal_file" ]]; then
        echo "错误：文件不存在 $proposal_file" >&2
        exit 1
    fi

    # 匹配 "### Spec-XX:" 或 "## Spec-XX:" 模式
    grep -E '^##? +Spec-[A-Z0-9]{2}:' "$proposal_file" \
        | sed -E 's/^##? +Spec-(..):.*/Spec-\1/' \
        | sort -u
}

scan_tests() {
    local tests_dir="$1"
    local spec_id="$2"

    if [[ ! -d "$tests_dir" ]]; then
        echo "错误：目录不存在 $tests_dir" >&2
        return 1
    fi

    # 在测试文件中搜索 Spec ID
    # 搜索范围：测试文件名、docstring、注释、测试用例名
    local matches
    matches=$(grep -rln "$spec_id" "$tests_dir" 2>/dev/null \
        | grep -E '\.(py|js|ts|go|rs|java)$' \
        | head -5)

    if [[ -n "$matches" ]]; then
        echo "$matches"
        return 0
    else
        return 1
    fi
}

check_coverage() {
    local proposal_file="$1"
    local tests_dir="$2"

    if [[ ! -f "$proposal_file" ]]; then
        echo "错误：Proposal 文件不存在：$proposal_file"
        exit 1
    fi

    if [[ ! -d "$tests_dir" ]]; then
        echo "错误：测试目录不存在：$tests_dir"
        exit 1
    fi

    echo "Spec 覆盖率报告"
    echo "=================="
    echo "Proposal: $proposal_file"
    echo "测试目录: $tests_dir"
    echo ""

    local specs
    specs=$(extract_specs "$proposal_file")
    local total=0
    local covered=0
    local missing_list=()

    while IFS= read -r spec; do
        total=$((total + 1))
        local test_files
        if test_files=$(scan_tests "$tests_dir" "$spec"); then
            covered=$((covered + 1))
            local file_list
            file_list=$(echo "$test_files" | tr '\n' ', ' | sed 's/,$//')
            echo "✓ $spec  已覆盖 by: $file_list"
        else
            missing_list+=("$spec")
            echo "✗ $spec  未覆盖 ❌"
        fi
    done <<< "$specs"

    local missing=$((total - covered))
    local pct=0
    if (( total > 0 )); then
        pct=$((covered * 100 / total))
    fi

    echo ""
    echo "结果"
    echo "----"
    echo "总 Spec 数：$total"
    echo "已覆盖: $covered"
    echo "未覆盖: $missing"
    echo "覆盖率: ${pct}%"

    if (( missing > 0 )); then
        echo ""
        echo "缺失列表:"
        for s in "${missing_list[@]}"; do
            echo "  - $s"
        done
        exit 1
    fi

    exit 0
}

list_specs() {
    local proposal_file="$1"
    extract_specs "$proposal_file"
}

case "${1:-}" in
    check)
        if [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]]; then
            echo "用法：spec-tracker.sh check <proposal.md> <tests_dir>"
            exit 1
        fi
        check_coverage "$2" "$3"
        ;;
    list-specs)
        if [[ -z "${2:-}" ]]; then
            echo "用法：spec-tracker.sh list-specs <proposal.md>"
            exit 1
        fi
        list_specs "$2"
        ;;
    list-coverage)
        if [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]]; then
            echo "用法：spec-tracker.sh list-coverage <proposal.md> <tests_dir>"
            exit 1
        fi
        check_coverage "$2" "$3"
        ;;
    *)
        echo "Spec 覆盖率追踪工具"
        echo ""
        echo "用法："
        echo "  spec-tracker.sh check <proposal.md> <tests_dir>   检查覆盖率"
        echo "  spec-tracker.sh list-specs <proposal.md>          列出所有 spec"
        echo "  spec-tracker.sh list-coverage <proposal.md> <tests_dir>  输出覆盖详情"
        echo ""
        echo "Spec 命名约定：Spec-AA, Spec-BB, ..., Spec-ZZ, Spec-00, Spec-01, ..."
        echo "测试文件必须在注释或 docstring 中包含 Spec ID 才能被识别。"
        exit 1
        ;;
esac
