# Review Report 格式规范

本文件定义了 Review 阶段各 Agent 的输出格式。所有审查 Agent 必须严格遵循。

---

## JSON Schema

```json
{
  "agent": "<Agent 标识符>",
  "findings": [
    {
      "id": "<Agent 前缀>-<三位数字>",
      "severity": "ERROR | WARN | INFO",
      "file": "<相对于项目根目录的文件路径>",
      "line": "<行号或行范围，如 37 或 37-42>",
      "issue": "<一句话描述问题，不超过 50 字>",
      "evidence": "<具体证据：代码片段引用和上下文说明>",
      "suggestion": "<修复建议，可执行且具体>"
    }
  ],
  "summary": "<整体评价，一句话，不超过 100 字>",
  "verdict": "PASS | CONDITIONAL_PASS | FAIL"
}
```

---

## Agent 标识符

| Agent | 标识符 | Finding ID 前缀 |
|-------|--------|-----------------|
| Correctness Reviewer | `Correctness` | `COR-` |
| Security Reviewer | `Security` | `SEC-` |
| Performance Reviewer | `Performance` | `PER-` |
| Test-Completeness Reviewer | `Test-Completeness` | `TST-` |

Example: `COR-001`, `SEC-002`, `PER-001`, `TST-003`

---

## Severity 定义

### ERROR（必须修复）

以下情况任一即标为 ERROR：
- 逻辑错误，可直接导致 bug
- 安全漏洞，可被恶意利用
- 数据丢失或数据损坏风险
- 资源泄漏（生产环境会导致系统不可用）
- Spec 缺失（关键行为无测试覆盖）

### WARN（建议修复）

以下情况任一即标为 WARN：
- 可读性问题（命名不清、结构混乱）
- 可维护性问题（代码重复、耦合过紧）
- 性能退化风险（在高负载下才会显现）
- 安全最佳实践缺失（当前不可直接利用，但有风险）
- 测试质量不足（断言过于宽松、测试隔离问题）

### INFO（信息记录）

以下情况任一即标为 INFO：
- 改进建议（非紧迫，但长期有益）
- 观察记录（值得了解但目前无需行动）
- 文档完善建议

---

## Verdict 定义

### PASS
- 无 ERROR
- WARN ≤ 2（不同 Agent 有不同阈值，见各 Agent 定义）
- 代码质量达标，可以进入下一阶段

### CONDITIONAL_PASS
- 有 ERROR 但修复方案明确
- 或 WARN 数量较多（> 阈值）
- 修复后可以进入下一阶段，但必须先处理 ERROR

### FAIL
- 有 ERROR 且修复需要重新设计方案
- 或代码质量严重不达标
- **必须回退到之前的阶段**

---

## 格式约束

### 必须遵守

1. **严格 JSON**：输出必须是合法 JSON，可以被 `json.loads()` 解析
2. **无 Markdown**：禁止 ```json``` 包裹符，禁止 Markdown 表格/列表
3. **无额外文字**：禁止 JSON 前后的任何文字（包括 "Here is the report"、"Summary:" 等）
4. **UTF-8 编码**：所有字符串使用 UTF-8
5. **路径规范**：文件路径相对于项目根目录，使用正斜杠 `/`
6. **行号准确**：必须经过验证，不允许"大约"行号

### 禁止行为

- ❌ 在 JSON 中添加注释
- ❌ 输出不完整的 JSON
- ❌ 添加 `spec` 类别（各 Agent 有各自的审查重点，不要越界）
- ❌ 添加 `references` 字段（引用通过 evidence 字段体现）
- ❌ 使用 emoji

---

## Test-Completeness 扩展字段

Test-Completeness Agent 在标准字段基础上，额外输出覆盖率统计：

```json
{
  "agent": "Test-Completeness",
  "findings": [...],
  "summary": "...",
  "verdict": "...",
  "spec_coverage": {
    "total": 8,
    "covered": 7,
    "missing": ["Spec-05"],
    "coverage_percent": 87.5
  },
  "path_coverage": {
    "happy": {"total": 3, "covered": 3},
    "edge": {"total": 3, "covered": 2},
    "negative": {"total": 2, "covered": 2}
  }
}
```

---

## Example Output

### Correctness Agent 示例

```json
{
  "agent": "Correctness",
  "findings": [
    {
      "id": "COR-001",
      "severity": "ERROR",
      "file": "src/auth/jwt.rs",
      "line": "37-42",
      "issue": "未校验 token 过期时间",
      "evidence": "verify_token() 函数在 src/auth/jwt.rs:37 解析了 JWT payload，但未检查 exp claim。代码：let payload = decode_jwt(token)?; // 仅验证签名，未检查 payload.exp < now。如果 token 过期但签名有效，函数仍返回 Ok(user_id)，导致过期 token 被接受。",
      "suggestion": "在 verify_token() 中解析 payload 后添加 exp 校验：if payload.exp < current_timestamp() { return Err(AuthError::TokenExpired) }。建议同时添加测试 test_verify_token_expired 覆盖此场景。"
    },
    {
      "id": "COR-002",
      "severity": "WARN",
      "file": "src/api/login.rs",
      "line": "78-92",
      "issue": "handle_login 错误处理可能掩盖底层错误",
      "evidence": "src/api/login.rs:85 对 auth_service.authenticate() 的错误使用了 match _ => Err(AuthError::InvalidCredentials)，将所有底层错误（数据库连接失败、内部服务超时等）都统一映射为 InvalidCredentials，导致难以排查真实故障原因。",
      "suggestion": "细化错误处理：match auth_service.authenticate() { Ok(user) => ..., Err(AuthError::InvalidCredentials) => ..., Err(e) => { log_error(e); Err(AuthError::Internal) } }。这样既保护了敏感信息（不暴露内部错误细节），又保留了日志可追踪性。"
    }
  ],
  "summary": "核心逻辑基本正确，但 token 过期校验存在漏洞，需要补充 exp claim 检查",
  "verdict": "CONDITIONAL_PASS"
}
```

### Test-Completeness Agent 示例

```json
{
  "agent": "Test-Completeness",
  "findings": [
    {
      "id": "TST-001",
      "severity": "ERROR",
      "file": "proposal.md",
      "line": "Spec-05",
      "issue": "Spec-05（边界：空用户名）缺少对应测试",
      "evidence": "Proposal 在 Spec-05 中定义了空用户名场景：'传入 username=\"\"，预期返回 ValidationError'。但在所有测试文件中未找到对应测试函数。grep 'test_.*login.*empty' tests/ 返回 0 结果。",
      "suggestion": "添加 test_login_empty_username 测试：输入 username=''，断言返回 Err(ValidationError::EmptyUsername)。如果该场景已在其他测试中覆盖（如 test_login_validation），需在 proposal.md 的 Spec-05 对应测试字段中更新映射。"
    }
  ],
  "spec_coverage": {
    "total": 8,
    "covered": 7,
    "missing": ["Spec-05"],
    "coverage_percent": 87.5
  },
  "path_coverage": {
    "happy": {"total": 3, "covered": 3},
    "edge": {"total": 3, "covered": 2},
    "negative": {"total": 2, "covered": 2}
  },
  "summary": "Spec 覆盖率 87.5%，缺少 Spec-05 的边界路径测试",
  "verdict": "CONDITIONAL_PASS"
}
```
