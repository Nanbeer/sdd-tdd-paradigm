# CLAUDE.md

本文件为 Claude Code（claude.ai/code）在此仓库中工作时提供指导。

## 交流语言

**所有与用户的交流必须使用中文**，包括回复、提示、错误信息、确认询问等。

## 这是什么仓库

这是一个 **Claude Code 技能仓库**，实现 SDD × TDD 开发范式——将规格驱动设计（Spec-Driven Development）与测试驱动开发（Test-Driven Development）结合的多阶段开发流程。**v2.0** 新增内置 Grilling 协议、铁律体系（R0-R5）、文档同步 Gate、高风险核验协议。

技能本质上是遵循技能文件格式的 Markdown 文件——不需要构建、测试或运行时。辅助脚本（Python）用于流程状态管理和 spec 追踪。

## 仓库结构

```
sdd-tdd-paradigm/              # 技能源文件（以这里为准）
  skills/sdd-tdd-paradigm/
    SKILL.md                   # 主技能文件（唯一真相源）v2.0
    agents/                    # 各阶段子 agent 的 prompt 定义
      orchestrator.md          # 主 Claude 编排指南 v2.0
      explore-agent.md         # Phase 1: 探索子 agent（含事实vs假设）
      proposal-agent.md        # Phase 2: 方案子 agent（含可证伪检查）
      apply-agent.md           # Phase 3: TDD 实现子 agent（含核验块）
      correctness-reviewer.md  # Phase 4: 正确性审查子 agent
      security-reviewer.md     # Phase 4: 安全性审查子 agent
      performance-reviewer.md  # Phase 4: 性能审查子 agent
      test-reviewer.md         # Phase 4: 测试完备性审查子 agent
      adversarial-verifier.md  # 对抗验证子 agent
      report-writer.md         # 报告汇总子 agent
      archive-agent.md         # Phase 5: 归档子 agent（含 Grilling 字段）
      agent_template.md        # 子 agent 通用模板
      report-format.md         # 审查 JSON 输出格式规范
    scripts/                   # 辅助脚本（Python 3 标准库，无外部依赖）
      flow-state.py            # 流程状态管理 v2.0（含 6 个新子命令）
      spec-tracker.py          # Spec → Test 映射追踪
      adversarial-review.py    # 对抗验证编排
      grill-check.py           # Grilling G4 退出条件机械校验（可选）
  docs/                        # 文档和设计资料
  install.sh                   # 安装脚本
```

**源文件 vs 已部署**：`skills/` 是源文件。部署时复制到 `~/.claude/skills/`（用户级，跨项目）或项目的 `.claude/skills/`（项目级）。

## 执行模型

**主 Claude 担任编排者（orchestrator）**，用 `Agent` 工具按阶段派发子 agent。每个 `agents/*.md` 是对应子 agent 的 prompt 主体。详见 `skills/sdd-tdd-paradigm/SKILL.md` 的"执行模型"章节与 `agents/orchestrator.md`。

## 核心架构：5 阶段流程 v2.0

```
Phase 1: Explore（探索）
  子 agent: explore-agent
  产物: explore_report.md（含事实与假设标注）
  目的: 理解问题空间，列出影响范围和约束
  
  ↓ 🔥 Grilling 点 1（拷问理解，G1-G5）

Phase 2: Proposal（方案）
  子 agent: proposal-agent
  产物: proposal.md（含可证伪 Spec 清单）
  目的: 设计方案，定义可测试的行为规格
  
  ↓ 🔥 Grilling 点 2（拷问 Spec）+ Document Sync Gate 2→3

Phase 3: Apply（TDD 实现）
  子 agent: apply-agent
  产物: 实现代码 + apply_log.md（含 Verification Block）
  目的: 按 Spec 逐个实现，TDD 循环（Red → Green → Refactor）
  完成标志: 全量测试通过 + spec-tracker.py check 通过 + 高风险核验

  ↓ Document Sync Gate 3→4

Phase 4: Review（多 Agent 交叉验证）
  子 agent: correctness/security/performance/test-completeness reviewer + adversarial-verifier + report-writer
  产物: review_report.md + 修复代码
  流程:
    4a. Mini-Explore（识别审查范围）
    4b. 4 子 agent 并行审查
    4c. 对抗验证（单 agent ERROR 反驳）
    4d. 汇总分级（必改 / 建议修复 / 信息）
    4e. Mini-Apply（TDD 修复，≤ 2 轮）

  ↓ Document Sync Gate 4→5

Phase 5: Archive（归档）
  子 agent: archive-agent
  产物: archive/<YYYY-MM-DD>_<任务名>.md
  目的: 沉淀为组织知识，含 Grilling 逼出的边界和反例
```

## v2.0 新增能力

### Iron Rules（铁律 R0-R5）
- R0: 技能必调 / R1: 事实先于讨论 / R2: 场景先于代码
- R3: 核验先于信任 / R4: 规范高于代码 / R5: 追问先于放行
- 强制约束，违规阻止 advance

### Grilling Protocol（G1-G5）
- G1: 一次一问 / G2: 禁止模糊词 / G3: 必须给反例 / G4: 退出条件 / G5: 直接语气
- 主 Claude 在两个关键节点直接执行（不派发子 Agent）

### Document Sync Gate
- 3 个过渡点（P2→3 / P3→4 / P4→5）的文档一致性 PASS/FAIL 检查

### 高风险核验
- Apply 完成后，对高风险任务由主 Claude 独立重跑测试、抽查 diff、检查 git status

### 其他
- 偏离检测、中断协议、状态 Self-Check 强制规则

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

每个开发任务在项目的 `.sdd-tdd/` 目录下维护一个 `.dev-flow-state.json`（扁平结构，v2.0 扩展了 grilling/iron_rules/sync_gates/verification/interruption 字段）。支持中断恢复和向后兼容旧 schema。

## 脚本使用说明

```bash
# 初始化流程状态
python skills/sdd-tdd-paradigm/scripts/flow-state.py init --task "<任务描述>"

# 读取当前状态（含 v2.0 新增字段）
python skills/sdd-tdd-paradigm/scripts/flow-state.py show

# 推进到下一阶段
python skills/sdd-tdd-paradigm/scripts/flow-state.py advance

# Spec → Test 追踪
python skills/sdd-tdd-paradigm/scripts/spec-tracker.py check .sdd-tdd/proposal.md <tests_dir>

# 对抗验证汇总
python skills/sdd-tdd-paradigm/scripts/adversarial-review.py collect .sdd-tdd/

# v2.0 新增
python skills/sdd-tdd-paradigm/scripts/flow-state.py grill-complete 1      # 标记 Grilling 完成
python skills/sdd-tdd-paradigm/scripts/flow-state.py iron-check r1 pass ""  # 铁律合规检查
python skills/sdd-tdd-paradigm/scripts/flow-state.py sync-gate gate_2_to_3 pass 0  # 同步 Gate
python skills/sdd-tdd-paradigm/scripts/flow-state.py verify-record <task> pass ""  # 核验记录
python skills/sdd-tdd-paradigm/scripts/flow-state.py interrupt-pause       # 中断暂停
python skills/sdd-tdd-paradigm/scripts/grill-check.py check <grill_log>   # Grilling 校验
```

## 开发本技能的约定

- **SKILL.md 是唯一真相源**：流程参数、状态 schema、归档命名、轮次上限、铁律清单以 SKILL.md 为准；其他文件只做引用与说明，不另立参数
- 修改子 agent 定义后，必须同步检查 SKILL.md 与 orchestrator.md 中的相关引用
- 新增子 agent 时，遵循现有的命名和结构约定
- 归档条目存放位置：`<项目目录>/archive/<YYYY-MM-DD>_<任务名>.md`
- 流程状态存放位置：`<项目目录>/.sdd-tdd/`
- 状态文件 v2.0 schema 向后兼容：`.get()` 读取新字段，绝不断言存在
