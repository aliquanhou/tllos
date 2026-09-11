# TLL OS Evidence Rules — 证据规范

> **TLL OS 的第一工程原则：没有 Evidence，不生成 Claim。**
> 本文档定义 TLL OS 所有施工阶段必须遵循的证据规范。
>
> 任何 Agent、任何施工方、任何功能声明，都必须遵守本规范。

---

## 1. 核心原则

### 1.1 没有 Evidence，不生成 Claim

**这是 TLL OS 的第一工程原则，没有例外。**

- 功能声明必须有 Evidence 支撑
- 性能声明必须有 benchmark 数据支撑
- 正确性声明必须有测试结果支撑
- 安全性声明必须有审计结果支撑

**禁止：**
- ❌ 凭感觉说"应该没问题"
- ❌ 凭经验说"这个方案是对的"
- ❌ 凭类比说"和某某系统一样"
- ❌ 凭文档说"代码应该是这样"

### 1.2 证据等级必须明确

每个 Claim 必须标注证据等级，禁止模糊表述。

| 证据等级 | 含义 | 使用场景 |
|----------|------|----------|
| **OBSERVED** | 观察到的现象，未经严格验证 | 初步发现、调试输出、手动测试结果 |
| **INFERRED** | 基于观察的合理推断，未经直接证明 | 根因分析、架构推断、性能预估 |
| **UNVERIFIED** | 未验证，可能正确也可能不正确 | 待验证的假设、未运行的测试、未审计的代码 |
| **PROVEN** | 通过实验/测试/审计直接证明 | 核心功能正确性、关键路径性能、安全审计结论 |
| **RULED OUT** | 通过实验/测试排除 | 已排除的根因、已排除的风险、已排除的方案 |

**禁止：**
- ❌ 把 OBSERVED 写成 PROVEN
- ❌ 把 INFERRED 写成 PROVEN
- ❌ 把 UNVERIFIED 写成 PROVEN
- ❌ 把"可能"写成"一定"
- ❌ 把"测试通过"写成"没有 bug"

---

## 2. Claim 格式规范

每个功能声明（Claim）必须包含以下字段：

```markdown
## Claim: [功能名称]

**Claim:** [一句话描述功能/能力/结果]

**Evidence:**
- commit: [完整 SHA]
- test: [测试名称和结果]
- CI: [CI 状态（如有）]
- risk: [风险评估]
- evidence_level: [OBSERVED / INFERRED / UNVERIFIED / PROVEN / RULED OUT]

**Status:** [PASS / FAIL / CONDITIONAL / UNVERIFIED]

**Known Limitations:** [已知限制（如有）]
```

### 2.1 示例：正确的 Claim

```markdown
## Claim: D2 Multi-Worker 7/7 核心测试通过

**Claim:** D2 核心 Worker Runtime 的 7 个核心测试在 Clean Build 下全部 PASS。

**Evidence:**
- commit: e1b6e8fa6dff687a7cfd58bea8abb970f4b28d44
- test: multi_worker_parallel (PASS), multi_worker_overlap_proof (PASS),
         multi_worker_stress_2w_100t (PASS), worker_global_test (PASS),
         simple_sleep_wakeup_test (PASS), worker_ownership_boundary (PASS),
         wake_list_300_coroutines (PASS)
- CI: N/A（当前无 CI）
- risk: 低（7/7 全部正常退出，无 HANG/DEADLOCK）
- evidence_level: PROVEN

**Status:** PASS

**Known Limitations:** A-GAP-1（10K+ coroutine 概率性崩溃）为已知限制，不阻塞 D2 封板。
```

### 2.2 示例：错误的 Claim

```markdown
## Claim: Runtime Core v0 完美无缺

**Claim:** TLL Runtime Core v0 已经完全稳定，没有任何 bug。

**Evidence:**
- commit: 13847f3
- test: 一些测试通过了
- risk: 无风险
- evidence_level: PROVEN

**Status:** PASS
```

**错误原因：**
- "一些测试通过了"不是明确的测试结果
- "无风险"没有证据支撑
- 忽略了 A-GAP-1 已知限制
- 证据等级标注错误

---

## 3. 测试证据规范

### 3.1 测试必须真实运行

- 测试必须在 Clean Build 下运行（无旧 .obj / 无旧 .exe）
- 测试结果必须记录：exit code、stdout、stderr、运行时间
- 禁止凭印象写"测试通过"
- 禁止使用 timeout 作为 PASS（除非测试本身就是 timeout 测试）

### 3.2 测试必须可复现

- 测试脚本必须提交到仓库
- 测试输入（.tllbc 等）必须提交到仓库
- 测试运行命令必须明确记录
- 测试环境（编译器版本、OS 版本）必须记录

### 3.3 测试结果分级

| 结果 | 含义 | 记录要求 |
|------|------|----------|
| PASS | 测试正常退出，输出符合预期 | exit code = 0，stdout 匹配预期 |
| FAIL | 测试异常退出，输出不符合预期 | exit code ≠ 0，记录错误信息 |
| TIMEOUT | 测试超时未退出 | 记录超时时间和部分输出 |
| CRASH | 测试崩溃（ACCESS_VIOLATION / HEAP_CORRUPTION 等） | 记录崩溃码和错误信息 |
| INTERMITTENT | 概率性失败（有时 PASS 有时 FAIL） | 记录运行次数和成功/失败次数 |

---

## 4. Build 证据规范

### 4.1 Clean Build 是强制要求

- 所有测试必须在 Clean Build 下运行
- 禁止使用旧 .obj 链接新测试
- 禁止编译失败后继续 link
- build script 必须 Fail-Closed（编译失败立即终止）

### 4.2 Build Provenance

每个测试必须记录：
- Source Commit: [完整 SHA]
- Build Time: [构建时间戳]
- Compiler: [编译器版本]
- Build Command: [构建命令]
- vm.obj SHA256: [值]
- tllvm.exe SHA256: [值]
- Build Result: SUCCESS / FAILURE

**目的：** 证明测试运行的二进制确实来自指定的源码 commit。

---

## 5. 风险记录规范

### 5.1 A-GAP / B-GAP 分级

| 级别 | 含义 | 处理方式 |
|------|------|----------|
| **A-GAP** | 架构级阻塞缺陷，影响核心功能正确性 | 阻塞当前阶段封板，必须解决或 MITIGATED |
| **B-GAP** | 非阻塞缺陷，不影响当前阶段核心功能 | 记录在案，后续阶段处理 |

### 5.2 A-GAP 记录格式

```markdown
## A-GAP-[编号]: [标题]

**Status:** OPEN / MITIGATED / CLOSED

**Trigger:** [触发条件]

**Crash Location:** [崩溃位置（如适用）]

**Nature:** [性质：确定性 / 概率性]

**Evidence:**
- PROVEN: [已证明的事实]
- RULED OUT: [已排除的假设]
- UNVERIFIED: [未验证的假设]
- INFERRED: [推断的结论]

**Mitigation:** [缓解措施（如有）]

**Risk:** [风险等级]

**Future Requirement:** [未来必须解决的事项]
```

### 5.3 B-GAP 记录格式

```markdown
## B-GAP-[编号]: [标题]

**Status:** OPEN (Non-Blocking)

**Description:** [描述]

**Impact:** [影响范围]

**Resolution Plan:** [后续解决计划]
```

---

## 6. Evidence 文档规范

### 6.1 命名规范

```
docs/evidence/P[阶段编号]-[阶段名称]-[主题].md
```

示例：
- `P2-01-C-D2-TRUE-MULTI-WORKER.md`
- `P2-01-C-D3-HIGH-FRAME-RUNTIME.md`
- `P2-01-C-D3-A-GAP1-ROOT-CAUSE.md`

### 6.2 文档结构

每个 Evidence 文档必须包含：

1. **Executive Summary**：一句话总结
2. **Goal**：本阶段目标
3. **Modifications**：修改内容（文件列表 + 说明）
4. **Build Evidence**：Build 结果（SHA / compiler / binary hash）
5. **Test Results**：测试结果（逐测试记录）
6. **Known Gaps**：已知限制（A-GAP / B-GAP）
7. **Conclusion**：结论（证据等级必须明确）
8. **Implementer Sign-off**：施工方确认
9. **Architect Sign-off**：架构师签核（待审计）

---

## 7. 独立审计规范

### 7.1 审计方独立

- 审计方（架构师）必须独立于施工方
- 审计方直接读取 GitHub 远程仓库的真实 commit
- 审计方不直接采信施工方报告
- 审计方独立验证关键代码和测试结果

### 7.2 审计内容

- commit 是否真实存在于远程仓库
- 代码修改是否与报告一致
- 测试结果是否可复现
- Evidence 是否如实记录
- 是否存在"测试跑了，但代码不是这个 commit"的问题
- 是否存在把失败吞掉的脚本
- 是否存在把"已缓解"写成"已修复"

### 7.3 审计结论分级

| 结论 | 含义 |
|------|------|
| **PASS** | 本阶段通过，可以封板/进入下一阶段 |
| **PASS WITH REQUIRED CORRECTION** | 核心发现正确，但措辞/细节需要修正 |
| **REQUEST CHANGES** | 不通过，需要修改后重新提交 |
| **CONDITIONAL PASS** | 有条件通过，记录已知限制后可以继续 |

---

## 8. 禁止事项

以下行为严格禁止：

1. ❌ **为了 PASS 删除测试**
2. ❌ **修改 Evidence 来匹配结果**
3. ❌ **没有 Clean Build 就测试**
4. ❌ **使用旧 tllvm.exe 测试**
5. ❌ **把 OBSERVED 写成 PROVEN**
6. ❌ **把 MITIGATED 写成 CLOSED**
7. ❌ **把 CONDITIONAL 写成 SEALED**
8. ❌ **自行宣布 PASS / SEALED / FINAL**
9. ❌ **隐瞒已知限制和风险**
10. ❌ **为了通过测试而扭曲架构**

---

*本文档是 TLL OS 的 Evidence Rules，所有施工阶段必须遵守。*
*最后更新：2026-09-11*
