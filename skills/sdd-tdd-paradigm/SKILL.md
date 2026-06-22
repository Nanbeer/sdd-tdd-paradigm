---
name: sdd-tdd-paradigm
description: Use when 用户提出涉及多文件变更、公开接口签名变更、数据模型变更、架构变更或第三方集成的开发任务，需要在写代码前先定义可测试规格并用 TDD 实现，再经多视角审查与归档沉淀知识。小改动（≤3 文件且无上述变更）不触发本技能。
---

# SDD × TDD 开发范式

## 技能概述

本技能实现一套多阶段开发流程，将规格驱动设计（SDD）与测试驱动开发（TDD）结合：先用规格定义"测什么"，再用 TDD 实现"怎么测过"，最后用多视角审查验证"规格是否被正确实现"。

根据变更规模自适应选择路径：

- **大改动**（>3 文件，或涉及接口/数据模型/架构/第三方集成变更）→ 完整 5 阶段流程
- **小改动**（≤3 文件且无上述变更）→ 普通流程（见下文"路由判定"）

## 核心原则

1. **决策前置（Decision First）**：写代码前先理解问题（Explore）、设计方案（Proposal），确保"测的是对的东西"。
2. **规格落地为测试（Spec Becomes Test）**：Proposal 中每个 Spec 必须是可测试的行为描述；Apply 阶段按 Spec 逐个 TDD 实现。规格不是文档，是有测试证明的行为契约。
3. **多视角交叉验证（Multi-Perspective Verification）**：Review 阶段用 4 个专精子 agent 从不同维度审查，每个子 agent 注意力不被其他维度稀释；通过对抗验证过滤误报。
4. **知识沉淀（Knowledge Archive）**：每个大改动强制输出结构化的归档条目，形成可检索的组织知识库。

## 执行模型（重要）

本技能由**主 Claude 担任编排者（orchestrator）**，用 `Agent` 工具按阶段派发**子 agent**执行实际工作。每个 `agents/*.md` 文件是对应子 agent 的 **prompt 主体**。

### 派发方式

收到大改动任务后，主 Claude 的工作是：

1. 判定变更规模（路由）
2. 初始化流程状态（`python scripts/flow-state.py init`）
3. **逐阶段派发子 agent**：读取对应 `agents/<phase>-agent.md`，将其内容作为子 agent 的 prompt，附上阶段输入，用 `Agent` 工具派发
4. 子 agent 产出阶段产物后，主 Claude 验证完成标志、推进状态（`flow-state.py advance`）、进入下一阶段

派发模板：

```
Agent 工具调用:
  subagent_type: "general-purpose"
  prompt: <agents/explore-agent.md 的完整内容>
          + "\n\n## 本次任务输入\n" + <用户需求 / 上一阶段产物路径>
  description: "Phase 1: Explore"
```

子 agent 拥有完整工具权限（读码、写文件、跑测试），独立完成本阶段工作。主 Claude **不干涉**子 agent 的具体工作方式，只负责调度、状态推进、完成标志校验。

### Phase 4 的并行与隔离

- **4 个 reviewer 子 agent 并行派发**：在**单条消息**里发起 4 个 `Agent` 工具调用（correctness / security / performance / test-completeness），它们同时运行、互不可见。这是真正的注意力隔离——每个子 agent 是独立上下文，天然不会读取其他 reviewer 的输出。
- **对抗验证用独立 verifier 子 agent**：对单 agent 标记的 ERROR，派发一个独立的 `adversarial-verifier` 子 agent 尝试反驳，与发现该问题的 reviewer 处于不同上下文。

### 小改动路径

小改动**不派发子 agent**，主 Claude 直接执行普通流程：先写失败测试→最少实现→重构 + 全量回归。本技能正文其余部分针对大改动的完整流程。

---

## 路由判定

收到开发任务时，立即判断变更规模。**满足任一即大改动**：

- 预计影响 > 3 个文件
- 涉及公开接口签名变更（新增/修改/删除对外 API）
- 涉及数据模型变更（表结构、字段、schema）
- 涉及架构变更（新增模块、改变模块间调用关系）
- 涉及第三方系统集成
- 用户明确要求走完整流程

判定依据是**变更的语义性质**（是否动接口/数据模型/架构），而非任务描述里是否出现特定关键词。拿不准时，向用户确认或默认按大改动处理。

- **大改动** → 初始化状态，进入 Phase 1（Explore）
- **小改动** → 告知用户走普通流程（先测试后实现 + 全量回归），不启动 5 阶段

---

## 完整 5 阶段流程

### Phase 1: Explore（探索）

- **子 agent**：`agents/explore-agent.md`
- **输入**：用户需求描述、项目根目录
- **活动**：读现有代码、分析 TODO/FIXME、识别影响范围与约束、列出风险点与关键决策点
- **输出**：`.sdd-tdd/explore_report.md`
- **完成标志**：`explore_report.md` 存在且含必需章节（任务描述、现有代码分析、影响范围、约束条件、风险点、关键决策点）

### Phase 2: Proposal（方案）

- **子 agent**：`agents/proposal-agent.md`
- **输入**：`.sdd-tdd/explore_report.md`
- **活动**：做技术决策（每个决策记录选项/理由/权衡）、设计 Spec 清单（每个 Spec 含前置条件/操作/预期结果/对应测试名/路径类型，覆盖正面/边界/负面三路径）、规划实现顺序
- **输出**：`.sdd-tdd/proposal.md`
- **完成标志**：`proposal.md` 存在、含 Spec 清单、每个 Spec 可直接翻译成一个测试用例
- **注意**：本阶段**不**运行 spec-tracker——测试尚未编写，校验无意义。Spec→Test 覆盖校验在 Phase 3 末尾进行。

### Phase 3: Apply（TDD 实现）

- **子 agent**：`agents/apply-agent.md`
- **输入**：`.sdd-tdd/proposal.md`
- **活动**：对每个 Spec 执行 TDD 循环（Red→Green→Refactor），详见 apply-agent.md
- **输出**：实现代码、测试代码、`.sdd-tdd/apply_log.md`
- **完成标志**：
  - 所有 Spec 都有对应测试
  - 全量测试 100% 通过
  - `python scripts/spec-tracker.py check .sdd-tdd/proposal.md <tests_dir>` 通过（Spec→Test 映射完整）
  - 产出 `apply_log.md`

### Phase 4: Review（多 Agent 交叉验证）

主 Claude 编排 5 个子步骤（详见 `agents/orchestrator.md`）：

- **4a. Mini-Explore**：主 Claude 列出变更文件、识别高风险代码段
- **4b. 4 Agent 并行审查**：并行派发 correctness / security / performance / test-completeness 四个子 agent，各自输出 `review-<agent>.json`
- **4c. 对抗验证**：`python scripts/adversarial-review.py collect .sdd-tdd/` 汇总 findings；对单 agent 标记的 ERROR，派发独立 `adversarial-verifier` 子 agent 尝试反驳
- **4d. 汇总分级**：`agents/report-writer.md` 子 agent 生成 `.sdd-tdd/review_report.md`，分 Must-Fix / Should-Fix / Info
- **4e. Mini-Apply（TDD 修复）**：对 Must-Fix 逐个 TDD 修复（先补暴露问题的测试→改代码→全量回归）

**输出**：`.sdd-tdd/review_report.md` + 修复代码
**完成标志**：对抗验证完成、Must-Fix = 0、全量测试仍通过

#### 4 个 reviewer 的职责边界

| Agent | 领域 | 关注点 |
|-------|------|--------|
| Correctness | 逻辑正确性 | 边界条件、并发安全、错误处理、状态一致性 |
| Security | 安全性 | 注入、越权、数据泄露、输入校验、认证绕过 |
| Performance | 性能 | N+1 查询、内存分配、阻塞操作、资源泄漏 |
| Test-Completeness | 测试完备性 | Spec→Test 映射、正面/边界/负面路径覆盖 |

每个 reviewer 是独立子 agent，只从自己的领域视角审查，不读取其他 reviewer 的输出。

#### 对抗验证规则

- **多证据确认**（≥2 个不同 agent 对同一文件报告 ERROR）→ 跳过反驳，直接标 Must-Fix
- **单 agent ERROR** → 派发独立 verifier 子 agent 尝试反驳
  - 反驳成功（refuted）→ 降级为 WARN
  - 反驳失败（confirmed）→ 确认 Must-Fix
  - 不确定（uncertain）→ 保留，标"需人工判断"
- verifier 必须引用具体代码作为反驳证据，不允许仅凭"看起来没问题"反驳

#### Mini-Apply 修复轮次上限

**2 轮**。超过 2 轮仍有 Must-Fix → 回退到 Phase 2（Proposal），说明初始方案有根本问题，应在错误基础上重新设计而非继续修补。

### Phase 5: Archive（归档）

- **子 agent**：`agents/archive-agent.md`
- **输入**：explore_report / proposal / apply_log / review_report
- **活动**：汇总全流程、提取关键决策与经验、生成结构化归档条目
- **输出**：`archive/<YYYY-MM-DD>_<任务名-kebab-case>.md`
- **完成标志**：归档条目产出，含问题定义/方案选择/关键决策/经验教训

---

## 流程状态管理

每个开发任务在项目根目录创建 `.sdd-tdd/.dev-flow-state.json`，用 `python scripts/flow-state.py` 管理。**schema（扁平结构，唯一真相源）**：

```json
{
  "task": "<任务描述>",
  "route": "full",
  "current_phase": 1,
  "phases_done": [],
  "base_commit": "",
  "explore_path": ".sdd-tdd/explore_report.md",
  "proposal_path": ".sdd-tdd/proposal.md",
  "apply_log_path": ".sdd-tdd/apply_log.md",
  "review_report_path": ".sdd-tdd/review_report.md",
  "specs_total": 0,
  "specs_done": 0,
  "review_findings": { "error": 0, "warn": 0, "info": 0 },
  "must_fix_total": 0,
  "must_fix_done": 0,
  "review_round": 0,
  "archive_path": "",
  "started_at": "<ISO8601>",
  "updated_at": "<ISO8601>"
}
```

**中断恢复**：流程中断后，主 Claude 读取状态文件，按 `current_phase` 继续，不重做已完成阶段。详见 `agents/orchestrator.md`。

---

## 自检触发器

### Explore 阶段
- "我已经理解问题了" → 是否读过代码？是否识别了影响范围？
- "影响范围很小" → 是否只看了直接相关文件？是否考虑了间接依赖？

### Proposal 阶段
- "方案已经很完善了" → 是否有 Spec 清单？每个 Spec 是否可测试？
- "这个 Spec 太简单了不用写" → 这个 Spec 对应的测试是否已经在写了？

### Apply 阶段
- "测试已经通过了不用写了" → 测试是在实现之前写的吗？
- "这个 Spec 太简单了不用测试" → 这个 Spec 的边界条件和负面路径有测试吗？
- "重构会破坏测试" → 重构是否改变了外部行为？若是，说明 Spec 定义有问题

### Review 阶段
- "看起来没问题不用仔细查" → 4 个子 agent 是否都派发了？对抗验证是否完整？
- "ERROR 太多了处理不过来" → 对抗验证是否有效过滤了误报？

### Archive 阶段
- "这个决策太明显了不用记录" → 决策的理由是否清晰？已知权衡是否记录？
- "归档条目太长了" → 只记录关键决策和学习，省略显而易见的步骤

---

## 与其他技能的关系

- **TDD 循环**：Phase 3 (Apply) 与小改动普通流程使用标准的 TDD 循环（Red→Green→Refactor）
- **code-review**：Phase 4 (Review) 的 4 个子 agent 借鉴 code-review 的多视角审查模式
- **brainstorming**：Phase 1 (Explore) 可使用 brainstorming 技能识别风险点

## 项目结构

部署后的技能目录：

```
~/.claude/skills/sdd-tdd-paradigm/   （或项目 .claude/skills/ 下）
├── SKILL.md                          # 主技能文件（本文件，唯一真相源）
├── agents/
│   ├── orchestrator.md               # 主 Claude 编排指南
│   ├── explore-agent.md              # Phase 1 子 agent prompt
│   ├── proposal-agent.md             # Phase 2 子 agent prompt
│   ├── apply-agent.md                # Phase 3 子 agent prompt
│   ├── correctness-reviewer.md       # Phase 4 子 agent prompt
│   ├── security-reviewer.md          # Phase 4 子 agent prompt
│   ├── performance-reviewer.md       # Phase 4 子 agent prompt
│   ├── test-reviewer.md              # Phase 4 子 agent prompt
│   ├── adversarial-verifier.md       # 对抗验证子 agent prompt
│   ├── report-writer.md              # 报告汇总子 agent prompt
│   ├── archive-agent.md              # Phase 5 子 agent prompt
│   ├── agent_template.md             # agent 通用模板
│   └── report-format.md              # 审查 JSON 输出格式规范
└── scripts/
    ├── flow-state.py                 # 流程状态管理
    ├── spec-tracker.py               # Spec→Test 追踪
    └── adversarial-review.py         # 对抗验证编排
```

使用技能时，项目目录下自动创建：

```
<项目目录>/
├── .sdd-tdd/
│   ├── .dev-flow-state.json          # 流程状态
│   ├── explore_report.md             # Explore 产出
│   ├── proposal.md                   # Proposal 产出
│   ├── apply_log.md                  # Apply 日志
│   ├── review-<agent>.json           # 各 reviewer 输出
│   ├── review_summary.json           # 对抗验证汇总
│   └── review_report.md              # 最终审查报告
└── archive/
    └── <YYYY-MM-DD>_<任务名>.md       # 归档条目
```

## 适用场景

### 推荐完整流程
- 新功能开发（用户认证、支付网关）
- 架构重构（数据库迁移、API 升级）
- 性能优化（需重新设计数据流或缓存策略）
- 复杂 bug 修复（涉及多模块、多层抽象）

### 推荐普通流程
- 单文件小修改（改配置、改文案）
- 明确的 bug 修复（已知根因，修复清晰）
- 测试补充、文档更新

## 常见问题

**Q: 为什么小改动不走完整流程？**
A: 完整流程的开销（5 份报告 + 4 个子 agent 审查）对小改动过重。普通流程（先测试后实现 + 全量回归）更敏捷。

**Q: 4 个 reviewer 子 agent 会不会互相干扰？**
A: 不会。它们是独立子 agent，各自独立上下文，互不可见，天然注意力隔离。

**Q: 对抗验证会不会误杀真实问题？**
A: 会。所以 verifier 被严格要求：必须引用代码证据反驳，不允许仅凭"看起来没问题"。找不到反驳证据必须承认反驳失败。

**Q: 修复轮次为什么限制 2 轮？**
A: 超过 2 轮仍有问题，说明 Proposal 有根本问题。应回退重新设计，而非在错误基础上继续修补。

**Q: Archive 真的有人看吗？**
A: 归档价值是长期积累。类似任务出现时可检索复用决策与经验。短期没人看，长期是组织知识资产。
