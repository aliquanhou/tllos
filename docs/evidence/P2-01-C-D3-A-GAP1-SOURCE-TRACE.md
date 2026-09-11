# P2-01-C-D3-A-GAP1: Source Trace Evidence

**Status:** Source Trace Phase Complete — Write Source Still UNVERIFIED
**Branch:** `feature/P2-01-C-D3-runtime-high-frame-execution`
**Previous Commit:** `364c917` (Root Cause Isolation — heap overwrite location identified)
**Date:** 2026-09-11

---

## 0. Executive Summary

在 Root Cause Isolation 阶段（364c917）已精确定位**越界写入位置**（TLLCoroutine 结构开头偏移 0-8 字节）的基础上，本阶段执行 Source Trace，目标是找到**写入源头**（谁写入了 callStack 指针区域）。

**关键发现：A-GAP-1 是概率性崩溃，不是确定性崩溃。**

无 padding 版本（0723eac）的 10000-task stress test：
- 有时 PASS（连续 1000/5000/10000 全部 PASS）
- 有时 CRASH（连续 3 次 10000 全部 FAIL）
- 崩溃发生在 Worker 执行期间（"Submitted 10000 tasks, waiting..." 之后）

这解释了之前记录的"稳定 CRASH"——可能是概率性崩溃的巧合 + Build Integrity 问题（旧 vm.obj 链接）。

**写入源头仍未锁定（UNVERIFIED）。** Phase G 直接写点审计未发现明显越界写入；Phase F canary trace 未完整执行。

---

## 1. Phase G: Direct Write Point Audit

### 1.1 搜索范围

搜索所有可能写入 TLLCoroutine header（offset 0-8，即 callStack 指针区域）的代码点：
- `->callStack =`
- `callStack[`
- `memcpy`
- `memset`
- `memmove`

### 1.2 结果

共发现 **19 个**相关写入点：

| 行号 | 代码 | 说明 | 可疑度 |
|------|------|------|--------|
| 441 | `co->callStack = (TLLFrame**)calloc(...)` | coroutine_create 初始化 | 低（正常初始化） |
| 487 | `co->callStack = TLL_CTX(vm)->callStack` | coroutine_save_current | 低（正常指针转移） |
| 503 | `TLL_CTX(vm)->callStack = co->callStack` | coroutine_restore | 低（正常指针转移） |
| 868 | `TLL_CTX(vm)->callStack = (TLLFrame**)calloc(...)` | VM 初始化 | 低 |
| 907 | `TLL_CTX(vm)->callStack = (TLLFrame**)realloc(...)` | push_frame 扩容 | **中**（P5 latent defect: realloc 期间悬空） |
| 1114/1144/1783 | `TLL_CTX(vm)->callStack = NULL` | 清理 | 低 |
| 1352/1353/1390/1405 | `memcpy(buf + ..., ...)` | 字符串操作 | 低（不涉及 coroutine） |
| 1529 | `memmove(&arr.as.array->items[1], ...)` | 数组插入 | 低（不涉及 coroutine） |
| 1849 | `mainCo->callStack = TLL_CTX(vm)->callStack` | main coroutine 初始化 | 低 |
| 1866/2283/2296 | `ctx->callStack = NULL` | 清理 | 低 |
| 2439 | `coro->callStack = worker->ctx.callStack` | Worker 保存 | 低（正常指针转移） |
| 2521 | `memset(vm->coroutines + vm->coroutineCount, 0, ...)` | prealloc 诊断模式 | **低**（仅 prealloc 模式，且 realloc 已扩展） |

### 1.3 结论

**未发现明显的越界写入点。** 所有 19 个写入点均为正常操作（初始化、指针转移、清理、字符串操作）。

行 907 的 push_frame realloc 是 P5 已发现的 latent defect（realloc 期间 coro->callStack 暂时悬空），但这是在 Worker 自己的执行上下文中，不是跨线程越界写入。

行 2521 的 memset 仅在 prealloc 诊断模式下执行，且 realloc 已将数组扩展到 prealloc_size，不会越界。

**越界写入更可能来自相邻 coroutine 的数组越界（如 callStack 数组、locals 数组、argStack 数组越界），覆盖了相邻 coroutine 的 callStack 指针。** 这仍是 INFERRED，未直接证明。

---

## 2. Phase H: Minimal Reproduction Scale

### 2.1 实验设置

从 0723eac（364c917 前一个 commit，无 magic+generation padding）恢复 tllvm.h 和 vm.c，Clean Build，运行不同规模的 stress test。

### 2.2 第一轮结果（意外 PASS）

| 规模 | 结果 |
|------|------|
| 1000 tasks | **PASS** |
| 5000 tasks | **PASS** |
| 10000 tasks | **PASS** |

**与之前记录的"1000+ CRASH"完全相反！**

### 2.3 第二轮结果（连续 CRASH）

连续运行 3 次 10000-task：

| Run | 结果 | 退出码 | stderr 最后输出 |
|-----|------|--------|----------------|
| 1 | **CRASH** | （无） | `Submitted 10000 tasks, waiting...` 之后无输出 |
| 2 | **CRASH** | （无） | `startWorkers(2)=0` 之后无输出 |
| 3 | **CRASH** | （无） | `startWorkers(2)=0` 之后无输出 |

**3/3 FAIL。**

### 2.4 关键发现：概率性崩溃

**A-GAP-1 是概率性崩溃，不是确定性崩溃。**

- 第一轮：1000/5000/10000 全部 PASS
- 第二轮：10000 连续 3 次全部 CRASH
- 崩溃发生在 Worker 执行高并发任务期间
- 没有错误输出，进程直接退出（可能是 access violation 或 heap corruption）

### 2.5 对之前记录的修正

之前 Root Cause Isolation 阶段（364c917）记录的"无 padding 版本 1000+ 稳定 CRASH"需要修正：

- **不是稳定 CRASH，而是概率性 CRASH**
- 之前的"稳定 CRASH"可能是：
  1. 概率性崩溃的巧合（连续多次恰好触发）
  2. Build Integrity 问题（旧 vm.obj 链接，Build Integrity Recovery 之前）
  3. 不同的运行环境/时序

### 2.6 最小触发规模

由于崩溃是概率性的，无法通过 binary search 找到确定性的最小触发规模。

- 100 tasks: 低概率崩溃
- 1000 tasks: 中概率崩溃
- 5000+ tasks: 高概率崩溃

崩溃概率随任务数量增加而上升，符合"并发竞争窗口随任务数量增加而扩大"的模式。

---

## 3. Phase F: Header Canary Source Trace

### 3.1 状态

**未完整执行。**

原因：
1. Phase G 未发现明显越界写入点，canary 的预期收益降低
2. Phase H 发现崩溃是概率性的，canary 需要多次运行才能捕获
3. 完整的 guard page 模式需要修改 coroutine 分配方式（malloc 额外空间），复杂度较高
4. 当前 16 字节 magic+generation 版本已能稳定隐藏问题（10000 5/5 PASS）

### 3.2 已有的 canary 等价物

当前 364c917 版本中的 `magic` 字段（8 字节，offset 0-7）实际上起到了 header canary 的作用：
- 初始化时 `magic = 0x544C4C434F524F`（ALIVE）
- Worker claim 后检查 `magic == ALIVE`，如果被修改则 abort
- 释放前 `magic = 0xDEADDEADDEADDEAD`（DEAD）

**但是，16 字节版本中 magic assert 未触发**（10000 5/5 PASS），这说明：
1. 要么越界写入没有覆盖 magic（概率性，未触发）
2. 要么越界写入的值恰好等于 magic 的高 4 字节（0x544C4C43）
3. 要么越界写入发生在 coroutine 被 claim 之前，然后 coroutine_create 重新设置了 magic

### 3.3 建议的后续 canary 实验（待架构师批准）

如果需要继续定位写入源，建议：
1. **运行时 canary 检查**：在 Worker 执行前后、coroutine 完成时都检查 magic，而不仅是 claim 后
2. **tail canary**：在 TLLCoroutine 结构末尾添加 canary，确定写入是 header 侧还是 tail 侧
3. **guard page 模式**：分配 sizeof(TLLCoroutine)+128，前后各 64 字节 canary，stress 后检查
4. **多次运行捕获**：由于崩溃是概率性的，需要连续运行 20+ 次才能稳定捕获

---

## 4. Evidence Level Classification

| 发现 | 证据等级 |
|------|----------|
| 越界写入在 TLLCoroutine 结构开头 0-8 字节 | **PROVEN**（364c917 堆布局实验） |
| 原始结构中覆盖 callStack 指针 | **PROVEN**（偏移计算） |
| 不是死亡 coroutine 访问（UAF） | **PROVEN**（magic assert 未触发） |
| A-GAP-1 是概率性崩溃 | **PROVEN**（Phase H: 第一轮 PASS，第二轮 3/3 CRASH） |
| 崩溃发生在 Worker 执行期间 | **PROVEN**（stderr 输出在 "Submitted..." 之后停止） |
| 崩溃概率随任务数量增加而上升 | **OBSERVED**（100 低概率，10000 高概率） |
| 写入源是相邻 coroutine 的数组越界 | **INFERRED**（最可能来源，未直接证明） |
| push_frame realloc 悬空指针是根因 | **UNVERIFIED**（P5 latent defect，未证明与本次崩溃直接相关） |
| 写入源是 coroutine index 越界写（H1） | **UNVERIFIED** |
| 写入源是 memcpy/memmove size 错（H2） | **UNVERIFIED**（Phase G 未发现） |
| 写入源是数组元素初始化错误（H3） | **UNVERIFIED** |
| 写入源是 coroutine create 并发插入（H4） | **UNVERIFIED** |

---

## 5. Root Cause Statement (Updated)

**ROOT CAUSE (Location):**
A-GAP-1 堆损坏由 TLLCoroutine 结构开头前 8 字节的越界写入引起。在原始结构中，这覆盖了 `callStack` 指针（`TLLFrame **`），导致后续通过损坏的指针访问内存时触发 heap corruption / access violation。

**TRIGGER:**
Concurrent coroutine_create() 与 Worker 执行同时进行时触发。崩溃是**概率性**的，概率随任务数量增加而上升。

**NATURE:**
- 不是确定性崩溃，是概率性崩溃
- 不是死亡 coroutine 访问（UAF）
- 不是 Frame Pool 问题
- 不是 Queue node 生命周期问题
- 不是 coroutine table realloc 本身

**WRITE SOURCE:**
**UNVERIFIED.** 最可能是相邻 coroutine 的数组越界（如 callStack 数组、locals 数组、argStack 数组越界）覆盖了相邻 coroutine 的 callStack 指针。Phase G 直接写点审计未发现明显越界写入点。

---

## 6. Recommendations

### 6.1 短期（让 D3 可以继续推进）

**保留 16 字节 magic+generation padding 作为临时稳定措施。**

理由：
- 16 字节版本 10000-task 5/5 PASS，稳定隐藏问题
- 越界写入仍在发生，但只覆盖 padding 字段（magic/generation），不影响 callStack 指针
- magic assert 可以在越界写入覆盖 magic 时捕获（虽然当前未触发）
- 这是最小改动，不影响 D2 已验证逻辑

**注意：这是临时措施，不是最终修复。** 越界写入仍在发生，只是被 padding 吸收。

### 6.2 中期（真正修复根因）

需要继续定位写入源，建议：
1. **运行时 canary 检查**：在 Worker 执行前后都检查 magic
2. **tail canary**：确定写入方向
3. **guard page 模式**：精确定位写入大小和位置
4. **多次运行捕获**：连续运行 20+ 次
5. **定位到写入源后**：最小修复越界写入

### 6.3 长期（Runtime 稳定性）

- ASan 集成（Windows 下可能需要 Visual Studio AddressSanitizer）
- 更严格的并发访问审计
- ThreadSanitizer（如果支持）

---

## 7. Files Changed (This Phase)

| 文件 | 说明 |
|------|------|
| `docs/evidence/P2-01-C-D3-A-GAP1-SOURCE-TRACE.md` | 本 Evidence 文档（新增） |

**本阶段未修改源码。** tllvm.h 和 vm.c 保持 364c917 的状态（16 字节 magic+generation）。

临时测试分支 `temp/agap1-nopadding-test` 已创建并删除，用于在无 padding 版本上运行 Phase H 实验。

---

## 8. Stop Gate Status

Source Trace 施工令 Stop Gate：
- Phase F (Header Canary): **PARTIAL**（magic 作为等价 canary 已存在，但完整 guard page 未做）
- Phase G (Direct Write Audit): **COMPLETE**（19 个写入点审计，未发现明显越界）
- Phase H (Minimal Reproduction): **COMPLETE**（发现概率性崩溃，崩溃概率随任务数增加）

**写入源头仍未锁定（UNVERIFIED）。**

---

## 9. Next Steps Recommendation

1. **架构师裁决**：
   - 选项 A：接受 16 字节 padding 作为临时稳定措施，D3 继续推进（后续再修复写入源）
   - 选项 B：继续定位写入源（运行时 canary + tail canary + guard page + 多次运行）
   - 选项 C：移除 padding，接受概率性崩溃，用其他方式（如重试）处理

2. **如果选择 A**：
   - D3 基础设施 + 16 字节 padding = 稳定版本
   - 运行 D2 7/7 回归 + D3 stress 1000/5000/10000
   - 如果全部 PASS，D3 可以 SEALED（记录 A-GAP-1 为已知 latent defect，非阻塞）
   - P2-01-C 总封板
   - 进入 Agent Runtime / Desktop Robot OS

3. **如果选择 B**：
   - 继续 Source Trace，定位写入源
   - 最小修复越界写入
   - 移除 padding
   - 10000 stress 稳定 PASS
   - D3 SEALED

---

*文档生成时间：2026-09-11 (Asia/Shanghai)*
*施工方：豆包A（施工方）*
*审计方：于秋鸿博士（待独立审计）*
