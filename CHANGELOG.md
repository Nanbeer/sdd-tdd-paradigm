# Changelog

All notable changes to the SDD-TDD Paradigm skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
