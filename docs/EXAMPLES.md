# SDD-TDD 实战案例

本文档展示 SDD-TDD 流程在真实项目中的应用示例。

---

## 案例 1：实现用户配置管理器

### 背景
需要为 Rust 项目实现一个配置管理器，支持：
- 从 TOML/YAML 文件读取配置
- 支持环境变量覆盖
- 类型安全的配置访问

### Phase 1: Explore（探索）

**explore-agent 输入**：
```
实现一个配置管理器，支持 TOML/YAML 文件和环境变量覆盖
```

**explore-agent 产出**：

```markdown
# Explore Report: 配置管理器实现

## 现有代码分析

### 已识别的模式

1. **现有配置使用**
   - `src/main.rs` 中有硬编码的配置值
   - 使用 `std::env::var()` 读取环境变量
   - 没有统一的配置管理

2. **依赖情况**
   - 项目已使用 `serde` (1.0.193)
   - 项目已使用 `toml` (0.8.8)
   - 需要添加 `yaml-rust2` 或 `serde_yaml`

3. **测试现状**
   - 当前测试覆盖率：45%
   - 没有配置相关的测试

## 需求理解

1. **核心需求**
   - 统一的配置访问接口
   - 支持多种配置源（文件、环境变量）
   - 类型安全的配置值

2. **边界情况**
   - 配置文件不存在时的默认值
   - 配置字段缺失时的处理
   - 环境变量覆盖的优先级

## 影响范围

### 新增文件
- `src/config.rs` — 配置管理器实现
- `src/config/` — 配置相关模块
- `tests/config_test.rs` — 测试

### 修改文件
- `src/main.rs` — 使用配置管理器替换硬编码
- `Cargo.toml` — 添加依赖

## 风险点

1. **环境变量命名约定**
   - 建议使用 `APP_` 前缀
   - 嵌套字段使用 `_` 分隔（如 `APP_DATABASE_HOST`）

2. **配置热重载**
   - V1 版本不支持，但可以预留接口

## 关键决策点

1. 配置格式支持：仅 TOML vs TOML + YAML
2. 配置验证时机：加载时 vs 访问时
3. 环境变量覆盖策略：全量覆盖 vs 字段级覆盖
```

### Phase 2: Design（设计）

**proposal-agent 产出**：

```markdown
# 设计提案：配置管理器

## 架构决策

### 决策 1：配置格式
- **选项 A**：仅 TOML（Rust 生态标准）
- **选项 B**：TOML + YAML（更灵活）
- **选择**：A（仅 TOML）
- **理由**：减少依赖，TOML 在 Rust 中更常见

### 决策 2：配置结构
```rust
pub struct Config {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub logging: LoggingConfig,
}
```

### 决策 3：环境变量覆盖
- 使用 `APP_` 前缀
- 嵌套字段用 `_` 分隔
- 示例：`APP_SERVER_PORT=8080` 覆盖 `server.port`

## Spec 清单

### Spec-01：从 TOML 文件加载配置
- **前置条件**：存在有效的 TOML 配置文件
- **输入**：文件路径
- **输出**：`Result<Config, ConfigError>`
- **验收标准**：配置文件的所有字段正确解析
- **测试**：`test_load_from_file()`

### Spec-02：配置文件不存在时使用默认值
- **前置条件**：配置文件路径不存在
- **输入**：不存在的文件路径
- **输出**：`Result<Config, ConfigError>` 使用默认值
- **验收标准**：所有字段都有默认值
- **测试**：`test_default_config()`

### Spec-03：环境变量覆盖配置字段
- **前置条件**：设置了环境变量 `APP_SERVER_PORT=9000`
- **输入**：配置文件 + 环境变量
- **输出**：Config.server.port = 9000
- **验收标准**：环境变量优先于文件配置
- **测试**：`test_env_override()`

### Spec-04：无效配置返回错误
- **前置条件**：配置文件包含无效值
- **输入**：无效文件路径
- **输出**：`Err(ConfigError::InvalidValue)`
- **验收标准**：错误信息包含字段名和期望类型
- **测试**：`test_invalid_config()`

### Spec-05：嵌套配置字段访问
- **前置条件**：Config 已加载
- **输入**：`config.database.host`
- **输出**：返回嵌套字段值
- **验收标准**：类型安全，编译期检查
- **测试**：`test_nested_access()`

## 测试策略

| Spec | 测试类型 | 测试文件 |
|------|---------|---------|
| 01 | 单元测试 | `tests/config_test.rs` |
| 02 | 单元测试 | `tests/config_test.rs` |
| 03 | 单元测试 | `tests/config_test.rs` |
| 04 | 单元测试 | `tests/config_test.rs` |
| 05 | 单元测试 | `tests/config_test.rs` |

## 实现步骤

1. 定义 `Config` 结构和 `ConfigError` 类型
2. 实现 TOML 文件加载（Spec-01, Spec-04）
3. 实现默认值逻辑（Spec-02）
4. 实现环境变量覆盖（Spec-03）
5. 添加配置验证
6. 编写所有测试

## 依赖
- `serde` (已有)
- `toml` (已有)
- `config` (可选，评估后不使用，自己实现更可控)
```

### Phase 3: Apply（实现）

**apply-agent 工作流**：

```
开始 TDD 循环...

Spec-01: 从 TOML 文件加载配置
  Step 1: Write test
    - 创建 tests/config_test.rs
    - 写入 test_load_from_file()
    - 运行测试 → FAIL (Config 类型不存在)
  Step 2: Fail
    - ✓ 测试失败，符合预期
  Step 3: Implement
    - 定义 Config 结构（最小实现）
    - 实现 load_from_file() 函数
    - 运行测试 → PASS
  Step 4: Pass
    - ✓ 测试通过
  Step 5: Refactor
    - 提取 parse_toml() 辅助函数
    - 运行测试 → PASS
  ✓ Spec-01 完成

Spec-02: 配置文件不存在时使用默认值
  Step 1: Write test
    - 写入 test_default_config()
    - 运行测试 → FAIL
  Step 2: Fail ✓
  Step 3: Implement
    - 实现 Default trait for Config
    - 修改 load_from_file() 处理文件不存在
    - 运行测试 → PASS
  Step 4: Pass ✓
  Step 5: Refactor
    - 无需要重构
  ✓ Spec-02 完成

... (Spec-03, 04, 05 类似)

全量测试运行：
  test config_test::test_load_from_file ... ok
  test config_test::test_default_config ... ok
  test config_test::test_env_override ... ok
  test config_test::test_invalid_config ... ok
  test config_test::test_nested_access ... ok

  test result: ok. 5 passed; 0 failed

覆盖率检查：
  python scripts/spec-tracker.py check .sdd-tdd/proposal.md tests
  - Spec-01: ✓ test_load_from_file
  - Spec-02: ✓ test_default_config
  - Spec-03: ✓ test_env_override
  - Spec-04: ✓ test_invalid_config
  - Spec-05: ✓ test_nested_access
  覆盖率：100% (5/5)
```

### Phase 4: Review（审查）

**4 个 reviewer 并行执行**：

#### Correctness Reviewer
```json
{
  "agent": "correctness",
  "findings": [
    {
      "id": "COR-001",
      "severity": "WARN",
      "location": "src/config.rs:145",
      "issue": "环境变量解析未处理空值",
      "evidence": "当环境变量存在但值为空时，parse_env_value() 返回空字符串而非 Error",
      "suggestion": "检查空值并返回 ConfigError::EmptyValue"
    }
  ],
  "verdict": "WARN"
}
```

#### Security Reviewer
```json
{
  "agent": "security",
  "findings": [
    {
      "id": "SEC-001",
      "severity": "INFO",
      "location": "src/config.rs:78",
      "issue": "配置验证信息可能被日志泄露",
      "evidence": "debug_log!() 输出了完整的 Config 结构（包括密码字段）",
      "suggestion": "为敏感字段实现 custom Debug trait，隐藏值"
    }
  ],
  "verdict": "OK"
}
```

#### Performance Reviewer
```json
{
  "agent": "performance",
  "findings": [],
  "verdict": "OK"
}
```

#### Test Reviewer
```json
{
  "agent": "test",
  "findings": [
    {
      "id": "TST-001",
      "severity": "INFO",
      "location": "tests/config_test.rs:67",
      "issue": "测试缺少并发场景",
      "evidence": "多个线程同时读取 Config 实例未测试",
      "suggestion": "添加 test_concurrent_access() 验证线程安全性"
    }
  ],
  "verdict": "OK"
}
```

**对抗验证**：

```
收集到 4 个 findings：
- COR-001 (WARN): 环境变量空值处理
- SEC-001 (INFO): 敏感字段日志
- TST-001 (INFO): 并发测试缺失
- 无 ERR findings

对抗验证流程：
  - 无 ERR findings，跳过对抗验证
  - 3 个 findings 分类为 Should-Fix 或 Info

生成最终报告...
```

**review-writer 产出**：

```markdown
# 审查报告

## 总结
- ERR findings: 0
- WARN findings: 1
- INFO findings: 2
- 总体评价：代码质量良好，无阻塞性问题

## Should-Fix
1. [COR-001] 环境变量空值处理
   - 建议修复以提升鲁棒性

## Info
1. [SEC-001] 敏感字段建议隐藏
2. [TST-001] 可选添加并发测试

## 结论
✓ 可以进入 Phase 5（归档）
```

### Phase 5: Archive（归档）

**archive-agent 产出**：

```markdown
# 任务归档：配置管理器实现

## 元数据
- 完成日期：2026-06-17
- 耗时：45 分钟
- Spec 数量：5
- 测试数量：5

## 问题背景
项目需要统一的配置管理，替代分散的硬编码值和环境变量读取。

## 方案选择
### 决策 1：配置格式
- 选择：TOML
- 理由：Rust 生态标准，减少依赖

### 决策 2：配置结构
- 选择：强类型结构
- 理由：编译期检查，避免运行时错误

### 决策 3：环境变量覆盖
- 选择：字段级覆盖
- 理由：灵活性高，符合 12-Factor App 原则

## 关键决策

### 为什么不用 config crate？
虽然 `config` crate 功能更强大，但：
1. 额外依赖增加编译时间
2. 自定义实现更可控
3. 需求不复杂，不需要 crate 的全部功能

### 为什么选择 Default trait？
使用 Rust 的 Default trait：
1. 符合语言约定
2. 与其他库无缝集成
3. 代码更简洁

## 经验总结

### 成功实践
1. **Spec 先行**：先写 Spec 再写代码，避免了过度设计
2. **TDD 循环**：每个 Spec 的 5 步循环确保了代码质量
3. **环境变量设计**：`APP_` 前缀 + `_` 分隔是清晰的约定

### 改进空间
1. 配置文件变更监听未实现（V1 excluded）
2. 可以考虑添加配置热重载（V2）
3. 测试可以添加 property-based testing

## 产物清单
- `src/config.rs` — 配置管理器实现
- `tests/config_test.rs` — 测试套件
- `.sdd-tdd/explore_report.md` — 探索报告
- `.sdd-tdd/proposal.md` — 设计提案
- `.sdd-tdd/review_report.md` — 审查报告
```

---

## 案例 2：实现缓存层（简略版）

### Phase 1 输出摘要
- 需求：为 API 添加内存缓存，支持 TTL
- 现有：无缓存机制，所有请求直接查询数据库
- 依赖：`dashmap` (并发 HashMap), `tokio` (异步)

### Phase 2 Spec 清单
- Spec-01：缓存命中时返回缓存值
- Spec-02：缓存未命中时查询并存储
- Spec-03：TTL 过期后自动清除
- Spec-04：并发访问安全
- Spec-05：缓存容量上限（LRU 淘汰）

### Phase 4 审查发现
- ERR: 并发测试不充分（test-reviewer）
  - 对抗验证：confirmed（确实需要更多并发测试）
- WARN: 缓存统计信息缺少（performance-reviewer）

### 经验总结
- 并发测试需要专门的工具（如 `loom`）
- 缓存层应该暴露统计接口用于监控

---

## 案例 3：修复权限验证 Bug（简略版）

### Phase 1 输出摘要
- 问题：用户报告偶发的 403 错误，但权限配置正确
- 分析：权限检查逻辑在并发场景下有竞态条件
- 影响：影响约 1% 的请求

### Phase 2 Spec 清单
- Spec-01：并发读写权限表不产生竞态
- Spec-02：权限检查的原子性
- Spec-03：错误日志包含详细上下文

### Phase 4 审查发现
- ERR: 锁的粒度太大，影响性能
  - 对抗验证：refuted（性能影响 <5%，可接受）
- INFO: 建议添加 metrics 监控权限检查耗时

### 经验总结
- 并发 bug 很难在测试中稳定复现
- 使用 `Arc<RwLock<>>` 时注意写锁的范围
- 建议在 Phase 1 就明确性能可接受范围

---

## 使用建议

### 新手常见问题

**问题 1：Phase 1 探索不充分**
- 症状：Phase 2 反复修改设计
- 解决：至少花 10-15 分钟理解现有代码

**问题 2：Spec 写得太模糊**
- 症状：测试写不出来
- 解决：每个 Spec 必须包含具体的输入/输出示例

**问题 3：忽略测试**
- 症状：Phase 3 发现 Spec 不可测试
- 解决：写 Spec 时就思考"这个怎么测试？"

**问题 4：Phase 4 审查走过场**
- 症状：没有发现任何问题
- 解决：每个 reviewer 至少找到 1 个 INFO 级问题

### 何时跳过阶段？

```
完整流程（5 阶段）适用于：
  ✓ 新功能开发
  ✓ 架构重构
  ✓ 性能优化
  ✓ 复杂 bug 修复

可以简化（跳过 Phase 1-2）：
  ✓ 小的 bug 修复（直接 Phase 3-5）
  ✓ 添加测试（直接 Phase 3-5）
  ✓ 文档更新（无需 SDD-TDD）

不建议简化：
  ✗ 涉及公共 API 变更
  ✗ 数据库 schema 变更
  ✗ 安全相关功能
```

### 团队协作建议

**角色分工**：
- **Architect**：完成 Phase 1-2，输出 Spec
- **Developer**：完成 Phase 3，实现 + 测试
- **Reviewer**：完成 Phase 4，审查代码

**交接点**：
- Phase 2 → Phase 3：`proposal.md` 作为交接文档
- Phase 3 → Phase 4：`all tests pass` 作为准入条件
- Phase 4 → Phase 5：`review_report.md` 作为归档依据

**Git 工作流**：
```bash
# Architect
git checkout -b feature/config-manager
# Phase 1-2
git add .sdd-tdd/explore_report.md .sdd-tdd/proposal.md
git commit -m "design: config manager proposal"
# 等待 review...

# Developer
git checkout feature/config-manager
# Phase 3
git add src/config.rs tests/config_test.rs
git commit -m "feat: implement config manager"
# 等待 review...

# Reviewer
git checkout feature/config-manager
# Phase 4
# 提出 findings...

# Developer (修复)
git add src/config.rs
git commit -m "fix: address review findings"

# 任何人
# Phase 5
git add archive/2026-06-17_config-manager.md
git commit -m "archive: config manager task"
git checkout main
git merge feature/config-manager
```

---

## 更多资源

- 📖 [快速开始](QUICKSTART.md) — 5 分钟上手指南
- 🏗️ [系统架构](ARCHITECTURE.md) — 深入理解系统
- 🧠 [方法论](METHODOLOGY.md) — SDD-TDD 核心理念
- ❓ [FAQ](FAQ.md) — 常见问题解答
