# TLL OS AI Native Engineering Foundation (.tll-engine/)

> **This is NOT README.md for humans. This is the official engineering cognition layer for Agents, CI, and tools.**

TLL OS is a high frame rate programming language. The AI Native Engineering Foundation is the wing that enhances TLL, not the soul that replaces it.

This directory contains machine-readable engineering truth that any Agent (Claude, GPT, DeepSeek, Doubao, OpenClaw, or future TLL Agent) can query and verify.

## First Principle

> **TLL is a high frame rate programming language. AI Engineering Layer enhances TLL, does not replace it.**

All work must serve the language first. This foundation makes it easier for Agents to develop TLL, but does not become a standalone product.

## Directory Structure

```
.tll-engine/
├── identity/           # Identity and authorization system
│   ├── root.json       # Identity Root: trust model, identity levels, agent policy
│   └── agents.json     # Agent registry: registered AI Agents and human contributors
├── truth/              # Canonical engineering truth (machine-readable)
│   ├── architecture.json   # Architecture truth: layers, components, key principles
│   ├── language.json       # Language semantics truth: features, scope model, limitations
│   ├── runtime.json        # Runtime truth: components, invariants, platform support
│   └── capability.json     # Capability matrix: what TLL can/cannot do, with evidence
├── protocol/           # Engineering protocols (YAML, machine-readable)
│   ├── development.yaml    # Agent Development Protocol: 8-phase workflow, forbidden behaviors
│   ├── testing.yaml        # Testing Protocol: test categories, CI gates, platform notes
│   └── audit.yaml          # Audit Protocol: independent audit procedure, common findings
├── cognition/          # Engineering Cognition Graph (NOT a neural network)
│   ├── graph.json          # Cognition graph: nodes, edges, weights, query examples
│   ├── dependency.json     # Dependency graph: module/test/capability dependencies
│   └── decisions.json      # Decision log: key engineering decisions with rationale
├── evidence/           # Evidence records (provenance, hash, scope)
│   ├── ci/                 # CI run evidence
│   ├── benchmark/          # Performance benchmark evidence
│   └── audit/              # Independent audit evidence
└── version/            # Version management
    └── manifest.json       # Foundation version manifest: component versions, hash chain, next phases
```

## Core Concepts

### Truth is not README

README is for humans. `.tll-engine/` is for Agents, CI, and tools. Truth must be:
- **Machine-readable**: JSON/YAML, not prose
- **Versioned**: hash chain, parent_hash
- **Evidence-backed**: every claim has evidence
- **Scope-limited**: evidence proves what it proves, no overclaiming

### Agent can change, Truth cannot be casually changed

Models, Agents, and frameworks can be swapped. Truth, Protocol, Identity, Authority, Evidence, Verification, and World Model must remain consistent.

### No construction report = completion

An Agent's self-report of completion is NOT evidence. Completion requires:
1. CI pass (3 platforms)
2. Independent audit
3. Truth update

### Engineering Cognition Graph is NOT a neural network

It behaves like a neural network:
- Nodes = engineering facts
- Edges = engineering relations
- Weights = evidence/confidence/impact
- Time = history
- Feedback = CI

But the foundation is a **machine-verifiable engineering world model**, not a trained neural network. No model training, embeddings, RAG, or fine-tuning in current phases.

## Agent Development Protocol (8 phases)

Every Agent participating in TLL development must follow:

1. **Identity Verification** — Agent reads agents.json, confirms identity and permissions
2. **Truth Reading** — Agent reads current Truth before planning
3. **Plan Generation** — Agent creates plan with scope boundary and acceptance criteria
4. **Code Modification** — Agent modifies code within allowed scope only
5. **CI Execution** — Agent commits, pushes, waits for 3-platform CI
6. **Evidence Submission** — Agent submits evidence for all claims
7. **Cognition Graph Update** — Agent updates graph, dependencies, decisions
8. **Independent Verification** — Independent auditor verifies the work

### Forbidden Behaviors

- Modify code → write README → announce completion
- Skip/delete failing tests to make CI green
- Claim capability without evidence
- Modify Runtime/VM/Compiler without real bug evidence
- Expand scope beyond authorized boundary
- Self-verify own work
- Modify Truth or Protocol directly (Level 3 Agent)
- Use TCC build as verification evidence (UNVERIFIED)
- Claim production readiness for blockchain (NOT READY)
- Call Engineering Cognition Graph a "Neural Network"

## Capability Status

Current TLL capabilities (as of bootstrap):

| Category | Status |
|----------|--------|
| Language Core (Compiler, VM, Scope Semantics) | ✅ Ready |
| Runtime (Coroutine 100K, TCP, Long-Run 120s) | ✅ Ready |
| Cryptography (SHA-256, HMAC) | ✅ Ready |
| Cryptography (Ed25519, SHA-512, Secure Random) | ❌ Missing (P0-15.19) |
| Blockchain 4-Node Network | ✅ Ready |
| Blockchain Fault Injection (5 scenarios) | ✅ Ready |
| Blockchain Real Cryptography | ❌ Missing (HMAC simulation) |
| Blockchain Account State / Persistence / Reorg | ❌ Missing |
| AI Engineering Foundation | 🟡 Bootstrap (structure established, automation pending) |
| Production Readiness | ❌ NOT READY |

## Validation

Validate the `.tll-engine/` structure and schema:

```bash
# Linux/macOS
scripts/validate-tll-engine.sh

# Windows
powershell -ExecutionPolicy Bypass -File scripts\validate-tll-engine.ps1

# Strict mode (warnings = errors)
scripts/validate-tll-engine.sh --strict
```

Validation checks:
1. Directory structure completeness
2. Required files presence
3. JSON validity
4. Required fields in Truth files
5. Evidence schema completeness
6. Version Manifest consistency
7. Protocol YAML basic validity

## Next Phases

| Phase | Name | Description |
|-------|------|-------------|
| P0-15.19 | TLL Native Cryptographic Foundation | Ed25519, SHA-512, secure random, Identity primitives, blockchain signature upgrade |
| P0-16.1 | AI Foundation CI Enforcement | CI validation of .tll-engine/, protocol compliance checks, automated evidence collection |
| P0-16.2 | Engineering Cognition Query API | Query API: What/Why/Depends/Proves/Constrains/Changed/Safely change/Must verify |
| P0-17.0 | tllos.com Official Portal | Truth Browser, Agent Developer Center, Cognition Graph visualization |

> **Website comes AFTER foundation is established. Website shows results, foundation makes results.**

## Immutable Core Rules (P001-P010)

1. **P001**: No construction report = completion
2. **P002**: Truth is not README
3. **P003**: First audit, then construct
4. **P004**: Bug only, no Runtime modification without evidence
5. **P005**: No test standard lowering for CI green
6. **P006**: Capability claim requires evidence
7. **P007**: Scope boundary respected
8. **P008**: Independent audit before seal
9. **P009**: Three-platform CI required
10. **P010**: First Principle: TLL is a high frame rate programming language

---

*Foundation version: 0.1.0-bootstrap*
*Created: 2026-09-01*
*Status: Bootstrap phase — structure and schema established, full automation and population are future work.*
