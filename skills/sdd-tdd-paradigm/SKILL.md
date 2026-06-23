---
name: sdd-tdd-paradigm
description: Use when 用户提出涉及多文件变更、公开接口签名变更、数据模型变更、架构变更或第三方集成的开发任务，需要在写代码前先定义可测试规格并用 TDD 实现，再经多视角审查与归档沉淀知识。v2.0 新增内置 Grilling 协议（无情追问）、铁律体系（R0-R5）、文档同步 Gate、高风险核验协议。小改动（≤3 文件且无上述变更）不触发本技能。
---

# SDD × TDD 开发范式 v2.0

## 技能概述

本技能实现一套多阶段开发流程，将规格驱动设计（SDD）与测试驱动开发（TDD）结合：先用规格定义"测什么"，再用 TDD 实现"怎么测过"，最后用多视角审查验证"规格是否被正确实现"。

根据变更规模自适应选择路径：

- **大改动**（>3 文件，或涉及接口/数据模型/架构/第三方集成变更）→ 完整 5 阶段流程（含 Grilling、铁律检查、文档同步 Gate）
- **小改动**（≤3 文件且无上述变更）→ 普通流程（见下文"路由判定"）

## 核心原则

1. **决策前置（Decision First）**：写代码前先理解问题（Explore）、设计方案（Proposal），确保"测的是对的东西"。
2. **规格落地为测试（Spec Becomes Test）**：Proposal 中每个 Spec 必须是可测试的行为描述；Apply 阶段按 Spec 逐个 TDD 实现。规格不是文档，是有测试证明的行为契约。
3. **多视角交叉验证（Multi-Perspective Verification）**：Review 阶段用 4 个专精子 agent 从不同维度审查，每个子 agent 注意力不被其他维度稀释；通过对抗验证过滤误报。
4. **知识沉淀（Knowledge Archive）**：每个大改动强制输出结构化的归档条目，形成可检索的组织知识库。
5. **追问先于放行（Question Before Proceeding）**：在两个关键节点（Explore→Proposal、Proposal→Apply）通过 Grilling 协议逼出隐藏假设和边界漏洞，不满足退出条件不放行。

## Iron Rules（铁律）v2.0

以下 6 条铁律是**强制约束**，不可跳过。违反任何一条，流程中止或回退。

| Rule | 内容 | 执行点 | 违规后果 |
|------|------|--------|---------|
| **R0** | 技能必调 | 路由判定 | 匹配大改动条件但绕过技能 → 拒绝执行 |
| **R1** | 事实先于讨论 | P1→P2 | explore_report.md 无代码证据 → 不能 advance |
| **R2** | 场景先于代码 | P2→P3 | proposal.md 中 Spec 不可测试 → 不能 advance |
| **R3** | 核验先于信任 | P3 高风险任务 | 高风险任务未独立核验 → 不能 advance |
| **R4** | 规范高于代码 | P4→P5 | 代码与 spec 不一致且未回写 → Gate FAIL |
| **R5** | 追问先于放行 | Grilling 1 & 2 | G4 退出条件未满足 → 不能 advance |

铁律合规状态通过 `python scripts/flow-state.py iron-check <rule_id> pass|fail "<reason>"` 记录在 state 文件中。

---

## Grilling Protocol（🔥 内置无情追问）v2.0

Grilling 由**主 Claude 直接执行**（不派发子 Agent），在两个关键节点对方案进行无情拷问，逼出隐藏假设与边界漏洞。此协议替代旧版"软性自检触发器"。

### Grilling 点 1：Explore → Proposal（拷问理解）

**时机**：`explore_report.md` 验证通过后

**目标**：确保对问题的理解不是"看起来很对"，而是经得起拷问。

**重点追问方向**：
- 标为"约束"的条件真的是硬约束，还是可以挑战的假设？
- 识别为"低风险"的点真的低吗？反例是什么？
- 影响范围是否只看了直接依赖，忽略了间接依赖（2 层深度）？
- "类似现有功能"——具体是哪段代码？差异点是什么？
- "现有逻辑可以复用"——现有逻辑的哪一段？它真的适用吗？

### Grilling 点 2：Proposal → Apply（拷问方案/Spec）

**时机**：`proposal.md` 验证通过后

**目标**：确保 Spec 是可证伪的、方案是经得起反例拷问的。

**重点追问方向**：
- 每个 Spec 是否可证伪？（你能写一个测试让它失败吗？）
- Spec 覆盖了正面/边界/负面三条路径吗？
- 技术决策的"理由"是真的理由，还是只是重述选择？有没有其他备选方案？
- Spec 之间的依赖顺序合理吗？有没有"先改 DB schema 再改读取代码"这种顺序倒置？
- Grilling 点 1 逼出的边界场景，是否在 Spec 中全部覆盖了？

### Grilling 执行规则

**G1. 一次一问，禁止连珠炮**：每轮只抛 1 个问题。用户回答后，先评估回答是否触发 G2/G3，再决定下一问。

**G2. 禁止接受模糊词**：回答中出现以下词必须追问"具体是什么/怎么衡量/边界在哪"：
- "一般来说 / 通常 / 大部分情况" → 反例是什么？
- "性能会好 / 应该够快" → 指标是多少？怎么测？
- "差不多 / 大概 / 几个" → 精确数字或范围
- "后续可以优化 / 以后再说" → 现在不做的代价是什么？
- "复用现有逻辑" → 现有逻辑的哪一段？文件:行号？

**G3. 必须给出反例**：每个关键设计点，grilling 必须至少构造 1 个反例/边界场景让用户回答"这种情况怎么办"：
- 并发场景、失败场景（下游超时/DB 死锁）、数据边界（空集合/超长字符串/负数）
- 状态机边界（重复触发/乱序到达/终态后操作）

**G4. 退出条件（全部满足才能结束）**：
- [ ] 所有模糊词已被逼出具体定义
- [ ] 每个关键决策点至少有 1 个反例被回答且答案自洽
- [ ] 用户对每个回答给出"可证伪"的依据（数据/代码引用/测试场景）
- [ ] 主 agent 复述 grilling 结论，用户确认"无遗漏"

未满足时继续追问。用户主动喊停时，把未解决问题写入 state 的 `grilling.unresolved`，标注风险。

**G5. grilling 语气**：直接、尖锐、不客套。不说"您说得对"，只说"这里有个洞"。引用用户原话作为追问锚点。

### Grilling 完成

- Grilling 点 1 完成：`python scripts/flow-state.py grill-complete 1`
- Grilling 点 2 完成：`python scripts/flow-state.py grill-complete 2`

---

## 执行模型（重要）

本技能由**主 Claude 担任编排者（orchestrator）**，用 `Agent` 工具按阶段派发**子 agent** 执行实际工作。每个 `agents/*.md` 文件是对应子 agent 的 **prompt 主体**。

### 派发方式

收到大改动任务后，主 Claude 的工作是：

1. 判定变更规模（路由）
2. 初始化流程状态（`python scripts/flow-state.py init`）
3. **逐阶段派发子 agent**：读取对应 `agents/<phase>-agent.md`，将其内容作为子 agent 的 prompt，附上阶段输入，用 `Agent` 工具派发
4. 子 agent 产出阶段产物后，主 Claude 验证完成标志、执行 Grilling / 铁律检查 / 同步 Gate，推进状态（`flow-state.py advance`）、进入下一阶段

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

## 完整 5 阶段流程 v2.0

```
Phase 1: Explore
    ↓
🔥 Grilling 点 1（拷问理解，G1-G5）
    ↓
Phase 2: Proposal
    ↓
🔥 Grilling 点 2（拷问方案/Spec，G1-G5）+ Document Sync Gate 2→3
    ↓
Phase 3: Apply (TDD) + 高风险核验 + Sync Gate 3→4
    ↓
Phase 4: Review (4 Agent 并行 + 对抗验证) + Sync Gate 4→5
    ↓
Phase 5: Archive
```

### Phase 1: Explore（探索）

- **子 agent**：`agents/explore-agent.md`
- **输入**：用户需求描述、项目根目录
- **活动**：读现有代码、分析 TODO/FIXME、识别影响范围与约束、列出风险点与关键决策点。区分"事实"（有代码引用）与"假设"（需 Grilling 验证）。
- **输出**：`.sdd-tdd/explore_report.md`
- **完成标志**：`explore_report.md` 存在且含必需章节（任务描述、现有代码分析、影响范围、约束条件、风险点、关键决策点）
- **铁律 R1**：确认报告中有代码引用作为事实基础

#### 🔥 Grilling 点 1（Phase 1 → Phase 2）

Explore 完成后，主 Claude 读取 `explore_report.md`，对关键决策点、风险点、约束条件执行 Grilling 协议（G1-G5）。退出条件全部满足后 `grill-complete 1`，用户确认 Explore 摘要后 advance。

### Phase 2: Proposal（方案）

- **子 agent**：`agents/proposal-agent.md`
- **输入**：`.sdd-tdd/explore_report.md` + Grilling 点 1 结论
- **活动**：做技术决策（每个决策记录选项/理由/权衡）、设计 Spec 清单（每个 Spec 含前置条件/操作/预期结果/对应测试名/路径类型，覆盖正面/边界/负面三路径）、规划实现顺序。Proposal-agent 的 Spec 设计要求每项**可证伪**——能写出一个使其失败的测试。
- **输出**：`.sdd-tdd/proposal.md`
- **完成标志**：`proposal.md` 存在、含 Spec 清单、每个 Spec 可直接翻译成一个测试用例
- **注意**：本阶段**不**运行 spec-tracker——测试尚未编写，校验无意义。

#### 🔥 Grilling 点 2 + Document Sync Gate（Phase 2 → Phase 3）

主 Claude 读取 `proposal.md`，对每个 Spec 和技术决策执行 Grilling 协议。Grilling 完成后执行 **Document Sync Gate 2→3**：

| 检查项 | 证据 | 结果 |
|--------|------|------|
| Explore 关键决策点在 proposal 中有回应 | `explore_report.md` Decision-* vs `proposal.md` | PASS/FAIL |
| 每个 Spec 可映射到一个测试 | 逐个 Spec 的"对应测试"字段 | PASS/FAIL |
| Spec 覆盖正面/边界/负面三类路径 | Spec 清单路径类型分布 | PASS/FAIL |
| Grilling 点 2 退出条件满足 | G4 checklist 全 ✓ | PASS/FAIL |

全部 PASS 后 `grill-complete 2`、`sync-gate gate_2_to_3 pass 0`，用户确认后 advance。

### Phase 3: Apply（TDD 实现）

- **子 agent**：`agents/apply-agent.md`
- **输入**：`.sdd-tdd/proposal.md` + Grilling 点 2 结论
- **活动**：对每个 Spec 执行 TDD 循环（Red→Green→Refactor），详见 apply-agent.md。apply_log.md 必须包含 **Verification Block**（测试命令、exit code、文件列表、风险级别）。
- **输出**：实现代码、测试代码、`.sdd-tdd/apply_log.md`
- **完成标志**：
  - 所有 Spec 都有对应测试
  - 全量测试 100% 通过
  - `python scripts/spec-tracker.py check .sdd-tdd/proposal.md <tests_dir>` 通过
  - 产出 `apply_log.md`（含 Verification Block）

#### 高风险核验（铁律 R3）

Apply 完成后，若任务满足**任一**高风险条件，主 Claude 执行独立核验：
- 删除/重命名/大规模 refactor
- 触及 DB schema / 协议层
- 改动 ≥5 文件（批量重命名不计）
- 用户在 spec 标注 `risk: high`
- 涉及外部 API / 网络请求
- 改动启动流程 / 全局配置

**核验动作**：
1. 独立重跑 apply_log 中 Verification Block 报告的测试命令
2. 抽查 1-2 个文件 diff，确认与 apply_log 一致
3. `git status` 确认无未汇报改动

用 `flow-state.py verify-record <task_name> pass|fail "<details>"` 记录。

#### Document Sync Gate 3→4

| 检查项 | 证据 | 结果 |
|--------|------|------|
| spec-tracker 覆盖率 100% | `spec-tracker.py check` exit 0 | PASS/FAIL |
| 全量测试通过 | apply_log 或测试输出 | PASS/FAIL |
| 高风险核验完成 | flow-state show 核验项 | PASS/FAIL/NA |

全部 PASS 后 `sync-gate gate_3_to_4 pass 0`，advance。

### Phase 4: Review（多 Agent 交叉验证）

主 Claude 编排 5 个子步骤（详见 `agents/orchestrator.md`）：

- **4a. Mini-Explore**：主 Claude 列出变更文件、识别高风险代码段
- **4b. 4 Agent 并行审查**：并行派发 correctness / security / performance / test-completeness 四个子 agent，各自输出 `review-<agent>.json`
- **4c. 对抗验证**：`python scripts/adversarial-review.py collect .sdd-tdd/` 汇总 findings；对单 agent 标记的 ERROR，派发独立 `adversarial-verifier` 子 agent 尝试反驳
- **4d. 汇总分级**：`agents/report-writer.md` 子 agent 生成 `.sdd-tdd/review_report.md`，分 Must-Fix / Should-Fix / Info
- **4e. Mini-Apply（TDD 修复）**：对 Must-Fix 逐个 TDD 修复（先补暴露问题的测试→改代码→全量回归）

**输出**：`.sdd-tdd/review_report.md` + 修复代码
**完成标志**：对抗验证完成、Must-Fix = 0、全量测试仍通过

#### Document Sync Gate 4→5（铁律 R4）

| 检查项 | 证据 | 结果 |
|--------|------|------|
| Must-Fix = 0 | review_report.md | PASS/FAIL |
| 代码变更已反映到 spec（如有） | proposal.md vs 实际代码 | PASS/FAIL/NA |
| 全量测试仍通过 | 测试输出 | PASS/FAIL |

全部 PASS 后 `sync-gate gate_4_to_5 pass 0`，advance。

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
- **输入**：explore_report / proposal / apply_log / review_report + Grilling 结论 + 铁律合规记录
- **活动**：汇总全流程、提取关键决策与经验（含 Grilling 逼出的边界和反例）、生成结构化归档条目
- **输出**：`archive/<YYYY-MM-DD>_<任务名-kebab-case>.md`
- **完成标志**：归档条目产出，含问题定义/方案选择/关键决策/Grilling 解决的决策/经验教训

---

## Deviation Detection（偏离检测）v2.0

当流程偏离时，主 Claude 立即提醒：

| 偏离场景 | 提醒话术 |
|---------|---------|
| 用户试图跳过 Explore 直接写方案 | "当前流程：Phase 1/5。R1 铁律：事实先于讨论。请先完成 Explore。" |
| 用户试图跳过 Proposal 直接写代码 | "当前流程：Phase 2/5。R2 铁律：场景先于代码。请先完成 Proposal。" |
| 子 agent 产出缺少完成标志 | "Phase X 完成标志未满足：<具体缺失项>。请重新派发。" |
| Grilling 被跳过 | "R5 铁律：追问先于放行。Grilling 退出条件未满足，不能 advance。" |
| Grilling 演变成自由讨论 | "Grilling 是拷问不是聊天。回到 G2：你刚才的回答'<引用>'是模糊词，请具体定义。" |

---

## Interruption Protocol（中断协议）v2.0

用户在 TDD 循环（Phase 3）中途追加意见时：

1. 立即停止启动新 subagent；当前 subagent 完成后不再继续下一 task
2. `python scripts/flow-state.py interrupt-pause`
3. `git status` + diff 摘要，列出当前未提交改动
4. 询问用户三选一：
   - **A. 保留改动**：基于现状修 plan/proposal
   - **B. 回滚改动**：`git checkout -- <files>` 后重做
   - **C. 暂存改动**：`git stash` 备份后重做
5. 未获用户选择前，**不得**自动删除或覆盖已有改动
6. 恢复时 `python scripts/flow-state.py interrupt-resume`

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

  "grilling": {
    "phase1_complete": false,
    "phase2_complete": false,
    "phase1_issues": [],
    "phase2_issues": [],
    "unresolved": []
  },
  "iron_rules": {
    "r0_compliance": true,
    "r1_to_r5_checks": {},
    "violations": []
  },
  "sync_gates": {
    "gate_2_to_3": {"passed": false, "fails": 0, "checked_at": ""},
    "gate_3_to_4": {"passed": false, "fails": 0, "checked_at": ""},
    "gate_4_to_5": {"passed": false, "fails": 0, "checked_at": ""}
  },
  "verification": {
    "high_risk_tasks": [],
    "failures": [],
    "last_verification": ""
  },
  "interruption": {
    "paused_at": "",
    "stashed": false,
    "tbd_action": ""
  },

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

**中断恢复**：流程中断后，主 Claude 读取状态文件，按 `current_phase` 继续。**Self-Check 强制规则**：进入新步骤前必须先 read state 文件并显式声明当前位置。

---

## 自检提醒（软性）

以下提醒保留了旧版自检触发器的精神，但已被铁律（R0-R5）和 Grilling 协议（G1-G5）覆盖了最关键的部分。余下的作为软性提醒保留：

### Explore 阶段
- "我已经理解问题了" → 是否读过代码？是否识别了影响范围（≥2 层深度）？

### Proposal 阶段
- "这个 Spec 太简单了不用写" → 是否真的零测试也能验证？边界条件和负面路径有没有覆盖？

### Apply 阶段
- "测试已经通过了不用写了" → 测试是在实现**之前**写的吗？
- "重构会破坏测试" → 重构是否改变了外部行为？若是，说明 Spec 定义有问题

### Review 阶段
- "ERROR 太多了处理不过来" → 对抗验证是否有效过滤了误报？

### Archive 阶段
- "这个决策太明显了不用记录" → 决策的理由是否清晰？已知权衡是否记录？

---

## 与其他技能的关系

- **TDD 循环**：Phase 3 (Apply) 与小改动普通流程使用标准的 TDD 循环（Red→Green→Refactor）
- **code-review**：Phase 4 (Review) 的 4 个子 agent 借鉴 code-review 的多视角审查模式
- **brainstorming**：Phase 1 (Explore) 可使用 brainstorming 技能识别风险点

## 项目结构

部署后的技能目录：

```
~/.claude/skills/sdd-tdd-paradigm/   （或项目 .claude/skills/ 下）
├── SKILL.md                          # 主技能文件（本文件，唯一真相源）v2.0
├── agents/
│   ├── orchestrator.md               # 主 Claude 编排指南 v2.0
│   ├── explore-agent.md              # Phase 1 子 agent prompt
│   ├── proposal-agent.md             # Phase 2 子 agent prompt
│   ├── apply-agent.md                # Phase 3 子 agent prompt（含核验块）
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
    ├── flow-state.py                 # 流程状态管理 v2.0
    ├── spec-tracker.py               # Spec→Test 追踪
    ├── adversarial-review.py         # 对抗验证编排
    └── grill-check.py                # Grilling 退出条件机械校验（可选）
```

使用技能时，项目目录下自动创建：

```
<项目目录>/
├── .sdd-tdd/
│   ├── .dev-flow-state.json          # 流程状态 v2.0
│   ├── explore_report.md             # Explore 产出
│   ├── proposal.md                   # Proposal 产出
│   ├── apply_log.md                  # Apply 日志（含核验块）
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
A: 完整流程的开销（铁律检查 + Grilling + 5 份报告 + 4 个子 agent 审查）对小改动过重。普通流程（先测试后实现 + 全量回归）更敏捷。

**Q: Grilling 会不会把流程拖得很长？**
A: Grilling 的价值是**前置发现问题**。一次 Grilling 追问出的边界条件，可能值回 5-10 倍的后期修复时间。但用户喊停时可以写悬留项，不阻塞流程。

**Q: 4 个 reviewer 子 agent 会不会互相干扰？**
A: 不会。它们是独立子 agent，各自独立上下文，互不可见，天然注意力隔离。

**Q: 对抗验证会不会误杀真实问题？**
A: 会。所以 verifier 被严格要求：必须引用代码证据反驳，不允许仅凭"看起来没问题"。找不到反驳证据必须承认反驳失败。

**Q: 修复轮次为什么限制 2 轮？**
A: 超过 2 轮仍有问题，说明 Proposal 有根本问题。应回退重新设计，而非在错误基础上继续修补。

**Q: Iron Rules 和以前的 Self-Check Triggers 有什么区别？**
A: Self-Check Triggers 是建议性的——"当你发现自己要做 X 时，停下来"。Iron Rules 是强制性的——由 orchestrator 在阶段过渡点主动检查，不通过就不能 advance。最关键的自检触发器已升级为铁律（R0-R5），余下保留为软性提醒。

**Q: Archive 真的有人看吗？**
A: 归档价值是长期积累。类似任务出现时可检索复用决策与经验。长期没人看，短期是组织知识资产。
