#!/bin/bash
# adversarial-review.sh - 对抗验证编排脚本
#
# 收集多个审查 agent 的 findings，识别出：
#   1. 多证据确认的 finding（>= 2 个 agent 报告同文件同行号）
#   2. 单 agent 的 ERR finding（需要对抗验证/反驳）
#   3. 汇总分类结果
#
# 输入：多个 review-*.json 文件
# 输出：review_summary.json
#
# 用法：
#   adversarial-review.sh collect <review_dir>
#   adversarial-review.sh show-pending
#   adversarial-review.sh record-refutation <finding_id> <refuted|confirmed|uncertain> <理由>

set -euo pipefail

STATE_DIR=".sdd-tdd"
SUMMARY_FILE="$STATE_DIR/review_summary.json"

# 收集 findings 并生成汇总
collect_findings() {
    local review_dir="$1"

    if [[ ! -d "$review_dir" ]]; then
        echo "错误：Review 目录不存在 $review_dir"
        exit 1
    fi

    # 找到所有 review-*.json
    local review_files
    review_files=$(find "$review_dir" -maxdepth 1 -name "review-*.json" 2>/dev/null || true)

    if [[ -z "$review_files" ]]; then
        echo "警告：未找到 review-*.json 文件于 $review_dir"
        exit 0
    fi

    # 使用临时文件收集所有 findings
    local tmp_dir
    tmp_dir=$(mktemp -d)
    trap "rm -rf $tmp_dir" EXIT

    local total_findings=0
    local err_count=0
    local warn_count=0
    local info_count=0

    cat > "$tmp_dir/all_findings.json" <<EOF
{
  "findings": [],
  "multi_evidence_confirmed": [],
  "needs_refutation": []
}
EOF

    while IFS= read -r review_file; do
        [[ -z "$review_file" ]] && continue

        local agent
        agent=$(jq -r '.agent // "unknown"' "$review_file")

        # 提取 findings，附带 agent 信息
        local count
        count=$(jq '.findings | length' "$review_file")
        total_findings=$((total_findings + count))

        # 统计 severity
        err_count=$((err_count + $(jq '[.findings[] | select(.severity == "ERROR")] | length' "$review_file")))
        warn_count=$((warn_count + $(jq '[.findings[] | select(.severity == "WARN")] | length' "$review_file")))
        info_count=$((info_count + $(jq '[.findings[] | select(.severity == "INFO")] | length' "$review_file")))

        # 给每个 finding 加上 source_agent
        jq --arg agent "$agent" \
           '[.findings[] | . + {source_agent: $agent}]' \
           "$review_file" > "$tmp_dir/$(basename "$review_file")"

    done <<< "$review_files"

    # 合并所有 findings
    local merged
    merged=$(jq -s 'flatten' "$tmp_dir"/review-*.json 2>/dev/null || echo "[]")

    # 按 file:line 分组找出多证据确认
    local multi_evidence
    multi_evidence=$(echo "$merged" \
        | jq '
            group_by(.file + ":" + .line) \
            | map(select(length >= 2)) \
            | map({
                location: .[0].file + ":" + .[0].line,
                findings: .,
                agent_count: [.[].source_agent] | unique | length,
                verdict: "must_fix_multi_evidence"
              })
          ')

    # 找出单 agent 的 ERR，需要反驳验证
    local single_err
    single_err=$(echo "$merged" \
        | jq '
            group_by(.file + ":" + .line) \
            | map(select(length == 1 and .[0].severity == "ERROR")) \
            | map(.[0] + {verdict: "needs_refutation"})
          ')

    # 输出汇总
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    jq -n \
        --argjson findings "$merged" \
        --argjson multi_evidence "$multi_evidence" \
        --argjson single_err "$single_err" \
        --argjson err_count "$err_count" \
        --argjson warn_count "$warn_count" \
        --argjson info_count "$info_count" \
        --arg timestamp "$timestamp" \
        '{
          findings: $findings,
          multi_evidence_confirmed: $multi_evidence,
          needs_refutation: $single_err,
          summary: {
            total: ($findings | length),
            error: $err_count,
            warn: $warn_count,
            info: $info_count,
            multi_evidence_count: ($multi_evidence | length),
            needs_refutation_count: ($single_err | length)
          },
          generated_at: $timestamp
        }' > "$SUMMARY_FILE"

    echo "✓ 已生成 Review 汇总：$SUMMARY_FILE"
    echo ""
    echo "Findings 统计:"
    echo "  总数: $(jq '.summary.total' "$SUMMARY_FILE")"
    echo "  ERROR: $(jq '.summary.error' "$SUMMARY_FILE")"
    echo "  WARN: $(jq '.summary.warn' "$SUMMARY_FILE")"
    echo "  INFO: $(jq '.summary.info' "$SUMMARY_FILE")"
    echo ""
    echo "分类:"
    echo "  多证据确认（必改）: $(jq '.summary.multi_evidence_count' "$SUMMARY_FILE")"
    echo "  需对抗验证: $(jq '.summary.needs_refutation_count' "$SUMMARY_FILE")"
}

# 显示待验证的 ERR findings
show_pending() {
    if [[ ! -f "$SUMMARY_FILE" ]]; then
        echo "错误：汇总文件不存在 $SUMMARY_FILE"
        echo "请先运行：adversarial-review.sh collect <review_dir>"
        exit 1
    fi

    local count
    count=$(jq '.needs_refutation | length' "$SUMMARY_FILE")

    echo "待对抗验证的 findings: $count"
    echo "======================="
    echo ""

    jq -r '.needs_refutation[] |
        "Finding: \(.id) [\(.severity)]",
        "位置: \(.file):\(.line)",
        "问题: \(.issue)",
        "证据: \(.evidence | split("\n") | map("  > " + .) | join("\n"))",
        ""' "$SUMMARY_FILE"
}

# 记录反驳结果
record_refutation() {
    local finding_id="$1"
    local verdict="$2"  # refuted|confirmed|uncertain
    local reason="$3"

    if [[ ! -f "$SUMMARY_FILE" ]]; then
        echo "错误：汇总文件不存在 $SUMMARY_FILE"
        exit 1
    fi

    if [[ "$verdict" != "refuted" && "$verdict" != "confirmed" && "$verdict" != "uncertain" ]]; then
        echo "错误：verdict 必须是 refuted|confirmed|uncertain"
        exit 1
    fi

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # 找到 finding 并更新 verdict
    local found
    found=$(jq --arg id "$finding_id" '.needs_refutation[] | select(.id == $id)' "$SUMMARY_FILE")

    if [[ -z "$found" ]]; then
        echo "错误：未找到 finding ID $finding_id"
        exit 1
    fi

    jq --arg id "$finding_id" \
       --arg verdict "$verdict" \
       --arg reason "$reason" \
       --arg timestamp "$timestamp" \
       '(.needs_refutation[] | select(.id == $id)) += {
          refutation_verdict: $verdict,
          refutation_reason: $reason,
          refuted_at: $timestamp
        }
        | .summary.refuted = ([.needs_refutation[] | select(.refutation_verdict == "refuted")] | length)
        | .summary.confirmed = ([.needs_refutation[] | select(.refutation_verdict == "confirmed")] | length)
        | .summary.uncertain = ([.needs_refutation[] | select(.refutation_verdict == "uncertain")] | length)
        ' \
       "$SUMMARY_FILE" > "$SUMMARY_FILE.tmp" && mv "$SUMMARY_FILE.tmp" "$SUMMARY_FILE"

    echo "✓ $finding_id marked as $verdict"
    echo "  原因: $reason"
}

case "${1:-}" in
    collect)
        if [[ -z "${2:-}" ]]; then
            echo "用法：adversarial-review.sh collect <review_dir>"
            exit 1
        fi
        collect_findings "$2"
        ;;
    show-pending)
        show_pending
        ;;
    record-refutation)
        if [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]] || [[ -z "${4:-}" ]]; then
            echo "用法：adversarial-review.sh record-refutation <finding_id> <refuted|confirmed|uncertain> <理由>"
            exit 1
        fi
        record_refutation "$2" "$3" "$4"
        ;;
    *)
        echo "SDD-TDD 对抗验证编排工具"
        echo ""
        echo "用法："
        echo "  adversarial-review.sh collect <review_dir>    收集 review-*.json 并生成汇总"
        echo "  adversarial-review.sh show-pending            显示待反驳的 findings"
        echo "  adversarial-review.sh record-refutation <id> <verdict> <理由>  记录反驳结果"
        echo ""
        echo "verdict 类型："
        echo "  refuted    - 反驳成功，降级为 WARN"
        echo "  confirmed  - 反驳失败，确认为真实问题，必改"
        echo "  uncertain  - 不确定，提交人工判断"
        exit 1
        ;;
esac
