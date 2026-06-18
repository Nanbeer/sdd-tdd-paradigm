# CLAUDE.md

本文件为 Claude Code（claude.ai/code）在此仓库中工作时提供指导。

## 交流语言

**所有与用户的交流必须使用中文**，包括回复、提示、错误信息、确认询问等。

## 这是什么仓库

这是一个 **Claude Code 技能仓库**，实现 SDD × TDD 开发范式——将规格驱动设计（Spec-Driven Development）与测试驱动开发（Test-Driven Development）结合的多阶段开发流程。

技能本质上是遵循技能文件格式的 Markdown 文件——不需要构建、测试或运行时。辅助脚本（Python）用于流程状态管理和 spec 追踪。

## 仓库结构

```
skills/                    # 技能定义（源文件，以这里为准）
  sdd-tdd-paradigm/
    SKILL.md               # 主技能文件
    agents/                # 各阶段 Agent 定义
      explore-agent.md     # Phase 1: 探索 Agent
      proposal-agent.md    # Phase 2: 方案 Agent
      apply-agent.md       # Phase 3: TDD 实现 Agent
      correctness-reviewer.md  # Phase 4: 正确性审查 Agent
      security-reviewer.md     # Phase 4: 安全性审查 Agent
      performance-reviewer.md  # Phase 4: 性能审查 Agent
      test-reviewer.md         # Phase 4: 测试完备性审查 Agent
      archive-agent.md     # Phase 5: 归档 Agent
    scripts/               # 辅助脚本
      flow-state.py        # 流程状态管理
      spec-tracker.py      # Spec → Test 映射追踪
openspec/                  # OpenSpec 变更工件
  changes/                 # 活跃变更目录
docs/                      # 文档和设计资料
release/                   # 安装脚本和打包文件
```

**源文件 vs 已部署**：`skills/` 是源文件。部署时会复制到 `~/.claude/skills/`（用户级，跨项目）或项目的 `.claude/skills/`（项目级）。

## 核心架构：5 阶段流程

```
Phase 1: Explore（探索）
  Agent: explore-agent
  产物: explore_report.md
  目的: 理解问题空间，列出影响范围和约束

Phase 2: Proposal（方案）
  Agent: proposal-agent
  产物: proposal.md（含 Spec 清单）
  目的: 设计方案，定义可测试的行为规格

Phase 3: Apply（TDD 实现）
  Agent: apply-agent
  产物: 实现代码 + apply_log.md
  目的: 按 Spec 逐个实现，TDD 循环（Red → Green → Refactor）

Phase 4: Review（多 Agent 交叉验证）
  Agents: correctness-reviewer + security-reviewer +
          performance-reviewer + test-reviewer
  产物: review_report.md + 修复代码
  流程:
    4a. Mini-Explore（识别审查范围）
    4b. 4 Agent 并行审查
    4c. 对抗验证（ERROR 级问题反驳）
    4d. 汇总分级（必改 / 建议修复 / 信息）
    4e. Mini-Apply（TDD 修复，≤ 2 轮）

Phase 5: Archive（归档）
  Agent: archive-agent
  产物: archive/<YYYY-MM-DD>_<任务名>.md
  目的: 沉淀为组织知识，供后续查阅
```

## 路由规则：大小改动分流

大改动（走完整 5 阶段）的判定条件（满足任一即是大改动）：
- 预计影响 > 3 个文件
- 涉及接口签名变更（新增/修改/删除公开 API）
- 涉及数据模型变更（新增/修改表结构、字段）
- 涉及架构变更（新增模块、改变模块间调用关系）
- 涉及第三方系统集成
- 用户明确要求走完整流程

小改动走普通流程：直接开发 + 写测试 + 全量回归。

## 流程状态管理

每个开发任务在项目的 `.sdd-tdd/` 目录下维护一个 `.dev-flow-state.json`：

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
    "findings": { "error": 0, "warn": 0, "info": 0 },
    "must_fix": 0,
    "must_fix_done": 0
  },
  "archive_path": "archive/2026-06-17_task-name.md",
  "started_at": "2026-06-17T10:00:00Z",
  "updated_at": "2026-06-17T10:30:00Z"
}
```

支持中断恢复：如果流程中断，读取状态文件从 `current_phase` 继续。

## Phase 4 Review 的多 Agent 机制

Review 阶段是流水线中计算最密集的部分，采用**多阶段隔离执行**策略（借鉴自 SDR 的经验）：

### 审查 Agent 分类

四类专精 Agent，各自有明确的领域边界：

| Agent | 领域 | 关注点 |
|-------|------|--------|
| Correctness | 逻辑正确性 | 边界条件、并发安全、错误处理、状态一致性 |
| Security | 安全性 | 注入、越权、数据泄露、输入校验、认证绕过 |
| Performance | 性能 | N+1 查询、内存分配、阻塞操作、资源泄漏 |
| Test-Completeness | 测试完备性 | Spec → Test 映射、正面/边界/负面路径覆盖 |

### 对抗验证

对单 Agent 报告的 ERROR 级问题，派一个"辩护 Agent"尝试反驳：
- 多证据确认（≥2 Agent 标记）→ 跳过反驳，直接必改
- 反驳成功 → 降级为 WARN
- 反驳失败 → 确认为真实问题，必改
- 不确定 → 保留，提交人工判断

辩护 Agent 必须引用具体代码作为反驳证据，不允许仅凭"看起来没问题"反驳。

### 修复轮次上限

Mini-Apply ≤ 2 轮。超过 2 轮仍有问题 → 回退到 Phase 2（Proposal），说明初始方案有根本问题。

## 技能文件格式约定

- `SKILL.md`：带有 YAML 前置元数据（`name`、`description`）的 Markdown
- 每个 Agent 模板（`agents/*.md`）：带有 `{project_rules}` 占位符的纯 Markdown
- 脚本（`scripts/*.py`）：Python 3.10+，无额外依赖（仅使用标准库）
- 输出格式文件（`agents/report-format.md`）：定义 JSON 输出结构的模板

## 如何使用此仓库

- **无构建步骤**：技能是 Markdown 文件，由 Claude Code 直接使用
- **部署技能**：将 `skills/sdd-tdd-paradigm/` 复制到 `~/.claude/skills/`（用户级）
- **编辑技能**：编辑 `skills/` 中的源文件，然后重新部署

### 脚本使用说明

```bash
# 初始化流程状态
python3 skills/sdd-tdd-paradigm/scripts/flow-state.py init --task "<任务描述>"

# 读取当前状态
python3 skills/sdd-tdd-paradigm/scripts/flow-state.py status

# 推进到下一阶段
python3 skills/sdd-tdd-paradigm/scripts/flow-state.py advance

# Spec → Test 追踪
python3 skills/sdd-tdd-paradigm/scripts/spec-tracker.py check --proposal ".sdd-tdd/proposal.md"
```

## 开发本技能的约定

- 修改 Agent 定义后，必须同步更新主 SKILL.md 中的相关引用
- 新增 Agent 时，遵循现有的命名和结构约定
- 归档条目存放位置：`<项目目录>/archive/`
- 流程状态存放位置：`<项目目录>/.sdd-tdd/`
