# 系统架构

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    SDD-TDD Skill                             │
│                                                             │
│  ┌──────────────┐                                           │
│  │ orchestrator │  ←── 流程编排，状态管理                      │
│  └──────┬───────┘                                           │
│         │                                                    │
│         │ 调度 5 个阶段                                       │
│         │                                                    │
│  ┌──────▼──────────────────────────────────────────────────┐│
│  │                  Phase Agents                           ││
│  │                                                        ││
│  │  Phase 1: explore-agent                                ││
│  │  Phase 2: proposal-agent                               ││
│  │  Phase 3: apply-agent                                  ││
│  │  Phase 4: 4 review agents + adversarial-verifier       ││
│  │  Phase 5: archive-agent                                ││
│  │                                                        ││
│  └────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Supporting Agents                         │ │
│  │                                                        │ │
│  │  report-writer: 汇总审查报告                             │ │
│  │  adversarial-verifier: 对抗验证                        │ │
│  │  agent_template: agent 通用模板                        │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                Scripts                                 │ │
│  │                                                        │ │
│  │  flow-state.py: 状态管理                               │ │
│  │  spec-tracker.py: Spec 覆盖率检查                      │ │
│  │  adversarial-review.py: 对抗验证编排                   │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Orchestrator（编排器）

**职责**：管理整个 SDD-TDD 流程的生命周期

**关键功能**：
- 初始化状态文件 (`.dev-flow-state.json`)
- 按顺序调度各阶段 agent
- 监控阶段完成状态
- 处理中断和恢复

**不做什么**：
- 不参与具体的代码审查
- 不干涉 agent 的工作方式
- 不修改项目代码

### 2. Phase Agents（阶段代理）

每个阶段一个专门的 agent，职责单一：

#### explore-agent
- **输入**：用户需求描述、现有代码
- **输出**：`explore_report.md`
- **关注**：问题理解、需求分析、风险识别

#### proposal-agent
- **输入**：`explore_report.md`
- **输出**：`proposal.md`（含 Spec 清单）
- **关注**：方案设计、接口定义、Spec 编写

#### apply-agent
- **输入**：`proposal.md`
- **输出**：实现代码、测试代码
- **关注**：TDD 循环（Write → Fail → Implement → Pass → Refactor）

#### review agents (4 个)
- **输入**：实现代码、`proposal.md`
- **输出**：`review-{agent}.json`
- **关注**：各自领域的审查（Correctness/Security/Performance/Test）

#### adversarial-verifier
- **输入**：单个 finding、相关代码
- **输出**：`refuted/confirmed/uncertain`
- **关注**：反驳验证，降低误报

#### archive-agent
- **输入**：所有阶段产物
- **输出**：`archive/<YYYY-MM-DD>_<任务名>.md`
- **关注**：知识沉淀、经验总结

### 3. Supporting Agents（辅助代理）

#### report-writer
- **输入**：`review_summary.json`（已反驳完成）
- **输出**：`review_report.md`
- **关注**：分类汇总、生成可读报告

#### agent_template
- **用途**：所有 agent 的通用模板
- **内容**：输入输出规范、执行约束、质量检查

#### report-format
- **用途**：统一审查报告格式
- **内容**：Finding schema、Severity 定义、Verdict 规则

### 4. Scripts（脚本工具）

均为 Python 3 标准库实现，无外部依赖，跨平台（`python scripts/xxx.py` 调用，无需执行权限）。

#### flow-state.py
- **功能**：管理 `.dev-flow-state.json`
- **命令**：`init`, `advance`, `update`, `show`, `check-phase`
- **用途**：状态持久化、进度跟踪

#### spec-tracker.py
- **功能**：检查 Spec 覆盖率
- **命令**：`check`, `list-specs`, `list-coverage`
- **用途**：验证每个 Spec 是否有对应测试

#### adversarial-review.py
- **功能**：编排对抗验证流程
- **命令**：`collect`, `show-pending`, `record-refutation`
- **用途**：汇总 findings、跟踪反驳状态

## 数据流

### Phase 1 → Phase 2

```
explore-agent
  ├─ 读取：用户需求、现有代码
  ├─ 输出：.sdd-tdd/explore_report.md
  └─ 传递：
      - 问题定义
      - 影响范围
      - 风险点
      - 约束条件
           ↓
proposal-agent
  ├─ 读取：explore_report.md
  ├─ 输出：.sdd-tdd/proposal.md
  └─ 包含：
      - 设计方案
      - Spec 清单
      - 接口定义
```

### Phase 2 → Phase 3

```
proposal-agent
  └─ 输出：Spec-AA, Spec-AB, Spec-AC...
           ↓
apply-agent
  ├─ 读取：proposal.md
  ├─ 遍历每个 Spec：
  │   └─ TDD 循环：
  │       1. Write test for Spec-X
  │       2. Run test → FAIL
  │       3. Implement
  │       4. Run test → PASS
  │       5. Run all tests → PASS
  │       6. Refactor
  ├─ 输出：
  │   - src/*.rs (实现代码)
  │   - tests/*.rs (测试代码)
  └─ 验证：
      - 全量测试通过
      - Spec 覆盖率 100%
```

### Phase 3 → Phase 4

```
apply-agent
  └─ 输出：完整实现 + 测试
           ↓
[并行派发 4 个 reviewer 子 agent]
  ├─ correctness-reviewer → review-correctness.json
  ├─ security-reviewer → review-security.json
  ├─ performance-reviewer → review-performance.json
  └─ test-reviewer → review-test.json
           ↓
python scripts/adversarial-review.py collect
  └─ 生成：review_summary.json
      - multi_evidence_confirmed: ≥2 子 agent 对同一文件报 ERROR（必改）
      - needs_refutation: 单子 agent ERR（需要反驳）
           ↓
[串行处理每个 needs_refutation]
  └─ adversarial-verifier 子 agent
      ├─ 读取：finding + 代码
      ├─ 判断：refuted/confirmed/uncertain
      └─ 调用：python scripts/adversarial-review.py record-refutation
           ↓
report-writer 子 agent
  ├─ 读取：review_summary.json
           ↓
report-writer
  ├─ 读取：review_summary.json
  └─ 输出：review_report.md
```

### Phase 4 → Phase 5

```
(如果 Must-Fix > 0)
  ↓
Mini-Apply 子循环（上限 2 轮）：
  while must_fix_count > 0 and round <= 2:
    apply-agent 子 agent:
      - 输入：Must-Fix findings
      - 输出：修复后的代码
    运行全量测试
    重新 review（只针对修复文件）
    更新 must_fix_count
  （超过 2 轮仍有 Must-Fix → 回退 Phase 2）
  ↓
(当 Must-Fix = 0)
  ↓
archive-agent 子 agent
  ├─ 读取：所有阶段产物
  │   - explore_report.md
  │   - proposal.md
  │   - review_report.md
  │   - 实现代码
  ├─ 输出：
  │   - archive/<YYYY-MM-DD>_<任务名>.md
  └─ 更新：
      - .dev-flow-state.json → archive_path
```

## 状态管理

### .dev-flow-state.json

扁平结构（与 `flow-state.py` 一致，SKILL.md 为唯一真相源）：

```json
{
  "task": "实现用户认证系统",
  "route": "full",
  "current_phase": 4,
  "phases_done": [1, 2, 3],
  "explore_path": ".sdd-tdd/explore_report.md",
  "proposal_path": ".sdd-tdd/proposal.md",
  "apply_log_path": ".sdd-tdd/apply_log.md",
  "review_report_path": ".sdd-tdd/review_report.md",
  "specs_total": 5,
  "specs_done": 5,
  "review_findings": { "error": 2, "warn": 1, "info": 1 },
  "must_fix_total": 2,
  "must_fix_done": 0,
  "review_round": 1,
  "archive_path": "",
  "started_at": "2026-06-17T10:05:30Z",
  "updated_at": "2026-06-17T14:32:00Z"
}
```

### 状态转移

```
init → Phase 1 (in_progress) → completed → advance
                                              ↓
                              Phase 2 (in_progress) → completed → advance
                                                                      ↓
                                                      Phase 3 (in_progress) → ...
```

## 文件布局

```
project/
├── .claude/skills/sdd-tdd-paradigm/     # 技能安装目录
│   ├── SKILL.md
│   ├── agents/
│   │   ├── agent_template.md
│   │   ├── report-format.md
│   │   ├── explore-agent.md
│   │   ├── proposal-agent.md
│   │   ├── apply-agent.md
│   │   ├── correctness-reviewer.md
│   │   ├── security-reviewer.md
│   │   ├── performance-reviewer.md
│   │   ├── test-reviewer.md
│   │   ├── adversarial-verifier.md
│   │   ├── report-writer.md
│   │   └── archive-agent.md
│   └── scripts/
│       ├── flow-state.py
│       ├── spec-tracker.py
│       └── adversarial-review.py
│
├── .sdd-tdd/                             # 运行时状态（不提交到 Git）
│   ├── .dev-flow-state.json
│   ├── explore_report.md
│   ├── proposal.md
│   ├── review-*.json
│   ├── review_summary.json
│   └── review_report.md
│
├── src/                                   # 项目源代码
│   ├── auth.rs
│   └── main.rs
│
├── tests/                                 # 项目测试
│   └── auth_test.rs
│
└── archive/                               # 任务归档
    └── 2026-06-17_user-auth.md
```

## 扩展机制

### 添加新的 Phase

1. 创建新的子 agent 文件：`agents/{new-phase}-agent.md`
2. 更新 `orchestrator.md`，添加新阶段的调度逻辑
3. 更新 `flow-state.py`，调整阶段编号（`LAST_PHASE`）
4. 更新 `SKILL.md`，描述新阶段（SKILL.md 为唯一真相源）

### 添加新的 Reviewer

1. 创建新的 reviewer 子 agent：`agents/{domain}-reviewer.md`
2. 更新 `report-format.md`，添加新的 agent 前缀
3. 更新 `orchestrator.md`，在 Phase 4 并行派发新 reviewer
4. 更新 `adversarial-review.py`（如果有特殊处理）

### 添加新的脚本

1. 创建脚本文件：`scripts/{new-tool}.py`（Python 3 标准库）
2. 在文档中说明用途和用法
3. 被相应子 agent 或 orchestrator 调用（`python scripts/{new-tool}.py`，无需执行权限）

## 性能考量

### 为什么 Review 阶段要并行？

4 个 reviewer 独立工作，没有依赖关系。串行执行需要 4 倍时间（可能 20 分钟），并行只需 5 分钟。

### 为什么对抗验证要串行？

每个反驳可能依赖于之前的反驳结果（例如理解上下文）。串行确保质量，避免并发冲突。

### 为什么 Mini-Apply 是循环？

修复一个问题可能引入新问题。循环直到稳定（Must-Fix = 0）。但有 **2 轮上限**防止死循环；超过则回退 Phase 2。

## 安全考量

### 脚本执行

脚本为 Python 3 标准库实现，用 `python scripts/xxx.py` 调用，**无需执行权限**，跨平台。

### 状态文件隔离

`.sdd-tdd/` 目录应该被 `.gitignore` 排除，避免：
- 临时状态污染 Git 历史
- 不同开发者的状态冲突

### 代码修改范围

Apply 子 agent 只修改：
- `src/` 目录（实现代码）
- `tests/` 目录（测试代码）

不会修改：
- 配置文件（除非 Spec 明确要求）
- 文档文件（归档 phase）
- 外部依赖

## 容错设计

### Agent 异常

子 agent 运行时间不受限制。若执行失败：
- 标记为 failed
- 记录到 `.dev-flow-state.json`
- orchestrator 决定是否继续

### 测试失败

Apply 子 agent 最多尝试 2 轮修复，失败后：
- 回退到 Phase 2（Proposal）
- 记录失败原因

### 状态损坏

如果 `.dev-flow-state.json` 损坏：
- 尝试从产物文件推断阶段
- 重建状态文件
- 继续流程

## 与外部系统集成

### Git

SDD-TDD 不强制 Git 工作流，但推荐：
- 每个任务一个分支
- 阶段性 commit（Design, Implementation, Review, Archive）
- 归档后合并回主分支

### CI/CD

可在 CI 中运行 spec-tracker 检查：

```yaml
# .github/workflows/sdd-tdd.yml
name: SDD-TDD Check
on: [push]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check Spec Coverage
        run: |
          python skills/sdd-tdd-paradigm/scripts/spec-tracker.py check .sdd-tdd/proposal.md tests
```

### IDE 插件

可以开发 VSCode 插件：
- 可视化当前阶段
- 快速查看 Spec 覆盖率
- 高亮 Must-Fix findings

（当前未实现，欢迎贡献）

## 未来方向

1. **GUI 可视化工具**：拖拽式流程编排
2. **分布式执行**：reviewer agents 在不同机器运行
3. **机器学习**：从历史项目中学习 common pitfalls
4. **多语言支持**：当前主要针对 Rust，可扩展到 Go/Python/TypeScript
5. **IDE 深度集成**：实时显示 Spec 覆盖率、Findings 高亮
