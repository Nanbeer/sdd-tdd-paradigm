# 快速开始指南

## 5 分钟上手

### 1. 安装

```bash
# 复制到项目的 .claude/skills/ 目录
cp -r skills/sdd-tdd-paradigm /path/to/your/project/.claude/skills/

# 或复制到全局技能目录
cp -r skills/sdd-tdd-paradigm ~/.claude/skills/
```

### 2. 启动 SDD-TDD 流程

在 Claude Code 中：

```
/sdd-tdd
实现一个用户认证系统，支持 JWT token，需要集成到现有的 PostgreSQL 数据库
```

### 3. 跟随流程

系统会自动进入 Phase 1（Explore），你只需要：

1. **回答确认问题**（是否需要调整探索范围？）
2. **审查输出产物**（explore_report.md 是否准确？）
3. **推进到下一阶段**（流程会自动 advance）

## 典型工作流程

```
用户：/sdd-tdd 实现一个用户认证系统

Claude：
  [Phase 1: Explore]
  正在探索现有代码结构...
  发现 src/database.rs 有用户表
  ...
  
  ✓ explore_report.md 已生成
  发现 3 个相关模块，2 个潜在风险点
  是否继续到 Phase 2？

用户：是

Claude：
  [Phase 2: Design]
  正在设计架构...
  生成 5 个 Spec...
  
  ✓ proposal.md 已生成
  Spec 列表：
    - AA: 生成 JWT token
    - AB: 验证 JWT token
    ...
  
  是否接受设计方案？

用户：是

Claude：
  [Phase 3: Apply]
  正在实现代码...
  
  Spec-AA:
    Write test -> FAIL -> Implement -> PASS
    Refactor -> PASS
  ✓ 完成
  
  ...
  
  ✓ 所有测试通过
  是否继续到 Phase 4？

用户：是

Claude：
  [Phase 4: Review]
  派发 4 个审查 agent...
  
  Correctness: 发现 2 个问题
  Security: 发现 1 个问题
  Performance: 没有发现
  Test-Completeness: 所有 spec 已覆盖
  
  对抗验证中...
  ✓ review_report.md 已生成
  
  Must-Fix: 2 个
  Should-Fix: 1 个
  
  正在修复...
  ✓ Must-Fix 已清零
  
  是否继续到 Phase 5？

用户：是

Claude：
  [Phase 5: Archive]
  ✓ archive/2026-06-17_user-auth.md 已生成
  
  任务完成！
```

## 中断恢复

如果流程中断（例如网络问题、会话超时），重新开始：

```
/sdd-tdd
```

系统会检测到未完成的任务，并询问：

```
发现未完成的 SDD-TDD 任务：实现用户认证系统
当前阶段：Phase 3（Apply）
已完成阶段：1, 2

是否继续？（否则将重置）
```

选择"继续"会从 Phase 3 恢复，之前的产物会被保留。

## 查看进度

随时检查当前状态：

```bash
python ./skills/sdd-tdd-paradigm/scripts/flow-state.py show
```

输出示例：
```
task: 实现用户认证系统
current_phase: 4
phases_done: 1, 2, 3
last_updated: 2026-06-17T14:32:00Z
```

## 常用命令

```bash
# 查看状态
python ./skills/sdd-tdd-paradigm/scripts/flow-state.py show

# 手动推进（不推荐，除非你理解后果）
python ./skills/sdd-tdd-paradigm/scripts/flow-state.py advance

# 检查 spec 覆盖率
python ./skills/sdd-tdd-paradigm/scripts/spec-tracker.py check .sdd-tdd/proposal.md tests

# 汇总审查结果
python ./skills/sdd-tdd-paradigm/scripts/adversarial-review.py collect .sdd-tdd/

# 手动记录反驳结果（正常流程中不需要）
python ./skills/sdd-tdd-paradigm/scripts/adversarial-review.py record-refutation \
  COR-001 refuted "理由..."
```

## 第一个任务的建议

**从简单的任务开始：**

✅ **好的第一个任务**：
- "实现一个配置管理器，支持读取 YAML 文件"
- "添加一个日志工具函数，支持不同级别"
- "创建一个简单的缓存层"

❌ **避免的第一个任务**：
- 大规模重构
- 复杂的多线程系统
- 涉及多个未知外部依赖

**建议：**
1. 先用简单任务熟悉流程
2. 理解每个阶段的产物格式
3. 学会阅读各种 .md 报告
4. 再尝试复杂任务

## 团队协作

### 分工模式

**模式 A：单人完整流程**
```
开发者：/sdd-tdd 任务A
       → 完成所有阶段
       → 归档
```

**模式 B：分工协作**
```
架构师：完成 Phase 1-2（Explore + Design）
       → 审查 proposal.md
       
开发者：从 Phase 3 开始（Apply）
       → 实现代码
       → 归档
```

**模式 C：审查分离**
```
开发者：完成 Phase 1-3
       → 代码实现完毕
       
审查者：完成 Phase 4（Review）
       → 独立审查
       → 提出 Must-Fix
       
开发者：修复 Must-Fix
       → 进入 Phase 5
```

### Git 工作流

推荐的 Git 分支策略：

```bash
# 每个 SDD-TDD 任务一个分支
git checkout -b sdd-tdd/user-auth

# Phase 1-2 的产物可以 commit（作为设计文档）
git add .sdd-tdd/explore_report.md
git add .sdd-tdd/proposal.md
git commit -m "design: user auth system"

# Phase 3 的实现
git add src/auth.rs tests/auth_test.rs
git commit -m "feat: implement user auth"

# Phase 4 的审查报告（可选 commit）
git add .sdd-tdd/review_report.md
git commit -m "review: user auth"

# Phase 5 的归档
git add archive/2026-06-17_user-auth.md
git commit -m "archive: user auth"

# 合并到主分支
git checkout main
git merge sdd-tdd/user-auth
```

## 故障排查

### 问题：流程卡在某个阶段

**症状**：`python scripts/flow-state.py show` 显示 `current_phase: X` 但实际产物不存在

**原因**：阶段执行失败但状态未更新

**解决**：
```bash
# 1. 强制推进
python ./skills/sdd-tdd-paradigm/scripts/flow-state.py advance

# 2. 重新运行该阶段
# （通过 /sdd-tdd 重新进入流程）
```

### 问题：审查 agent 超时

**症状**：Phase 4 卡住，某个 reviewer 无响应

**原因**：代码库太大，审查耗时超过 5 分钟

**解决**：
1. 减小审查范围（只审查核心文件）
2. 单独手动调用 reviewer agent
3. 标记该 reviewer 为 failed，继续流程

### 问题：测试一直失败

**症状**：Phase 3 或 Phase 4 中测试持续失败

**原因**：
- Spec 定义不准确
- 测试写错了
- 实现有 bug

**解决**：
1. 重新读取 `proposal.md`，确认 spec 定义
2. 检查测试代码是否真的验证了 spec 行为
3. 如果修复 2 轮仍失败 → 回退到 Phase 2（Design）

### 问题：对抗验证全部 refuted

**症状**：所有 ERR findings 都被标记为 refuted，没有 Must-Fix

**原因**：
- reviewer 质量太差
- adversarial verifier 过于宽松

**解决**：
1. 检查 reviewer 的输出质量
2. 检查 adversarial verifier 的理由是否合理
3. 必要时手动审查代码

## 下一步

- 阅读 [METHODOLOGY.md](./METHODOLOGY.md) 深入理解方法论
- 查看 [ARCHITECTURE.md](./ARCHITECTURE.md) 了解系统架构
- 浏览 [EXAMPLES.md](./EXAMPLES.md) 学习实战案例
- 阅读 [FAQ.md](./FAQ.md) 解答常见疑问
