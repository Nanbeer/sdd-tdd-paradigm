# CLAUDE.md

本文件为 Claude Code（claude.ai/code）在此仓库中工作时提供指导。

## 交流语言

**所有与用户的交流必须使用中文**，包括回复、提示、错误信息、确认询问等。

## 这是什么仓库

这是一个 **Claude Code 技能仓库**，实现 SDD × TDD 开发范式——将规格驱动设计（Spec-Driven Development）与测试驱动开发（Test-Driven Development）结合的多阶段开发流程。

技能本质上是遵循技能文件格式的 Markdown 文件——不需要构建、测试或运行时。辅助脚本（Python）用于流程状态管理和 spec 追踪。

## 仓库结构

```
sdd-tdd-paradigm/              # 技能源文件（以这里为准）
  skills/sdd-tdd-paradigm/
    SKILL.md                   # 主技能文件（唯一真相源）
    agents/                    # 各阶段子 agent 的 prompt 定义
      orchestrator.md          # 主 Claude 编排指南
      explore-agent.md         # Phase 1: 探索子 agent
      proposal-agent.md        # Phase 2: 方案子 agent
      apply-agent.md           # Phase 3: TDD 实现子 agent
      correctness-reviewer.md  # Phase 4: 正确性审查子 agent
      security-reviewer.md     # Phase 4: 安全性审查子 agent
      performance-reviewer.md  # Phase 4: 性能审查子 agent
      test-reviewer.md         # Phase 4: 测试完备性审查子 agent
      adversarial-verifier.md  # 对抗验证子 agent
      report-writer.md         # 报告汇总子 agent
      archive-agent.md         # Phase 5: 归档子 agent
      agent_template.md        # 子 agent 通用模板
      report-format.md         # 审查 JSON 输出格式规范
    scripts/                   # 辅助脚本（Python 3 标准库，无外部依赖）
      flow-state.py            # 流程状态管理
      spec-tracker.py          # Spec → Test 映射追踪
      adversarial-review.py    # 对抗验证编排
  docs/                        # 文档和设计资料
  install.sh                   # 安装脚本
```

**源文件 vs 已部署**：`skills/` 是源文件。部署时复制到 `~/.claude/skills/`（用户级，跨项目）或项目的 `.claude/skills/`（项目级）。

## 执行模型

**主 Claude 担任编排者（orchestrator）**，用 `Agent` 工具按阶段派发子 agent。每个 `agents/*.md` 是对应子 agent 的 prompt 主体。详见 `skills/sdd-tdd-paradigm/SKILL.md` 的"执行模型"章节与 `agents/orchestrator.md`。

## 核心架构：5 阶段流程

```
Phase 1: Explore（探索）
  子 agent: explore-agent
  产物: explore_report.md
  目的: 理解问题空间，列出影响范围和约束

Phase 2: Proposal（方案）
  子 agent: proposal-agent
  产物: proposal.md（含 Spec 清单）
  目的: 设计方案，定义可测试的行为规格
  完成标志: proposal.md 存在且含 Spec 清单（本阶段不跑 spec-tracker，测试未写）

Phase 3: Apply（TDD 实现）
  子 agent: apply-agent
  产物: 实现代码 + apply_log.md
  目的: 按 Spec 逐个实现，TDD 循环（Red → Green → Refactor）
  完成标志: 全量测试通过 + spec-tracker.py check 通过

Phase 4: Review（多 Agent 交叉验证）
  子 agent: correctness/security/performance/test-completeness reviewer + adversarial-verifier + report-writer
  产物: review_report.md + 修复代码
  流程:
    4a. Mini-Explore（识别审查范围）
    4b. 4 子 agent 并行审查
    4c. 对抗验证（单 agent ERROR 反驳）
    4d. 汇总分级（必改 / 建议修复 / 信息）
    4e. Mini-Apply（TDD 修复，≤ 2 轮）

Phase 5: Archive（归档）
  子 agent: archive-agent
  产物: archive/<YYYY-MM-DD>_<任务名>.md
  目的: 沉淀为组织知识，供后续查阅
```

## 路由规则：大小改动分流

大改动（走完整 5 阶段）的判定条件（满足任一）：
- 预计影响 > 3 个文件
- 涉及公开接口签名变更（新增/修改/删除对外 API）
- 涉及数据模型变更（表结构、字段、schema）
- 涉及架构变更（新增模块、改变模块间调用关系）
- 涉及第三方系统集成
- 用户明确要求走完整流程

判定依据是变更的语义性质，而非任务描述里的关键词。小改动走普通流程：先写失败测试→最少实现→重构 + 全量回归，不派发子 agent。

## 流程状态管理

每个开发任务在项目的 `.sdd-tdd/` 目录下维护一个 `.dev-flow-state.json`（扁平结构）：

```json
{
  "task": "<任务描述>",
  "route": "full",
  "current_phase": 1,
  "phases_done": [],
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

支持中断恢复：流程中断后，主 Claude 读取状态文件从 `current_phase` 继续。

## Phase 4 Review 的多 Agent 机制

Review 阶段采用**多子 agent 隔离执行**：

### 审查子 agent 分类

四类专精子 agent，各自有明确的领域边界：

| 子 agent | 领域 | 关注点 |
|-------|------|--------|
| Correctness | 逻辑正确性 | 边界条件、并发安全、错误处理、状态一致性 |
| Security | 安全性 | 注入、越权、数据泄露、输入校验、认证绕过 |
| Performance | 性能 | N+1 查询、内存分配、阻塞操作、资源泄漏 |
| Test-Completeness | 测试完备性 | Spec → Test 映射、正面/边界/负面路径覆盖 |

4 个子 agent 由主 Claude 在单条消息里并行派发，各自独立上下文、互不可见，注意力天然隔离。

### 对抗验证

对单子 agent 报告的 ERROR 级问题，派发独立 adversarial-verifier 子 agent 尝试反驳：
- 多证据确认（≥2 个不同子 agent 对同一文件报告 ERROR）→ 跳过反驳，直接必改
- 反驳成功（refuted）→ 降级为 WARN
- 反驳失败（confirmed）→ 确认为真实问题，必改
- 不确定（uncertain）→ 保留，提交人工判断

verifier 必须引用具体代码作为反驳证据，不允许仅凭"看起来没问题"反驳。

### 修复轮次上限

Mini-Apply ≤ 2 轮。超过 2 轮仍有 Must-Fix → 回退到 Phase 2（Proposal），说明初始方案有根本问题。

## 技能文件格式约定

- `SKILL.md`：带有 YAML 前置元数据（`name`、`description`）的 Markdown，是流程参数的唯一真相源
- 每个子 agent 模板（`agents/*.md`）：作为子 agent 的 prompt 主体
- 脚本（`scripts/*.py`）：Python 3 标准库，无额外依赖，跨平台（Windows/PowerShell、Linux、macOS）
- 输出格式文件（`agents/report-format.md`）：定义 JSON 输出结构的模板

## 如何使用此仓库

- **无构建步骤**：技能是 Markdown 文件，由 Claude Code 直接使用
- **部署技能**：将 `skills/sdd-tdd-paradigm/` 复制到 `~/.claude/skills/`（用户级）
- **编辑技能**：编辑 `skills/` 中的源文件，然后重新部署

### 脚本使用说明

```bash
# 初始化流程状态
python skills/sdd-tdd-paradigm/scripts/flow-state.py init --task "<任务描述>"

# 读取当前状态
python skills/sdd-tdd-paradigm/scripts/flow-state.py show

# 推进到下一阶段
python skills/sdd-tdd-paradigm/scripts/flow-state.py advance

# Spec → Test 追踪
python skills/sdd-tdd-paradigm/scripts/spec-tracker.py check .sdd-tdd/proposal.md <tests_dir>

# 对抗验证汇总
python skills/sdd-tdd-paradigm/scripts/adversarial-review.py collect .sdd-tdd/
```

## 开发本技能的约定

- **SKILL.md 是唯一真相源**：流程参数、状态 schema、归档命名、轮次上限以 SKILL.md 为准；其他文件只做引用与说明，不另立参数
- 修改子 agent 定义后，必须同步检查 SKILL.md 与 orchestrator.md 中的相关引用
- 新增子 agent 时，遵循现有的命名和结构约定
- 归档条目存放位置：`<项目目录>/archive/<YYYY-MM-DD>_<任务名>.md`
- 流程状态存放位置：`<项目目录>/.sdd-tdd/`
