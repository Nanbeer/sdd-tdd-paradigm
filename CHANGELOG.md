# Changelog

All notable changes to the SDD-TDD Paradigm skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-06-18

### Changed
- **执行模型落地**：SKILL.md 新增"执行模型"章节，明确主 Claude 用 `Agent` 工具按阶段派发子 agent；各 agent 文件改为子 agent prompt 语义。Phase 4 的 4 个 reviewer 改为并行派发独立子 agent（真正的注意力隔离），对抗验证用独立 verifier 子 agent。
- **脚本 Python 化**：`flow-state.sh`/`spec-tracker.sh`/`adversarial-review.sh` 重写为 `flow-state.py`/`spec-tracker.py`/`adversarial-review.py`（Python 3 标准库，无外部依赖，跨平台 Windows/PowerShell）。修复 Windows GBK 编码问题（强制 UTF-8 stdout）。
- **统一参数（SKILL.md 为唯一真相源）**：Mini-Apply 轮次上限统一为 2 轮（原 orchestrator/ARCHITECTURE 为 3）；归档文件名统一为 `archive/<YYYY-MM-DD>_<任务名>.md`（删除 `TASK_ARCHIVE.md`/`TASK_SPEC.md`/`specs/archive/` 说法）；状态 schema 统一为扁平结构（删除 `phase_details` 嵌套版）。
- **Phase 2 完成标志修正**：去掉"spec-tracker 通过"（测试未写，逻辑死锁），Spec→Test 覆盖校验移到 Phase 3 末尾。
- **description 修正**：改为纯触发条件（"Use when..."），不再剧透 5 阶段流程（符合 CSO 规则）。
- **路由判定**：从中文关键词字面匹配改为语义判定（接口/数据模型/架构/第三方集成变更）；明确"普通流程"= 引用 `test-driven-development` 技能。

### Fixed
- **spec-tracker 正则**：`Spec-[A-Z0-9]{2}`（强制 2 字符，漏 `Spec-1`/`Spec-100`）放宽为 `Spec-(\w+)`。
- **多证据确认**：从按 `file:line` 精确字符串分组（不同 agent 引用同一 bug 时行范围不同会漏）改为按 `file` 分组，同文件 ≥2 个不同 agent 的 ERROR 即多证据确认。
- **adversarial-verifier schema**：删除冗余的 `refuted: true|false|null` 字段，统一为单一 `verdict: refuted|confirmed|uncertain`。
- **flow-state 死代码**：修复 `new_phases_done` 被立即覆盖的问题；advance 上限校验改为 `> 5`。
- **README 2.5 节断裂**：修复"第 37 行有 if (amount"后直接跳进 explore_report 模板的文档断裂。
- **DRY**：删除 4 个 reviewer + agent_template 中重复的"三阶段注意力隔离表"（子 agent 独立运行，隔离自动成立）；TDD 循环/报告结构细节移到对应 agent 文件，SKILL.md 只保留概览。
- **"分形结构"措辞**：校准为"三层相似模式"（非递归调用）。
- 移除不存在的 `writing-specs` 技能引用；移除仓库结构中不存在的 `openspec/`/`release/` 提及。

## [1.0.0] - 2026-06-17

### Added
- **核心 Skill**: `sdd-tdd-paradigm/SKILL.md` — 完整的 5 阶段开发范式定义
- **Phase 1 探索**: `explore-agent.md` — 代码库探索和需求理解
- **Phase 2 设计**: `proposal-agent.md` — 架构设计和 Spec 生成
- **Phase 3 实现**: `apply-agent.md` — TDD 驱动的实现（Write-Fail-Implement-Pass-Refactor）
- **Phase 4 审查**: 4 个专项 reviewer agents
  - `correctness-reviewer.md` — 逻辑正确性
  - `security-reviewer.md` — 安全性审查
  - `performance-reviewer.md` — 性能优化
  - `test-reviewer.md` — 测试完备性
- **对抗验证**: `adversarial-verifier.md` — 反驳验证以降低误报率
- **报告汇总**: `report-writer.md` — 分类汇总审查结果
- **Phase 5 归档**: `archive-agent.md` — 知识沉淀和经验积累
- **流程编排**: `orchestrator.md` — 5 阶段流程管理和状态调度
- **辅助脚本**:
  - `flow-state.sh` — 流程状态管理（init/advance/show）
  - `spec-tracker.sh` — Spec 覆盖率检查
  - `adversarial-review.sh` — 对抗验证编排
- **共享模板**:
  - `agent_template.md` — agent 通用结构模板
  - `report-format.md` — 审查报告 JSON 输出格式规范
- **文档**:
  - `README.md` — 项目介绍和使用说明
  - `CLAUDE.md` — Claude Code 集成指南
  - `QUICKSTART.md` — 5 分钟快速开始
  - `ARCHITECTURE.md` — 系统架构详解
  - `METHODOLOGY.md` — SDD-TDD 方法论
- **基础设施**:
  - `install.sh` — 安装脚本（用户/项目双模式）
  - `LICENSE` — MIT 许可证
  - `VERSION` — 版本号管理
  - `.gitignore` — Git 忽略规则

### Design Decisions
- **分形结构**: 整体流程和每个 Spec 都遵循相同的 "Understand → Design → Execute → Verify" 模式
- **对抗验证**: 通过独立的反驳验证者降低误报率（从 ~40% 降至 <20%）
- **Spec 即测试**: 每个 Spec 必须映射到具体的测试用例，spec-tracker 验证覆盖率
- **强制归档**: Phase 5 不可跳过，确保知识沉淀

### Known Limitations
- 主要针对 Rust 项目优化，其他语言需要调整 reviewer 规则
- 没有 GUI 可视化工具（CLI only）
- Review 阶段 4 个 reviewer 并行需要 subagent 支持
