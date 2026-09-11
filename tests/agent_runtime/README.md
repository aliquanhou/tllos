# TLL OS Agent Runtime Foundation — Test Suite

**Project:** TLL OS
**Phase:** P2-03 Agent Runtime Foundation
**Date:** 2026-09-11

---

## Test 1: Agent Boot Flow

**目的：** 验证 Agent Boot Protocol 的读取顺序正确。

### 测试步骤

1. **Step 1: Load Genesis**
   - 读取 `tllos/identity/genesis.json`
   - 验证：os_name == "TLL OS"
   - 预期：✅ PASS

2. **Step 2: Verify Manifest**
   - 读取 `tllos/identity/canonical_manifest.json`
   - 验证：integrity_level == "git_anchored_integrity"
   - 预期：✅ PASS

3. **Step 3: Read Agent Contract**
   - 读取 `tllos/agents/agent_contract.md`
   - 验证：包含权利、义务、拒绝权
   - 预期：✅ PASS

4. **Step 4: Declare Capability**
   - 读取 `tllos/agent_runtime/capability_declaration.schema.json`
   - 验证：schema 存在
   - 预期：✅ PASS

### 测试结果

| Step | 文件 | 结果 |
|------|------|------|
| 1. Load Genesis | genesis.json | ✅ PASS |
| 2. Verify Manifest | canonical_manifest.json | ✅ PASS |
| 3. Read Contract | agent_contract.md | ✅ PASS |
| 4. Declare Capability | capability_declaration.schema.json | ✅ PASS |

**Test 1 Result: ✅ PASS**

---

## Test 2: Capability Boundary

**目的：** 验证 Agent 请求越权任务时，必须被拒绝。

### 测试场景

**场景 A: 合法任务**
- Agent: developer（权限：read=canonical/evidence, write=evidence/docs/code）
- 任务：修改 `docs/evidence/*.md`
- 预期：✅ 允许

**场景 B: 越权任务**
- Agent: developer
- 任务：修改 `host/c/vm.c`（Runtime Core）
- 预期：❌ 必须拒绝

### 测试结果

| 场景 | 任务 | 预期 | 结果 |
|------|------|------|------|
| A: 合法 | 修改 Evidence 文档 | 允许 | ✅ PASS |
| B: 越权 | 修改 Runtime Core | 拒绝 | ✅ PASS |

**Test 2 Result: ✅ PASS**

---

## Test 3: Evidence Requirement

**目的：** 验证没有 Evidence 的完成声明，必须被拒绝。

### 测试场景

**场景 A: 有 Evidence 的 Claim**
- Agent 完成任务
- 提交：commit_sha + test_results
- 状态：OBSERVED
- 预期：✅ 接受

**场景 B: 没有 Evidence 的 Claim**
- Agent 完成任务
- 提交：只有 "完成了"
- 没有 evidence 字段
- 预期：❌ 必须拒绝

### 测试结果

| 场景 | Evidence | 预期 | 结果 |
|------|----------|------|------|
| A: 有 Evidence | commit_sha + test_results | 接受 | ✅ PASS |
| B: 无 Evidence | 无 evidence 字段 | 拒绝 | ✅ PASS |

**Test 3 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | 结果 |
|------|------|------|
| Test 1 | Agent Boot Flow | ✅ PASS |
| Test 2 | Capability Boundary | ✅ PASS |
| Test 3 | Evidence Requirement | ✅ PASS |

**Overall: 3/3 PASS (Phase 1)**

---

## Test 4: Permission Missing (P2-03.2)

**目的：** 验证没有 permission 字段的 task 必须被拒绝。

### 测试场景

**场景 A: 缺少 permission 的 task**
- Task: 执行写操作
- 缺少 permission_id 字段
- 预期：❌ REJECT（PERMISSION_DENIED）

**场景 B: 有 permission 的 task**
- Task: 执行写操作
- permission_id: perm-001（approved）
- 预期：✅ ALLOW

### 测试结果

| 场景 | permission | 预期 | 结果 |
|------|------------|------|------|
| A: 缺少 permission | 无 permission_id | REJECT | ✅ PASS |
| B: 有 permission | perm-001 (approved) | ALLOW | ✅ PASS |

**Test 4 Result: ✅ PASS**

---

## Test 5: Capability Escalation (P2-03.2)

**目的：** 验证 permission 超出 capability 范围时必须被拒绝。

### 测试场景

**场景 A: 合法 escalation**
- Agent capability: write_evidence
- Requested permission: write:evidence
- 预期：✅ ALLOW（在 capability 范围内）

**场景 B: 非法 escalation**
- Agent capability: read_code
- Requested permission: write:code
- 预期：❌ REJECT（read_code 不包含 write:code）

**场景 C: 超宽 capability**
- Agent capability: filesystem（太宽泛）
- Requested permission: write_all
- 预期：❌ REJECT（capability 必须精确）

### 测试结果

| 场景 | capability | requested permission | 预期 | 结果 |
|------|-----------|---------------------|------|------|
| A: 合法 | write_evidence | write:evidence | ALLOW | ✅ PASS |
| B: 越权 | read_code | write:code | REJECT | ✅ PASS |
| C: 超宽 | filesystem | write_all | REJECT | ✅ PASS |

**Test 5 Result: ✅ PASS**

---

## Test 6: Valid Execution Boundary (P2-03.2)

**目的：** 验证合法的 execution request 流程完整。

### 测试步骤

1. **Step 1: 声明 capability**
   - Agent: doubao-a
   - capability: write_evidence
   - 预期：✅ PASS

2. **Step 2: 申请 permission**
   - permission_type: write:evidence
   - state: requested
   - 预期：✅ PASS

3. **Step 3: 批准 permission**
   - state: requested → approved
   - approved_by: owner
   - 预期：✅ PASS（由系统/裁决方设置）

4. **Step 4: 创建 execution request**
   - request_id: exec-req-001
   - permission_id: perm-001 (approved)
   - action: write_evidence
   - 预期：✅ PASS

5. **Step 5: 执行并返回结果**
   - status: SUCCESS
   - evidence: { file_hash, commit_sha }
   - 预期：✅ PASS

### 测试结果

| Step | 步骤 | 结果 |
|------|------|------|
| 1 | 声明 capability | ✅ PASS |
| 2 | 申请 permission | ✅ PASS |
| 3 | 批准 permission | ✅ PASS |
| 4 | 创建 execution request | ✅ PASS |
| 5 | 执行并返回结果 | ✅ PASS |

**Test 6 Result: ✅ PASS**

---

## Test 7: Missing Permission (P2-03.3)

**目的：** 验证 Gateway 收到缺少 permission_id 的请求时必须拒绝。

### 测试场景

**场景 A: Gateway 请求缺少 permission_id**
- Gateway Request: { task_id, agent_id, action, input }
- 缺少 permission_id
- 预期：❌ REJECT（MISSING_PERMISSION）

**场景 B: Gateway 请求缺少 task_id**
- Gateway Request: { permission_id, agent_id, action, input }
- 缺少 task_id
- 预期：❌ REJECT（MISSING_TASK_ID）

### 测试结果

| 场景 | 缺少字段 | 预期 | 结果 |
|------|----------|------|------|
| A: 缺少 permission_id | permission_id | REJECT | ✅ PASS |
| B: 缺少 task_id | task_id | REJECT | ✅ PASS |

**Test 7 Result: ✅ PASS**

---

## Test 8: Missing Evidence (P2-03.3)

**目的：** 验证 Gateway 收到 evidence_required=false 的请求时必须拒绝。

### 测试场景

**场景 A: evidence_required = false**
- Gateway Request: { ..., evidence_required: false }
- 预期：❌ REJECT（EVIDENCE_REQUIRED）

**场景 B: evidence_required 缺失**
- Gateway Request: { ... }（没有 evidence_required 字段）
- 预期：❌ REJECT（MISSING_FIELD）

### 测试结果

| 场景 | evidence_required | 预期 | 结果 |
|------|-------------------|------|------|
| A: evidence_required=false | false | REJECT | ✅ PASS |
| B: evidence_required 缺失 | undefined | REJECT | ✅ PASS |

**Test 8 Result: ✅ PASS**

---

## Test 9: Valid Gateway Request (P2-03.3)

**目的：** 验证合法的 Gateway 请求通过所有检查。

### 测试步骤

1. **Step 1: 创建 Gateway Request**
   - gateway_request_id: gw-req-001
   - task_id: P2-03.3-TEST-001
   - agent_id: doubao-a
   - capability: write_evidence
   - permission_id: perm-001 (approved)
   - action: write_evidence_file
   - evidence_required: true
   - 预期：✅ PASS

2. **Step 2: Gateway 检查**
   - ✅ task_id 存在
   - ✅ permission_id 存在
   - ✅ capability 存在
   - ✅ evidence_required = true
   - 预期：✅ ALLOWED

3. **Step 3: 转发到 Runtime Adapter**
   - runtime_request_id: rt-req-001
   - 预期：✅ PASS

### 测试结果

| Step | 步骤 | 结果 |
|------|------|------|
| 1 | 创建 Gateway Request | ✅ PASS |
| 2 | Gateway 检查 | ✅ PASS |
| 3 | 转发到 Runtime Adapter | ✅ PASS |

**Test 9 Result: ✅ PASS**

---

## Test 10: Runtime Adapter Boundary (P2-03.3)

**目的：** 验证 Runtime Adapter 只定义接口，不执行 Runtime。

### 测试场景

**场景 A: 接口定义存在**
- runtime_adapter.md 存在
- runtime_request.json 存在
- runtime_result.json 存在
- 预期：✅ PASS

**场景 B: 不调用 vm.c**
- 确认：Adapter 没有调用 vm.c
- 确认：Adapter 没有修改 Runtime Core
- 预期：✅ PASS

**场景 C: 不直接访问 coroutine/scheduler**
- 确认：Adapter 没有直接访问 coroutine
- 确认：Adapter 没有直接访问 scheduler
- 预期：✅ PASS

### 测试结果

| 场景 | 检查项 | 预期 | 结果 |
|------|--------|------|------|
| A: 接口定义存在 | 3 个文件存在 | PASS | ✅ PASS |
| B: 不调用 vm.c | 无 vm.c 调用 | PASS | ✅ PASS |
| C: 不访问 coroutine | 无 coroutine 直接访问 | PASS | ✅ PASS |

**Test 10 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | Phase | 结果 |
|------|------|-------|------|
| Test 1 | Agent Boot Flow | Phase 1 | ✅ PASS |
| Test 2 | Capability Boundary | Phase 1 | ✅ PASS |
| Test 3 | Evidence Requirement | Phase 1 | ✅ PASS |
| Test 4 | Permission Missing | P2-03.2 | ✅ PASS |
| Test 5 | Capability Escalation | P2-03.2 | ✅ PASS |
| Test 6 | Valid Execution Boundary | P2-03.2 | ✅ PASS |
| Test 7 | Missing Permission | P2-03.3 | ✅ PASS |
| Test 8 | Missing Evidence | P2-03.3 | ✅ PASS |
| Test 9 | Valid Gateway Request | P2-03.3 | ✅ PASS |
| Test 10 | Runtime Adapter Boundary | P2-03.3 | ✅ PASS |

**Overall: 10/10 PASS**

---

*TLL OS Agent Runtime Foundation Test Suite*
