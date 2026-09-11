# TLL OS Agent Runtime Foundation — Test Suite Phase 1

**Project:** TLL OS
**Phase:** P2-03 Agent Runtime Foundation Phase 1
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

**Overall: 3/3 PASS**

---

*TLL OS Agent Runtime Foundation Test Suite Phase 1*
