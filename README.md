# SDD-TDD Paradigm — 规格驱动 × 测试驱动开发范式

SDD-TDD Paradigm（规格驱动 × 测试驱动开发范式）是一个多阶段开发技能。它根据变更规模自适应选择开发路径，大改动走完整的 5 阶段流程（Explore → Proposal → Apply(TDD) → Review(多Agent交叉验证) → Archive），小改动走普通流程。通过决策前置、实现验证、多Agent审查的三重保障，确保大改动的质量和可追溯性。

## 1. 快速入门

### 1.1 安装

一行命令安装技能：

**Linux / Mac：**
```bash
curl -sL -H "PRIVATE-TOKEN: <your-token>" "https://your-gitlab/skills/sdd-tdd-paradigm/raw?ref=master" | bash
```

**Windows（PowerShell）：**
```powershell
Invoke-RestMethod -Uri "https://your-gitlab/skills/sdd-tdd-paradigm/raw?ref=master" -Headers @{"PRIVATE-TOKEN"="<your-token>"} | Invoke-Expression
```

安装脚本会将技能复制到 `~/.claude/skills/sdd-tdd-paradigm/`（用户级，跨项目）或当前项目的 `.claude/skills/sdd-tdd-paradigm/`（项目级）。

### 1.2 启动开发流程

直接告诉 Claude 你要做什么，技能会根据变更规模自动选择路径：

```
/sdd-tdd
帮我实现用户认证系统，包括登录、登出、JWT token 管理
```

技能会先分析这个任务的影响范围，然后告诉你：

```
这是一个大改动（预计影响 > 3 个文件，涉及接口变更）
将启动完整的 5 阶段流程：
1. Explore（探索）- 理解问题空间
2. Proposal（方案）- 设计方案，列 Spec 清单
3. Apply（实现）- TDD 驱动，先测试后实现
4. Review（审查）- 4 Agent 交叉验证 + 对抗验证
5. Archive（归档）- 沉淀为组织知识

继续吗？/ 切换到普通流程？
```

### 1.3 流程概览

```
触发开发任务
  │
  ├─ 小改动（≤3 文件，无接口变更）→ 普通流程直接开发
  │
  └─ 大改动（>3 文件或有接口变更）→ 完整 5 阶段流程
                                      │
                                      ├─ Phase 1: Explore（单 Agent）
                                      │   输出：影响分析、风险点清单、关键约束
                                      │   产物：explore_report.md
                                      │
                                      ├─ Phase 2: Proposal（单 Agent）
                                      │   输出：技术方案、Spec 清单（每个 Spec 可独立测试）
                                      │   产物：proposal.md
                                      │
                                      ├─ Phase 3: Apply（单 Agent，TDD 循环）
                                      │   按 Spec 逐个实现：Red → Green → Refactor
                                      │   产物：实现代码 + 全量测试通过
                                      │
                                      ├─ Phase 4: Review（多 Agent 交叉验证）
                                      │   4 个审查 Agent + 对抗验证
                                      │   产物：review_report.md + 修复代码
                                      │
                                      └─ Phase 5: Archive（单 Agent）
                                          沉淀为组织知识
                                          产物：<项目>/archive/<YYYY-MM-DD>_<任务名>.md
```

## 2. 思路历程

### 2.1 从"写完再测"到"测了再写"

TDD（测试驱动开发）的核心价值不是"测试"，而是"规格"——先写测试就是先定义行为规格，再写代码就是实现规格。但在实践中，TDD 有三大痛点：

1. **测的是错的东西**：如果需求理解有误，测试写得再好也是错的测试
2. **缺乏架构思考**：TDD 鼓励"先让测试通过"，但可能导致糟糕的架构决策
3. **大改动难以驾驭**：一个涉及 10 个文件的大特性，按 TDD 逐个写测试会让人迷失方向

### 2.2 SDD 的介入：在 TDD 之前加一层规格

SDD（Spec-Driven Development）强调在写代码之前先写规格文档——定义接口、数据结构、行为约束。这解决了 TDD 的第 1 个问题：如果规格是错的，那是在写代码之前就发现了。

但 SDD 也有自己的问题：**规格写了没人看**。一份 50 页的规格文档，开发者往往扫一眼就开始写代码，规格变成了"写给人看的文档"而非"驱动开发的规格"。

### 2.3 SDD × TDD 的结合：规格落地为测试

SDD-TDD Paradigm 的核心思想是：**用 SDD 定义规格，用 TDD 验证规格**。

具体来说：
- **Proposal 阶段**产出的每个 Spec 必须是"可测试的行为描述"——不是"系统应该很快"，而是"在 1000 条记录下查询应在 100ms 内返回"
- **Apply 阶段**按 Spec 逐个实现，每个 Spec 对应至少一个测试用例
- **Review 阶段**的 Test-Completeness Agent 会检查：Proposal 里的 Spec 是否都有对应测试？

这样，规格不再是"写给人看的文档"，而是"有测试证明的、可追溯的行为契约"。

### 2.4 Review 的多 Agent 交叉验证

传统的代码审查是"找一个人看看"。这种方法有三个问题：

1. **单一视角盲区**：一个审查者关注逻辑正确性，就可能忽略安全问题
2. **认知负荷过载**：一个审查者同时关注正确性、安全性、性能、可维护性，容易漏掉不显眼的维度
3. **标准不一致**：不同审查者的标准不同，审查质量不稳定

SDD-TDD 的 Review 阶段用 4 个专精的 Agent 解决这些问题：

- **Correctness Agent**：只看逻辑正确性、边界处理、并发安全
- **Security Agent**：只看注入、越权、数据泄露、输入校验
- **Performance Agent**：只看 N+1 查询、内存分配、资源泄漏
- **Test-Completeness Agent**：只看测试覆盖度（Spec → Test 映射）

4 个 Agent 独立运行，互不通信，确保每个维度的注意力不被其他维度稀释。

### 2.5 对抗验证：让 Agent 互相吵架

4 个 Agent 并行审查会产生大量 findings，其中不乏误报。如果直接把所有 findings 丢给开发者，会被噪音淹没。

对抗验证（Adversarial Validation）借鉴了红蓝军对抗的思想：对每个 ERROR 级的 finding，派一个"辩护 Agent"尝试反驳它。

```
发现：函数 handlePayment 未校验 amount 是否为负数
  │
  ├─ 被 ≥2 子 agent 标记（同一文件）
  │   → 确认为真实问题，跳过反驳，必改
  │
  └─ 仅被 1 子 agent 标记
      ├─ 指派独立 verifier 子 agent 尝试反驳
      │   → 找到反驳证据：第 37 行有 if (amount < 0) return Err 的前置检查
      │     → 反驳成功（refuted），降级为 WARN
      │
      └─ 找不到反驳证据
          → 反驳失败（confirmed），确认为真实问题，必改
```

verifier 必须引用具体代码作为反驳证据，不允许仅凭"看起来没问题"反驳。找不到反驳证据必须诚实承认反驳失败。

### 2.6 修复轮次上限

Mini-Apply（对 Must-Fix 的 TDD 修复）上限 **2 轮**。超过 2 轮仍有 Must-Fix，说明初始方案（Proposal）有根本问题，回退到 Phase 2 重新设计，而非在错误基础上继续修补。

### 2.7 知识归档

每个大改动强制输出结构化的归档条目，存放在项目的 `archive/` 目录下（`archive/<YYYY-MM-DD>_<任务名>.md`）。归档记录问题定义、方案选择、关键决策和经验教训，形成可检索的组织知识库。

## 3. 流程详解

### 3.1 路由判定

收到开发任务时，主 Claude 判断变更规模。满足任一即大改动：影响 > 3 文件、涉及公开接口签名/数据模型/架构/第三方集成变更、用户明确要求。判定依据是变更的语义性质，而非任务描述里的关键词。小改动走普通流程（参考 `test-driven-development` 技能：先写失败测试→最少实现→重构 + 全量回归），不派发子 agent。

### 3.2 Phase 1: Explore（探索）

Explore 子 agent 读现有代码、分析 TODO/FIXME、识别影响范围与约束、列出风险点。退出条件：能回答三个问题——要解决什么问题？影响哪些东西？有哪些硬约束？

### 3.3 Phase 2: Proposal（方案）

Proposal 阶段的核心产出是 **Spec 清单**——一组可以独立实现、独立测试的行为描述。

#### Spec 的三要素

每个 Spec 必须包含：

1. **前置条件**（Before）：在什么状态下
2. **操作/输入**（Action）：执行什么操作
3. **预期结果**（After）：系统应该是什么状态

#### Spec 的覆盖要求

每个功能特性，必须覆盖三类路径：

- **正面路径**（Happy Path）：正常输入 → 正常输出（至少 1 个 Spec）
- **边界路径**（Edge Case）：空值/极值/最大最小值（至少 1 个 Spec）
- **负面路径**（Negative Path）：非法输入 → 错误处理（至少 1 个 Spec）

#### 产物：proposal.md

```markdown
# Proposal: 用户认证系统

## Spec 清单

### Spec-01: 正常登录
- 前置条件：用户已注册，密码为 bcrypt hash
- 操作：POST /login，传入 username + password
- 预期结果：返回 JWT token，有效期 7 天
- 对应测试：test_login_success

### Spec-02: 密码错误
- 前置条件：用户已注册
- 操作：POST /login，传入错误的 password
- 预期结果：返回 401，body 含 "invalid credentials"
- 对应测试：test_login_wrong_password

### Spec-03: 用户不存在
- 前置条件：用户未注册
- 操作：POST /login，传入未注册的 username
- 预期结果：返回 401，body 含 "invalid credentials"（不暴露用户名是否存在）
- 对应测试：test_login_user_not_found

### Spec-04: Token 刷新
- 前置条件：用户已登录，持有有效 token
- 操作：POST /refresh_token
- 预期结果：返回新 token，旧 token 失效
- 对应测试：test_token_refresh

## 技术决策
- JWT 签名算法：HS256（简单）vs RS256（安全）→ 选 HS256，因为不需要跨服务验证
- 密码 hashing：bcrypt，cost factor = 12
- Token 存储：客户端 localStorage（前端）/ httpOnly cookie（后端）

## 已知取舍
- 选择 7 天有效期是为了用户体验，牺牲了一点安全性（可以在后续引入 refresh token 机制）
- 没有做 rate limiting，假设上游有网关防护
```

### 3.4 Phase 3: Apply（TDD 实现）

Apply 阶段是机械性的：拿着 Proposal 的 Spec 清单，逐个实现。

#### TDD 循环

```
取下一个 Spec
  │
  ├─ Red（写失败的测试）
  │   → 测试描述 Spec 的预期行为
  │   → 运行测试，必须 FAIL
  │
  ├─ Green（写最少代码通过测试）
  │   → 只写让测试通过的最少代码
  │   → 运行测试，必须 PASS
  │   → 运行全量测试，必须全部 PASS
  │
  ├─ Refactor（测试保护下重构）
  │   → 删除重复代码
  │   → 改善命名和结构
  │   → 运行全量测试，必须全部 PASS
  │
  └─ 下一个 Spec
```

#### 集成验证

所有 Spec 实现完成后：

1. 运行全量测试套件
2. 检查 Proposal 里的每个 Spec 是否都有对应的测试
3. 检查测试是否真正验证了预期行为（不是只测了 happy path）

### 3.5 Phase 4: Review（多 Agent 交叉验证）

Review 阶段分为 5 个子步骤：

```
4a. Mini-Explore（识别审查范围）
4b. 4 Agent 并行审查
4c. 对抗验证
4d. 汇总分级
4e. Mini-Apply（TDD 修复，≤2 轮）
```

#### 4a. Mini-Explore

主 Agent 列出本次变更的所有文件，识别审查重点。

#### 4b. 4 Agent 并行审查

4 个 Agent 独立运行，互不通信，各自输出 JSON 格式的 findings。

每个 Agent 的输出结构：

```json
{
  "agent": "Correctness | Security | Performance | Test-Completeness",
  "findings": [
    {
      "id": "CR-001",
      "severity": "ERROR | WARN | INFO",
      "file": "src/auth/jwt.rs",
      "line": "37-42",
      "issue": "未校验 token 过期时间",
      "evidence": "第 37 行 token 生成后未设置 exp claim",
      "suggestion": "添加 exp claim，值为当前时间 + 7 天"
    }
  ],
  "summary": "整体逻辑正确，但缺少 token 过期校验",
  "verdict": "CONDITIONAL_PASS"
}
```

#### 4c. 对抗验证

汇总所有 findings，对 ERROR 级问题启动对抗验证：

```
每个 ERROR 级 finding
  │
  ├─ 被 ≥2 Agent 标记
  │   → 确认为真实问题，跳过反驳
  │
  └─ 仅被 1 Agent 标记
      │
      ├─ 指派辩护 Agent（与发现 Agent 不同类）
      │   读取相关文件 + 测试
      │   尝试反驳，输出 { refuted: true/false, reason: "<理由>" }
      │
      ├─ 反驳成功（refuted=true）
      │   → 降级为 WARN 或 INFO，记录反驳理由
      │
      └─ 反驳失败（refuted=false）
          → 确认为真实问题
```

#### 4d. 汇总分级

```
必改（Must Fix）
├─ 多证据确认（≥2 Agent 标记同一问题）
└─ 反驳失败的单 Agent ERROR

建议修复（Should Fix）
├─ 被反驳降级的 ERROR
└─ 所有 WARN

信息（Info Only）
└─ 所有 INFO
```

#### 4e. Mini-Apply（TDD 修复）

对每个"必改"问题，执行 TDD 修复：

1. 补测试：写一个能暴露此问题的测试 → 必须 FAIL
2. 改代码：修复问题 → 必须 PASS
3. 全量回归：运行全量测试 → 必须全部 PASS

**修复轮次上限：2 轮**。超过 2 轮仍有问题，说明初始方案有根本缺陷，回退到 Proposal 阶段重新设计。

### 3.6 Phase 5: Archive（归档）

Archive 阶段强制输出结构化的知识条目，存放在项目的 `archive/` 目录下。

#### 归档条目结构

```markdown
# Task: 用户认证系统

## Meta
- 日期：2026-06-17
- 作者：张三
- 影响文件数：12
- Spec 数量：8
- 测试覆盖：12 个测试用例
- Review 发现：2 ERROR（已修复）+ 3 WARN（已修复）+ 1 INFO

## 问题定义
实现用户认证系统，支持登录、登出、token 刷新。

## 方案选择
考虑了三种方案：
- 方案 A：Session（传统）
- 方案 B：JWT（无状态）✓ 采用
- 方案 C：OAuth2（过重）

选择 B 的原因：需要跨域支持，Session 需要额外的 session store

## 关键决策
1. **JWT 签名算法**：HS256 vs RS256
   - 选 HS256，因为不需要跨服务验证
   - 取舍：如果未来需要跨服务验证，需要迁移到 RS256

2. **Token 有效期**：7 天
   - 权衡：安全性（短）vs 用户体验（长）
   - 后续：可以引入 refresh token 机制

3. **密码 hashing**：bcrypt，cost factor = 12
   - 测试：登录耗时约 200ms，可接受
   - 备选：argon2（更新但生态不成熟）

## 学到了什么
- bcrypt 的 cost factor 每增加 1，耗时翻倍
- 某些旧浏览器（IE11）不支持 JWT 的 RS256 算法
- Token 放在 httpOnly cookie 比 localStorage 更安全（防 XSS）
```

## 4. 目录结构

```
项目目录
└── .sdd-tdd/                        # 流程状态目录（自动创建）
    ├── .dev-flow-state.json         # 流程状态文件
    ├── explore_report.md            # Explore 产物
    ├── proposal.md                  # Proposal 产物（含 Spec 清单）
    ├── apply_log.md                 # Apply 日志（TDD 循环记录）
    ├── review_report.md             # Review 报告（多 Agent findings + 对抗验证）
    └── archive_entry.md             # Archive 条目

项目目录
└── archive/                         # 归档目录（持久化）
    ├── 2026-06-17_user-auth.md      # 用户认证系统
    ├── 2026-06-18_payment-gateway.md
    └── ...
```

## 5. 可推广性

### 5.1 适用范围

本范式适用于任何需要结构化开发流程的场景：

- **新功能开发**：用户认证、支付网关、权限系统
- **架构重构**：模块化拆分、数据库迁移、API 升级
- **复杂 bug 修复**：并发问题、性能瓶颈、安全漏洞

### 5.2 团队推广

团队推广的关键是**降低门槛**：

1. **不需要全员掌握**：只需要 1-2 个人掌握完整流程，其他人可以直接使用
2. **渐进式采纳**：先从"小改动走普通流程"开始，逐步引入大改动的完整流程
3. **archive 复用**：新人可以通过查阅 archive 快速了解系统的设计决策和历史取舍

### 5.3 与现有工具链集成

- **Git**：每个阶段的产物都可以 commit，形成可追溯的开发历史
- **CI/CD**：Apply 阶段的全量测试可以集成到 CI pipeline
- **文档系统**：Archive 可以导入 Notion/Confluence 作为项目文档

## 6. 后续优化方向

### 6.1 进行中的

- **Review Agent 的专精化**：针对特定技术栈（如 Rust、Go、Python）的 Review Agent 定制
- **Archive 的智能化检索**：用向量数据库索引 archive，支持语义搜索

### 6.2 规划中的

- **跨项目 Archive 共享**：多个项目共享一个 archive 库，避免重复踩坑
- **Review 规则的自动演进**：类似 SDR 的 `/sdr-archive`，从 Review findings 中提炼出通用规则
- **可视化的开发流程看板**：在 VSCode/IDE 中可视化各个 Phase 的进度和产物

## 7. 参考文献

- [Spec-Driven Development (SDD)](https://en.wikipedia.org/wiki/Specification-driven_development)
- [Test-Driven Development (TDD)](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [Multi-Agent Code Review](https://www.qodo.ai/blog/the-next-generation-of-ai-code-review-from-isolated-to-system-intelligence/)
- [Adversarial Validation](https://machinelearningmastery.com/adversarial-validation/)
- SD-Reviewer Skill（本项目的 Review 阶段借鉴了 SDR 的多 Agent 审查模式）
