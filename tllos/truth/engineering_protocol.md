# TLL OS Engineering Protocol — 工程协议

> **TLL OS 的工程协议。**
> 所有 Agent 接入 TLL OS、所有施工阶段、所有功能开发，都必须遵守本协议。
>
> **核心：Claim + Evidence + Test + CI + Risk + Status = 完整工程闭环。**

---

## 1. 工程闭环

TLL OS 要求每个施工阶段形成完整的工程闭环：

```
Claim (功能声明)
   ↓
Evidence (证据)
   ↓
Test (测试)
   ↓
CI (持续集成，当前可选)
   ↓
Risk (风险评估)
   ↓
Status (状态判定)
   ↓
Architect Audit (独立审计)
   ↓
PASS / REQUEST CHANGES
```

### 1.1 各环节要求

| 环节 | 要求 | 禁止 |
|------|------|------|
| **Claim** | 明确、可验证、有边界 | 模糊、夸大、无边界 |
| **Evidence** | commit SHA + test result + risk assessment | 凭印象、凭经验、无数据 |
| **Test** | Clean Build、真实运行、可复现 | timeout 当 PASS、旧二进制、凭感觉 |
| **CI** | （当前可选）自动构建 + 自动测试 | 跳过 CI 就宣布完成 |
| **Risk** | 如实记录 A-GAP / B-GAP | 隐瞒风险、淡化风险、忽略风险 |
| **Status** | PASS / FAIL / CONDITIONAL / UNVERIFIED | 自行宣布 SEALED / FINAL / PERFECT |
| **Audit** | 独立审计方直接读 GitHub 真实代码 | 直接采信施工方报告 |

---

## 2. 施工流程

### 2.1 标准施工流程

```
1. 接收施工令（架构师下达）
   ↓
2. 理解需求和边界
   ↓
3. 创建分支（feature/P[阶段]-[主题]）
   ↓
4. 小步实现（每步可验证）
   ↓
5. Clean Build（Fail-Closed）
   ↓
6. 运行测试（记录结果）
   ↓
7. 写 Evidence 文档（如实记录）
   ↓
8. git diff --check（代码规范检查）
   ↓
9. git add + commit（只提交源码和 Evidence）
   ↓
10. git push（推送到远程仓库）
   ↓
11. 停止，等待独立审计
   ↓
12. 审计 PASS → 进入下一阶段
    审计 REQUEST CHANGES → 修改后重新提交
```

### 2.2 关键纪律

1. **不自行宣布 PASS / SEALED**
   - 只有架构师独立审计后才能宣布
   - 施工方只负责实现和提交 Evidence

2. **没有远程 commit 不作为正式 Evidence**
   - 只有 push 到 GitHub 远程仓库的 commit 才是正式 Evidence
   - 本地 commit 只是草稿

3. **小步实现，每阶段独立验收**
   - 不要一次把所有功能做完再提交
   - 每个小阶段都要有明确的验收标准

4. **封板保护**
   - 已封板的阶段不随意修改
   - 新功能在新分支上开发

5. **如实记录风险**
   - 已知限制必须写入 Evidence
   - 禁止把"已缓解"写成"已修复"

---

## 3. Git 工作流

### 3.1 分支命名规范

```
feature/P[阶段编号]-[阶段名称]-[子阶段]
```

示例：
- `feature/P2-01-C-D3-runtime-high-frame-execution`
- `feature/P2-02-canonical-layer-genesis`

### 3.2 Commit Message 规范

```
P[阶段编号]-[阶段名称]: [一句话总结]

详细说明：
- 修改内容
- 测试结果
- 已知限制
- Evidence 文档位置

Architect decision (如有): [架构师裁决]
Implementer confirmation: [施工方确认]
```

### 3.3 提交内容规范

**必须提交：**
- 源码修改（.c / .h 等）
- Evidence 文档（docs/evidence/*.md）
- 测试用例（tests/*.tllbc 等）

**禁止提交：**
- 生成物（.exe / .obj / .tllbc 等）
- 临时诊断脚本（debug_*.tll / analyze_*.py 等）
- 临时输出文件（*_out.txt / *_err.txt 等）
- 个人配置文件（.vscode / .idea 等）

### 3.4 Push 规范

- Push 前确认：`git status` 只提交预期文件
- Push 目标：远程 feature 分支（不直接 push main）
- Push 失败（网络问题）：等待后重试，不换实现方案
- Push 成功后：立即停止，等待架构师审计

---

## 4. 测试规范

### 4.1 测试分级

| 级别 | 类型 | 要求 |
|------|------|------|
| **Gate-1** | 基础测试 | hello.tll 运行成功，exit code = 0 |
| **Gate-2** | 单协程测试 | 单协程创建、执行、完成 |
| **Gate-3** | 单 Worker 测试 | startWorkers(1) 正常返回 |
| **Gate-4** | 多 Worker 测试 | startWorkers(2) 正常返回 |
| **Regression** | 回归测试 | 已封板阶段的核心测试全部 PASS |
| **Stress** | 压力测试 | 高并发/大规模场景验证 |

### 4.2 测试运行规范

- 必须使用 Clean Build 的二进制
- 必须记录：source commit、binary SHA256、exit code、stdout、stderr、运行时间
- 禁止使用 PowerShell `Start-Process`（之前导致误报）
- 推荐使用 `System.Diagnostics.ProcessStartInfo`

### 4.3 测试结果判定

- **PASS**：exit code = 0，stdout 匹配预期
- **FAIL**：exit code ≠ 0，或 stdout 不匹配预期
- **CRASH**：exit code 为崩溃码（0xC0000005 / 0xC0000374 等）
- **TIMEOUT**：超时未退出
- **INTERMITTENT**：概率性失败（记录运行次数和成功/失败次数）

---

## 5. Evidence 提交规范

### 5.1 Evidence 文档结构

每个阶段的 Evidence 文档必须包含：

```markdown
# P[阶段]-[名称] Evidence

## Executive Summary
[一句话总结]

## Goal
[本阶段目标]

## Modifications
[修改内容：文件列表 + 说明]

## Build Evidence
[Build 结果：SHA / compiler / binary hash]

## Test Results
[测试结果：逐测试记录]

## Known Gaps
[已知限制：A-GAP / B-GAP]

## Conclusion
[结论：证据等级必须明确]

## Implementer Sign-off
[施工方确认]

## Architect Sign-off
[架构师签核（待审计）]
```

### 5.2 证据等级标注

每个结论必须标注证据等级：
- **OBSERVED**：观察到的现象
- **INFERRED**：基于观察的推断
- **UNVERIFIED**：未验证
- **PROVEN**：已证明
- **RULED OUT**：已排除

---

## 6. 审计规范

### 6.1 审计方职责

- 直接读取 GitHub 远程仓库的真实 commit
- 不直接采信施工方报告
- 独立验证关键代码和测试结果
- 检查 Evidence 是否如实记录
- 给出 PASS / REQUEST CHANGES 结论

### 6.2 审计重点

1. **commit 真实性**：commit 是否真实存在于远程仓库
2. **代码一致性**：代码修改是否与报告一致
3. **测试可复现性**：测试结果是否可复现
4. **Evidence 诚实性**：是否如实记录了所有结果（包括失败）
5. **风险完整性**：是否遗漏了已知限制和风险
6. **表述准确性**：是否把"已缓解"写成"已修复"、"条件通过"写成"完全通过"

---

## 7. 架构师裁决权

### 7.1 架构师（于秋鸿博士）的权力

- 最终裁决权：决定阶段是否通过、是否封板
- 方向决策权：决定下一阶段的技术方向和施工范围
- 风险否决权：可以否决任何有重大风险的方案
- 边界控制权：可以随时暂停某个阶段、缩小施工范围

### 7.2 施工方（豆包A）的职责

- 严格按施工令执行，不扩大范围
- 如实记录测试结果和已知限制
- 不自行宣布 PASS / SEALED
- 发现问题及时报告，不隐瞒
- 按规范提交 commit 和 Evidence

---

## 8. 禁止事项

以下行为严格禁止：

1. ❌ **为了 PASS 删除测试**
2. ❌ **修改 Evidence 来匹配结果**
3. ❌ **没有 Clean Build 就测试**
4. ❌ **使用旧二进制测试**
5. ❌ **自行宣布 PASS / SEALED / FINAL**
6. ❌ **隐瞒已知限制和风险**
7. ❌ **为了通过测试而扭曲架构**
8. ❌ **不按施工令执行，自行扩大范围**
9. ❌ **把 OBSERVED 写成 PROVEN**
10. ❌ **把 MITIGATED 写成 CLOSED**
11. ❌ **把 CONDITIONAL 写成 SEALED**
12. ❌ **未经授权 push main 分支**

---

## 9. 常见问题

### Q: 测试失败了怎么办？

A: 如实记录失败结果，分析原因，提出修复方案，等待架构师裁决。不要为了通过测试而修改测试或 Evidence。

### Q: 发现了新的 bug 怎么办？

A: 记录为 A-GAP 或 B-GAP，如实报告，等待架构师决定是否阻塞当前阶段。

### Q: 施工令要求的范围太大怎么办？

A: 向架构师报告，请求缩小范围或分阶段执行。不要自行减少范围或跳过要求。

### Q: 网络问题导致 push 失败怎么办？

A: 等待后重试，通常可以成功。不要因为网络问题而改变实现方案。

### Q: 我觉得施工令有问题怎么办？

A: 向架构师报告你的疑虑和理由，等待架构师裁决。不要自行修改施工令的范围或方向。

---

*本文档是 TLL OS 的 Engineering Protocol，所有施工阶段必须遵守。*
*最后更新：2026-09-11*
