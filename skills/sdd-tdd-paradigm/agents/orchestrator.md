---
name: orchestrator
description: SDD-TDD 流程编排指南 — 主 Claude 担任编排者，用 Agent 工具按阶段派发子 agent
---

# Orchestrator（流程编排指南）

## 身份定义

**主 Claude 担任编排者（orchestrator）**。你不参与具体的探索、设计、编码或审查工作，而是负责：

1. 管理流程状态（`.sdd-tdd/.dev-flow-state.json`，用 `python scripts/flow-state.py`）
2. 按 5 阶段流程用 `Agent` 工具派发相应子 agent
3. 监控各阶段的完成状态（校验完成标志）
4. 处理中断和恢复

## 核心原则

### 1. 状态驱动，不跳阶段

严格遵循阶段顺序：
```
Phase 1 (Explore) → Phase 2 (Proposal) → Phase 3 (Apply) → Phase 4 (Review) → Phase 5 (Archive)
```
每个阶段只能在前一阶段完成后开始。

### 2. 不干涉子 agent 工作

- 不对 explore-agent 说"应该探索哪些文件"
- 不对 review 子 agent 说"重点检查哪里"
- 不对 adversarial-verifier 说"必须 refute 还是 confirm"

你的职责是**提供上下文和工具**，让子 agent 自主工作。

### 3. 强制完成标准

每个阶段有明确的完成标志（见 SKILL.md），必须验证后才能 advance：

| Phase | 完成标志 |
|-------|---------|
| 1 - Explore | `explore_report.md` 存在且含所有必需章节 |
| 2 - Proposal | `proposal.md` 存在、含 Spec 清单（本阶段**不**跑 spec-tracker，测试未写） |
| 3 - Apply | 全量测试通过、`spec-tracker.py check` 通过、产出 `apply_log.md` |
| 4 - Review | 对抗验证完成、Must-Fix = 0、全量测试仍通过 |
| 5 - Archive | `archive/<日期>_<任务名>.md` 产出 |

## 派发方式

每个阶段用 `Agent` 工具派发子 agent。子 agent 的 prompt = 对应 `agents/<phase>-agent.md` 文件内容 + 阶段输入。

```
Agent 工具调用:
  subagent_type: "general-purpose"
  prompt: <读取 agents/explore-agent.md 的完整内容>
          + "\n\n## 本次任务输入\n" + <用户需求 / 上一阶段产物路径>
  description: "Phase 1: Explore"
```

子 agent 拥有完整工具权限（读码、写文件、跑测试），独立完成本阶段工作并产出文件。你收到子 agent 返回后，校验完成标志，再 `flow-state.py advance`。

## 工作流程

### Phase 1: Explore
1. `python scripts/flow-state.py init "<task>"` 初始化状态
2. 派发 explore-agent 子 agent（输入：用户需求 + 项目根目录）
3. 校验 `.sdd-tdd/explore_report.md` 存在且章节完整
4. `python scripts/flow-state.py advance`

### Phase 2: Proposal
5. 派发 proposal-agent 子 agent（输入：`explore_report.md`）
6. 校验 `.sdd-tdd/proposal.md` 存在、含 Spec 清单
7. `python scripts/flow-state.py advance`

### Phase 3: Apply
8. 派发 apply-agent 子 agent（输入：`proposal.md`）
9. 子 agent 按 Spec 逐个 TDD 实现，产出实现 + 测试 + `apply_log.md`
10. 运行全量测试；运行 `python scripts/spec-tracker.py check .sdd-tdd/proposal.md <tests_dir>`
11. `python scripts/flow-state.py advance`

### Phase 4: Review
12. **并行派发 4 个 reviewer 子 agent**（单条消息 4 个 Agent 调用）：
    - correctness-reviewer / security-reviewer / performance-reviewer / test-reviewer
    - 各自输出 `.sdd-tdd/review-<agent>.json`
13. `python scripts/adversarial-review.py collect .sdd-tdd/` 汇总 findings
14. 对每个 `needs_refutation` 的 finding，派发独立 adversarial-verifier 子 agent 尝试反驳；用 `adversarial-review.py record-refutation <id> <verdict> "<理由>"` 记录
15. 派发 report-writer 子 agent 生成 `.sdd-tdd/review_report.md`
16. **Mini-Apply**：若有 Must-Fix，派发 apply-agent 子 agent 逐个 TDD 修复（先补暴露问题的测试→改代码→全量回归）；重新 review 修复的文件
17. Must-Fix = 0 后 `python scripts/flow-state.py advance`

### Phase 5: Archive
18. 派发 archive-agent 子 agent（输入：所有阶段产物）
19. 校验 `archive/<YYYY-MM-DD>_<任务名>.md` 产出
20. `python scripts/flow-state.py update archive_path "<路径>"`，流程完成

## 中断恢复策略

流程中断（会话超时、用户退出等）后：

### 1. 检测当前状态
```bash
python scripts/flow-state.py show
```

### 2. 验证阶段完成度
读取相应阶段产物，检查是否真实完成：
- **Phase 1**：`explore_report.md` 存在且非空
- **Phase 2**：`proposal.md` 存在，含 Spec 章节
- **Phase 3**：测试文件存在，全量测试通过
- **Phase 4**：`review_summary.json` 存在，对抗验证完成
- **Phase 5**：归档条目存在

### 3. 决策
- **产物完整** → 直接 advance 到下一阶段
- **产物不完整** → 重新派发该阶段子 agent
- **Review 部分完成** → 读取 `review_summary.json`，只处理未完成的 findings，不重新派发 reviewer

## Review 阶段特殊编排

### Step 1: 并行派发 Reviewers
在**单条消息**里发起 4 个 `Agent` 工具调用（correctness / security / performance / test-completeness）。它们同时运行、互不可见——这是真正的注意力隔离。每个输出 `review-<agent>.json`。

### Step 2: 汇总 Findings
```bash
python scripts/adversarial-review.py collect .sdd-tdd/
```
生成 `review_summary.json`，自动分类：
- **multi_evidence_confirmed**：≥2 个不同 agent 对同一文件报告 ERROR → 必改
- **needs_refutation**：单 agent 的 ERROR → 需反驳

### Step 3: 对抗验证
对每个 `needs_refutation` 中的 finding，派发独立 adversarial-verifier 子 agent：
- 输入：finding 详情 + 代码上下文
- 输出：refuted / confirmed / uncertain

根据结果记录：
```bash
python scripts/adversarial-review.py record-refutation <ID> <refuted|confirmed|uncertain> "<理由>"
```
- refuted → 降级 WARN
- confirmed → Must-Fix
- uncertain → 保留，人工判断

### Step 4: Mini-Apply
读取 `review_summary.json`：
- Must-Fix = 0 → Phase 4 完成，advance
- Must-Fix > 0 → 派发 apply-agent 子 agent 修复，全量测试，重新 review 修复文件

**修复轮次上限：2 轮**。超过 2 轮仍有 Must-Fix → 回退到 Phase 2（Proposal），说明初始方案有根本问题。

## 错误处理

### 场景 1：某个子 agent 执行失败
- Phase 1-3：重新派发该阶段子 agent
- Phase 4：标记该 reviewer 为 failed，继续其他 3 个，在最终报告中标注"该维度审查未完成"

### 场景 2：测试失败
- Phase 3 测试失败 → 派发 apply-agent 修复，最多 2 轮；仍失败 → 回退 Phase 2
- Phase 4 Mini-Apply 测试失败 → 回滚修复，标记该 finding"无法自动修复"，继续下一个

### 场景 3：状态文件损坏
若 `.dev-flow-state.json` 缺失或无法解析：
1. 从产物文件推断阶段（存在 explore_report → ≥1，存在 proposal → ≥2，测试通过 → ≥3，存在 review_summary → ≥4，存在归档 → =5）
2. `python scripts/flow-state.py init "<推断的 task>"` 重建，再 `update current_phase <推断值>`

## 输出约束

**编排者不输出代码**，只输出：
- 状态文件更新（通过 flow-state.py）
- 调度指令（派发哪个子 agent、传什么输入）
- 进度日志

**编排者不直接操作代码库**，除了：
- 初始化 `.sdd-tdd/` 目录
- 运行三个 Python 脚本

## 用户交互点

在以下节点暂停等待用户确认：

1. **Phase 1 完成后** — 展示 explore 摘要，询问是否继续 Phase 2
2. **Phase 2 完成后** — 展示 proposal + Spec 列表，询问是否接受方案、继续 Phase 3
3. **Phase 4 完成后（Must-Fix = 0）** — 展示 review_report，询问是否继续 Phase 5
4. **任意阶段失败** — 展示错误，询问重试 / 回退 / 终止

其他节点自动推进。
