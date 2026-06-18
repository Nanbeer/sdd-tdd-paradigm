#!/bin/bash
# flow-state.sh - 管理 SDD-TDD 开发流程的状态文件
#
# 用法：
#   flow-state.sh init <task_name>
#   flow-state.sh advance
#   flow-state.sh update <field> <value>
#   flow-state.sh show
#   flow-state.sh check-phase <phase_number>

set -euo pipefail

STATE_DIR=".sdd-tdd"
STATE_FILE="$STATE_DIR/.dev-flow-state.json"

# 获取当前时间戳（ISO 8601）
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# 初始化状态文件
init_state() {
    local task_name="$1"

    if [[ ! -d "$STATE_DIR" ]]; then
        mkdir -p "$STATE_DIR"
    fi

    if [[ -f "$STATE_FILE" ]]; then
        echo "警告：状态文件已存在 $STATE_FILE"
        echo "如需重新开始，请先删除：rm $STATE_FILE"
        exit 1
    fi

    local timestamp=$(get_timestamp)

    cat > "$STATE_FILE" << EOF
{
  "task": "$task_name",
  "route": "full",
  "current_phase": 1,
  "phases_done": [],
  "explore_path": "$STATE_DIR/explore_report.md",
  "proposal_path": "$STATE_DIR/proposal.md",
  "apply_log_path": "$STATE_DIR/apply_log.md",
  "review_report_path": "$STATE_DIR/review_report.md",
  "specs_total": 0,
  "specs_done": 0,
  "review_findings": {
    "error": 0,
    "warn": 0,
    "info": 0
  },
  "must_fix_total": 0,
  "must_fix_done": 0,
  "review_round": 0,
  "archive_path": "",
  "started_at": "$timestamp",
  "updated_at": "$timestamp"
}
EOF

    echo "✓ 已初始化状态：$STATE_FILE"
    echo "  任务：$task_name"
    echo "  当前阶段：Phase 1 (Explore)"
}

# 推进到下一阶段
advance_phase() {
    if [[ ! -f "$STATE_FILE" ]]; then
        echo "错误：状态文件不存在 $STATE_FILE"
        echo "请先运行：flow-state.sh init <task_name>"
        exit 1
    fi

    local current=$(jq -r '.current_phase' "$STATE_FILE")
    local phases_done=$(jq -r '.phases_done | join(",")' "$STATE_FILE")
    local timestamp=$(get_timestamp)

    local new_phase=$((current + 1))

    # 更新 phases_done
    local new_phases_done="$phases_done$current"
    [[ -n "$phases_done" ]] && new_phases_done="${phases_done},${current}" || new_phases_done="${current}"

    # 检查新阶段是否有效
    if (( new_phase > 6 )); then
        echo "✓ 流程已完成（Phase 5: Archive 是最后一步）"
        jq ".updated_at = \"$timestamp\"" "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
        exit 0
    fi

    # 更新状态文件
    jq --argjson phase "$new_phase" \
       --arg phases_done "$new_phases_done" \
       --arg timestamp "$timestamp" \
       '.current_phase = $phase | .phases_done = ($phases_done | split(",")) | .updated_at = $timestamp' \
       "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

    echo "✓ 已推进到 Phase $new_phase"
    echo "  已完成阶段：$new_phases_done"
}

# 更新状态字段
update_field() {
    local field="$1"
    local value="$2"
    local timestamp=$(get_timestamp)

    if [[ ! -f "$STATE_FILE" ]]; then
        echo "错误：状态文件不存在 $STATE_FILE"
        exit 1
    fi

    # 尝试将 value 转换为 JSON（如果是数字或布尔值）
    if [[ "$value" =~ ^-?[0-9]+$ ]] || [[ "$value" == "true" ]] || [[ "$value" == "false" ]]; then
        jq --arg field "$field" --argjson value "$value" --arg timestamp "$timestamp" \
           '.[$field] = $value | .updated_at = $timestamp' \
           "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
    else
        jq --arg field "$field" --arg value "$value" --arg timestamp "$timestamp" \
           '.[$field] = $value | .updated_at = $timestamp' \
           "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
    fi

    echo "✓ 已更新：$field = $value"
}

# 显示当前状态
show_state() {
    if [[ ! -f "$STATE_FILE" ]]; then
        echo "状态文件不存在：$STATE_FILE"
        exit 0
    fi

    local task=$(jq -r '.task' "$STATE_FILE")
    local current=$(jq -r '.current_phase' "$STATE_FILE")
    local phases_done=$(jq -r '.phases_done | join(", ")' "$STATE_FILE")
    local specs_total=$(jq -r '.specs_total' "$STATE_FILE")
    local specs_done=$(jq -r '.specs_done' "$STATE_FILE")
    local review_findings=$(jq -c '.review_findings' "$STATE_FILE")
    local must_fix_total=$(jq -r '.must_fix_total' "$STATE_FILE")
    local must_fix_done=$(jq -r '.must_fix_done' "$STATE_FILE")
    local review_round=$(jq -r '.review_round' "$STATE_FILE")
    local started_at=$(jq -r '.started_at' "$STATE_FILE")
    local updated_at=$(jq -r '.updated_at' "$STATE_FILE")

    cat << EOF
SDD-TDD 流程状态
================

任务：$task
当前阶段：Phase $current
已完成阶段：${phases_done:-无}

规格进度：$specs_done / $specs_total specs (${specs_done}/${specs_total})
必须修复：$must_fix_done / $must_fix_total completed
Review 轮次：$review_round
Review 发现：$review_findings

开始时间：$started_at
最后更新：$updated_at

状态文件：$STATE_FILE
EOF
}

# 检查是否处于指定阶段（用于 agent 脚本）
check_phase() {
    local target_phase="$1"

    if [[ ! -f "$STATE_FILE" ]]; then
        echo "error"
        exit 1
    fi

    local current=$(jq -r '.current_phase' "$STATE_FILE")

    if (( current == target_phase )); then
        echo "active"
        exit 0
    elif (( current > target_phase )); then
        echo "done"
        exit 0
    else
        echo "pending"
        exit 0
    fi
}

# 主逻辑
case "${1:-}" in
    init)
        if [[ -z "${2:-}" ]]; then
            echo "用法：flow-state.sh init <task_name>"
            exit 1
        fi
        init_state "$2"
        ;;
    advance)
        advance_phase
        ;;
    update)
        if [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]]; then
            echo "用法：flow-state.sh update <field> <value>"
            exit 1
        fi
        update_field "$2" "$3"
        ;;
    show)
        show_state
        ;;
    check-phase)
        if [[ -z "${2:-}" ]]; then
            echo "用法：flow-state.sh check-phase <phase_number>"
            exit 1
        fi
        check_phase "$2"
        ;;
    *)
        echo "SDD-TDD 流程状态管理工具"
        echo ""
        echo "用法："
        echo "  flow-state.sh init <task_name>            初始化新流程"
        echo "  flow-state.sh advance                     推进到下一阶段"
        echo "  flow-state.sh update <field> <value>      更新状态字段"
        echo "  flow-state.sh show                        显示当前状态"
        echo "  flow-state.sh check-phase <phase_num>     检查阶段状态（active/done/pending）"
        echo ""
        echo "示例："
        echo "  flow-state.sh init '实现用户登录模块'"
        echo "  flow-state.sh advance"
        echo "  flow-state.sh update specs_total 5"
        echo "  flow-state.sh update must_fix_done 2"
        echo "  flow-state.sh show"
        exit 1
        ;;
esac
