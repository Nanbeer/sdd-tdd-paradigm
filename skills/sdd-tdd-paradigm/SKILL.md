---
name: sdd-tdd-paradigm
description: SDD × TDD 开发范式。将规格驱动设计与测试驱动开发结合，大改动走 5 阶段流程（探索→方案→TDD实现→多Agent审查→归档），小改动走普通流程。
version: 1.0.0
category: development-workflow
tags:
  - sdd
  - tdd
  - multi-agent
  - code-review
  - spec-driven
---

# SDD × TDD 开发范式

## 技能概述

本技能实现一套分形结构的多阶段开发流程，根据变更规模自适应选择开发路径：

- **大改动**（>3 文件或涉及接口/架构变更）→ 完整 5 阶段流程
- **小改动**（≤3 文件且无接口/架构变更）→ 普通流程

完整流程确保大改动的质量和可追溯性，普通流程保持小改动的敏捷性。

## 核心原则

### 1. 决策前置（Decision First）

在写代码之前先做决策。Explore 阶段理解问题，Proposal 阶段设计方案，确保"测的是对的东西"。

### 2. 规格落地为测试（Spec Becomes Test）

Proposal 中的每个 Spec 必须是可测试的行为描述，Apply 阶段按 Spec 逐个实现并编写对应测试。规格不是文档，是有测试证明的行为契约。

### 3. 多视角交叉验证（Multi-Perspective Verification）

Review 阶段用 4 个专精 Agent 从不同维度审查代码，每个 Agent 的注意力不被其他维度稀释。通过对抗验证过滤误报。

### 4. 知识沉淀（Knowledge Archive）

每个大改动强制输出结构化的归档条目，记录问题定义、方案选择、关键决策和学到的经验，形成可检索的组织知识库。

## 执行流程

### 0. 路由判定（Routing）

收到开发任务时，立即判断变更规模：

```python
def is_large_change(task_description, affected_files_estimate):
    """判断是否为大改动"""
    return (
        affected_files_estimate > 3 or
        "接口" in task_description or
        "API" in task_description or
        "架构" in task_description or
        "数据库" in task_description or
        "集成" in task_description
    )
```

**大改动** → 进入 Phase 1（Explore）
**小改动** → 提示用户使用普通流程（直接开发 + 测试）

### 1. Phase 1: Explore（探索）

**Agent**: `agents/explore-agent.md`

**输入**: 用户需求描述

**活动**:
- 读取现有代码（相关模块、接口定义、测试文件）
- 分析代码中的 TODO、FIXME、XXX 注释
- 识别影响范围（哪些文件会被修改）
- 列出约束条件（性能、兼容性、安全）
- 识别风险点

**输出**: `.sdd-tdd/explore_report.md`

**报告结构**:
```markdown
# Explore Report: <任务名称>

## 任务描述
<用户原始需求>

## 现有代码分析
- 相关模块：<列表>
- 现有接口：<列表>
- 测试覆盖：<覆盖率或"无测试"">

## TODO/FIXME 发现
- `<文件>:<行号>`: <注释内容>

## 影响范围
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| src/auth.rs | 修改 | 扩展 JWT 生成逻辑 |
| src/api/login.rs | 新增 | 新增登录接口 |

## 约束条件
- 性能：<具体指标>
- 兼容性：<向后兼容要求>
- 安全：<安全要求>

## 风险点
1. <风险 1>
2. <风险 2>

## 关键决策点
- <需要在 Proposal 阶段做出的决策 1>
- <需要在 Proposal 阶段做出的决策 2>
```

**阶段完成标志**: 产出 `explore_report.md`

### 2. Phase 2: Proposal（方案）

**Agent**: `agents/proposal-agent.md`

**输入**: `.sdd-tdd/explore_report.md`

**活动**:
- 基于探索报告设计技术方案
- 定义 Spec 清单（每个 Spec 是可测试的行为描述）
- 明确技术决策及权衡
- 规划测试策略

**输出**: `.sdd-tdd/proposal.md`

**Spec 格式要求**:
每个 Spec 必须包含：
1. **前置条件**（Before）：系统处于什么状态
2. **操作**（Action）：执行什么操作
3. **预期结果**（After）：系统应该变成什么状态
4. **对应测试**: 测试用例名称（`test_<spec_name>`）

**Spec 覆盖要求**:
每个功能特性必须覆盖三类路径：
- **正面路径**（Happy Path）：至少 1 个 Spec
- **边界路径**（Edge Case）：至少 1 个 Spec
- **负面路径**（Negative Path）：至少 1 个 Spec

**报告结构**:
```markdown
# Proposal: <任务名称>

## 技术决策

### Decision 1: <决策标题>
- **选项 A**: <描述>
  - Pros: <优点列表>
  - Cons: <缺点列表>
- **选项 B**: <描述>
  - Pros: <优点列表>
  - Cons: <缺点列表>
- **选择**: 选项 X
- **理由**: <为什么选 X>
- **已知权衡**: <取舍点>

## Spec 清单

### Spec-01: <Spec 名称>
- **前置条件**: <系统状态>
- **操作**: <执行的动作>
- **预期结果**: <系统应达到的状态>
- **对应测试**: `test_<spec_name>`
- **路径类型**: Happy Path / Edge Case / Negative Path

### Spec-02: <Spec 名称>
...

## 测试策略
- 单元测试：<测试什么>
- 集成测试：<测试什么>
- E2E 测试：<测试什么>

## 关键实现点
1. <实现要点 1>
2. <实现要点 2>
```

**阶段完成标志**: 产出 `proposal.md`，包含完整的 Spec 清单

### 3. Phase 3: Apply（TDD 实现）

**Agent**: `agents/apply-agent.md`

**输入**: `.sdd-tdd/proposal.md`

**活动**: 对每个 Spec 执行 TDD 循环

**TDD 循环**:
```
对于 proposal.md 中的每个 Spec:
  1. Read（写失败的测试）
     - 根据 Spec 写测试用例
     - 运行测试 → 必须 FAIL
     - 如果测试直接通过 → 检查是否重复实现或测试写错
  
  2. Green（写最少代码让测试通过）
     - 只写让测试通过的最少代码
     - 运行测试 → 必须 PASS
     - 运行全量测试 → 必须全部 PASS
  
  3. Refactor（测试保护下重构）
     - 删除重复代码
     - 改善命名和结构
     - 运行全量测试 → 必须全部 PASS
```

**输出**:
- 实现代码（按 Spec 逐个实现）
- 测试代码（每个 Spec 对应至少一个测试）
- `.sdd-tdd/apply_log.md`（实现日志）

**日志结构**:
```markdown
# Apply Log: <任务名称>

## 实现进度

### Spec-01: <Spec 名称>
- **状态**: ✅ 完成 / 🚧 进行中
- **测试**: `test_<spec_name>`
- **实现文件**: `<文件路径>`
- **测试文件**: `<测试文件路径>`
- **备注**: <实现过程中的发现或问题>

### Spec-02: <Spec 名称>
...

## 全量测试结果
- 测试总数：<N>
- 通过：<N>
- 失败：<N>
- 覆盖的行数：<N>

## 关键发现
- <在实现过程中发现的设计问题或需求澄清>
```

**阶段完成标志**:
- 所有 Spec 都有对应的测试
- 全量测试 100% 通过
- 产出 `apply_log.md`

### 4. Phase 4: Review（多 Agent 交叉验证）

**Agents**: 
- `agents/correctness-reviewer.md`
- `agents/security-reviewer.md`
- `agents/performance-reviewer.md`
- `agents/test-reviewer.md`

**输入**: 
- `.sdd-tdd/proposal.md`
- `.sdd-tdd/apply_log.md`
- 实现代码和测试代码

#### 4a. Mini-Explore（识别审查范围）

主 Agent 分析变更范围，生成审查清单：
- 列出所有新增/修改的文件
- 识别高风险代码段（复杂逻辑、并发、外部调用）
- 确定审查重点

#### 4b. 4 Agent 并行审查

4 个审查 Agent 独立运行，互不通信，各自审查代码并产出 findings。

**每个 Agent 的输出格式**:
```json
{
  "agent": "<Agent 名称>",
  "findings": [
    {
      "id": "<Agent 前缀>-001",
      "severity": "ERROR | WARN | INFO",
      "file": "<文件路径>",
      "line": "<行号或行范围>",
      "issue": "<一句话描述问题>",
      "evidence": "<具体证据：代码片段、行号引用>",
      "suggestion": "<修复建议>"
    }
  ],
  "summary": "<整体评价，一句话>",
  "verdict": "PASS | CONDITIONAL_PASS | FAIL"
}
```

**Agent 职责边界**:

| Agent | 领域 | 关注点 |
|-------|------|--------|
| Correctness | 逻辑正确性 | 边界条件、并发安全、错误处理、状态一致性 |
| Security | 安全性 | 注入、越权、数据泄露、输入校验、认证绕过 |
| Performance | 性能 | N+1 查询、内存分配、阻塞操作、资源泄漏 |
| Test-Completeness | 测试完备性 | Spec → Test 映射、正面/边界/负面路径覆盖 |

**每个 Agent 不关注其他 Agent 的领域**。这样可以避免注意力稀释。

#### 4c. 对抗验证（Adversarial Validation）

汇总所有 findings，对 ERROR 级问题启动对抗验证：

```
对于每个 severity=ERROR 的 finding:
  case 被 ≥2 Agent 标记:
    → 确认为真实问题，跳过反驳，标记为"必改"
  
  case 仅被 1 Agent 标记:
    → 指派辩护 Agent（与发现 Agent 不同类）
    → 辩护 Agent 读取相关文件 + 测试
    → 尝试反驳，输出:
      {
        "refuted": true/false,
        "reason": "<理由>"
      }
    
    if 反驳成功:
      → 降级为 WARN，记录反驳理由
    else if 反驳失败:
      → 确认为真实问题，标记为"必改"
    else:  // 不确定
      → 保留 ERROR，标记"需人工判断"
```

**辩护 Agent 的行为约束**:
- 必须引用具体代码作为反驳证据
- 不允许仅凭"看起来没问题"反驳
- 如果找不到反驳证据，必须承认反驳失败

#### 4d. 汇总分级

```
汇总规则:

必改（Must Fix）
├─ 多证据确认（≥2 Agent 标记同一问题）
└─ 反驳失败的单 Agent ERROR

建议修复（Should Fix）
├─ 被反驳降级的 ERROR
└─ 所有 WARN

仅信息（Info）
└─ 所有 INFO
```

**输出**: `.sdd-tdd/review_report.md`

**报告结构**:
```markdown
# Review Report: <任务名称>

## 审查概览
| Agent | ERROR | WARN | INFO | Verdict |
|-------|-------|------|------|---------|
| Correctness | N | N | N | PASS/WARN/FAIL |
| Security | N | N | N | PASS/WARN/FAIL |
| Performance | N | N | N | PASS/WARN/FAIL |
| Test-Completeness | N | N | N | PASS/WARN/FAIL |

## 对抗验证结果
| Finding ID | 发现 Agent | 辩护 Agent | 结果 | 最终级别 |
|------------|-----------|-----------|------|---------|
| COR-001 | Correctness | Security | 反驳失败 | ERROR（必改） |
| SEC-002 | Security | Correctness | 反驳成功 | WARN（建议修复） |

## 必改（Must Fix）
### COR-001: <问题标题>
- **文件**: <路径>
- **行号**: <行号>
- **问题**: <描述>
- **证据**: <代码片段>
- **建议**: <修复建议>
- **状态**: ⬜ 待修复 / ✅ 已修复

### SEC-003: <问题标题>
...

## 建议修复（Should Fix）
### PER-001: <问题标题>
...

## 仅信息（Info）
### TST-002: <观察记录>
...

## 修复日志
| Finding ID | 修复轮次 | 状态 |
|------------|---------|------|
| COR-001 | Round 1 | ✅ 已修复 |
| SEC-003 | Round 1 | ⬜ 待修复 |
```

**阶段完成标志**: 产出 `review_report.md`，包含所有 findings 和对抗验证结果

#### 4e. Mini-Apply（TDD 修复）

对 Review 报告中的"必改"问题逐个修复：

```
For each must_fix finding:
  1. 先补测试（暴露问题）
     - 写一个能复现此问题的测试
     - 运行测试 → 必须 FAIL
  
  2. 改代码（修复问题）
     - 修复问题
     - 运行测试 → 必须 PASS
  
  3. 全量回归
     - 运行全量测试 → 必须 100% 通过

记录修复轮次:
  Round 1: 修复 N 个问题
  Round 2: 修复 M 个问题（如果有新引入的问题）

if 修复轮次 > 2:
  STOP! 回退到 Phase 2（Proposal），说明初始方案有根本问题
```

**修复轮次上限**: 2 轮。超过 2 轮仍有问题 → 回退到 Proposal 阶段。

### 5. Phase 5: Archive（归档）

**Agent**: `agents/archive-agent.md`

**输入**: 
- `.sdd-tdd/explore_report.md`
- `.sdd-tdd/proposal.md`
- `.sdd-tdd/apply_log.md`
- `.sdd-tdd/review_report.md`

**活动**:
- 汇总所有阶段的产出
- 提取关键决策和学到的经验
- 生成结构化的归档条目

**输出**: `archive/<YYYY-MM-DD>_<任务名-kebab-case>.md`

**归档条目结构**:
```markdown
# Task: <任务名称>

## Meta
- 日期: YYYY-MM-DD
- 作者: <作者>
- 影响文件数: N
- Spec 数量: N
- 测试覆盖: N 个测试用例
- Review 发现: N ERROR（已修复）+ N WARN（已修复）+ N INFO

## 问题定义
<一段话描述要解决的问题>

## 方案选择
### 方案 A: <名称>
- 描述: <描述>
- 优点: <列表>
- 缺点: <列表>

### 方案 B: <名称>
- 描述: <描述>
- 优点: <列表>
- 缺点: <列表>

### 采纳方案
- 选择: 方案 X
- 理由: <为什么选这个方案>

## 关键决策

### 决策 1: <决策标题>
- 场景: <在什么情况下需要做这个决策>
- 选项: <可选项列表>
- 选择: <选了什么>
- 理由: <为什么这么选>

### 决策 2: <决策标题>
...

## 关键发现
1. <在开发过程中发现的重要事实>
2. <在 Review 阶段发现的重要问题>

## 经验教训
1. <学到了什么>
2. <哪些假设被验证/推翻了>
```

**阶段完成标志**: 产出归档条目

## 流程状态管理

每个开发任务在项目根目录下创建 `.sdd-tdd/.dev-flow-state.json`：

```json
{
  "task": "<任务描述>",
  "route": "full | normal",
  "current_phase": 1,
  "phases_done": [],
  "explore_path": ".sdd-tdd/explore_report.md",
  "proposal_path": ".sdd-tdd/proposal.md",
  "specs_total": 8,
  "specs_done": 0,
  "review": {
    "round": 1,
    "findings": {
      "error": 0,
      "warn": 0,
      "info": 0
    },
    "must_fix": 0,
    "must_fix_done": 0
  },
  "archive_path": "archive/2026-06-17_task-name.md",
  "started_at": "2026-06-17T10:00:00Z",
  "updated_at": "2026-06-17T10:30:00Z"
}
```

**中断恢复**:
- 如果流程中断，读取状态文件
- 根据 `current_phase` 字段继续执行
- 不重新开始已完成的阶段

## 自检触发器

### Explore 阶段
- "我已经理解问题了" → 检查：是否读过代码？是否识别了影响范围？
- "影响范围很小" → 检查：是否只看了直接相关的文件？是否考虑了间接依赖？

### Proposal 阶段
- "方案已经很完善了" → 检查：是否有 Spec 清单？每个 Spec 是否可测试？
- "这个 Spec 太简单了不用写" → 检查：这个 Spec 对应的测试是否已经在写了？

### Apply 阶段
- "测试已经通过了不用写了" → 检查：测试是在实现之前写的吗？
- "这个 Spec 太简单了不用测试" → 检查：这个 Spec 的边界条件和负面路径有测试吗？
- "重构会破坏测试" → 检查：重构是否改变了外部行为？如果是，说明 Spec 定义有问题

### Review 阶段
- "看起来没问题不用仔细查" → 检查：4 个 Agent 是否都执行了？对抗验证是否完整？
- "ERROR 太多了处理不过来" → 检查：对抗验证是否有效过滤了误报？

### Archive 阶段
- "这个决策太明显了不用记录" → 检查：决策的理由是否清晰？已知权衡是否记录？
- "归档条目太长了" → 检查：只记录关键决策和学习，省略显而易见的步骤

## 使用方式

### 启动新任务

```bash
# 用户提出开发任务
用户: "帮我实现用户认证系统"

# 技能自动判断变更规模并启动流程
技能: "检测到这是大改动（涉及接口变更），启动 5 阶段流程。Phase 1: Explore..."
```

### 中断恢复

```bash
# 流程中断后继续
用户: "继续上次的认证系统开发"

# 技能读取状态文件并从当前阶段继续
技能: "检测到中断在 Phase 3（Apply），已完成 5/8 个 Spec，继续..."
```

### 查看进度

```bash
# 查看当前流程状态
用户: "当前进度"

# 技能输出状态摘要
技能: "Phase 3: Apply (5/8 Specs), 全量测试: 12/12 通过"
```

### 切换到普通流程

```bash
# 用户判断为小改动
用户: "这只是个小改动，不用走完整流程"

# 技能切换到普通流程
技能: "好的，使用普通流程：直接开发 + 写测试 + 全量回归"
```

## 与其他技能的关系

- **test-driven-development**: Phase 3 (Apply) 使用 TDD 技能的方法
- **code-review**: Phase 4 (Review) 的 4 个 Agent 借鉴了 code-review 的多视角审查模式
- **brainstorming**: Phase 1 (Explore) 可以使用 brainstorming 技能的方法识别风险点
- **writing-specs**: Phase 2 (Proposal) 的 Spec 撰写遵循 writing-specs 技能的规范

## 项目结构

部署后的目录结构：

```
~/.claude/skills/sdd-tdd-paradigm/
├── SKILL.md                          # 主技能文件（本文件）
├── agents/
│   ├── explore-agent.md              # Phase 1: 探索 Agent
│   ├── proposal-agent.md             # Phase 2: 方案 Agent
│   ├── apply-agent.md                # Phase 3: TDD 实现 Agent
│   ├── correctness-reviewer.md       # Phase 4: 正确性 Agent
│   ├── security-reviewer.md          # Phase 4: 安全性 Agent
│   ├── performance-reviewer.md       # Phase 4: 性能 Agent
│   ├── test-reviewer.md              # Phase 4: 测试 Agent
│   └── archive-agent.md              # Phase 5: 归档 Agent
└── scripts/
    ├── flow-state.py                 # 流程状态管理
    └── spec-tracker.py               # Spec → Test 追踪
```

使用技能时，项目目录下会自动创建：

```
<项目目录>/
├── .sdd-tdd/
│   ├── .dev-flow-state.json          # 流程状态
│   ├── explore_report.md             # Explore 产出
│   ├── proposal.md                   # Proposal 产出
│   ├── apply_log.md                  # Apply 日志
│   └── review_report.md              # Review 报告
└── archive/
    └── 2026-06-17_task-name.md       # 归档条目
```

## 适用场景

### 推荐使用完整流程的场景

- 新功能开发（用户认证、支付网关）
- 架构重构（数据库迁移、API 升级）
- 性能优化（需要重新设计数据流或缓存策略）
- 复杂 bug 修复（涉及多模块、多层抽象）

### 推荐使用普通流程的场景

- 单文件的小修改（改配置、改文案）
- 明确的 bug 修复（已知根因，修复清晰）
- 测试补充（为已有功能补测试）
- 文档更新

## 常见问题

**Q: 为什么小改动不走完整流程？**
A: 完整流程的开销（5 份报告 + 4 个 Agent 审查）对小改动来说过重。普通流程（直接开发 + 测试）更敏捷。

**Q: Review 的 4 个 Agent 会不会互相干扰？**
A: 不会。4 个 Agent 独立运行，互不通信，各自关注自己的领域。这样可以避免注意力稀释。

**Q: 对抗验证会不会误杀真实问题？**
A: 会。所以辩护 Agent 被严格要求：必须引用代码证据反驳，不允许仅凭"看起来没问题"反驳。如果找不到反驳证据，必须承认反驳失败。

**Q: 修复轮次为什么限制 2 轮？**
A: 超过 2 轮仍有问题，说明初始方案（Proposal）有根本问题。应该回退到 Proposal 阶段重新设计，而不是在错误的基础上继续修补。

**Q: Archive 阶段真的有人看吗？**
A: 归档条目的价值是长期积累。当类似任务出现时，可以检索归档条目，复用之前的决策和经验。即使短期没人看，长期看是组织知识资产。

**Q: 状态文件可以手动编辑吗？**
A: 可以。如果流程状态出错，可以手动编辑 `.dev-flow-state.json` 恢复。修改 `current_phase` 字段可以跳转到任意阶段。
