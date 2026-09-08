# TLL Stdlib Namespace Audit Report

**Baseline**: main @ 5ff603f
**Date**: 2026-09-08
**Scope**: stdlib flat modules vs subdirectory modules
**Status**: AUDIT ONLY — no moves, no deletes, no refactoring

---

## Executive Summary

The stdlib directory contains **two distinct semantic layers** that share namespace names. This is NOT a case of duplicate wheels. It is a case of **legacy runtime modules** and **P0-15.21 Agent Identity Protocol Stack** coexisting under the same namespace names.

| Namespace | Legacy Flat Module | New Subdirectory Module | Relationship |
|-----------|-------------------|------------------------|-------------|
| `agent` | agent.tll (15KB) | agent/agent_ecosystem.tll (20KB) | Different layers |
| `capability` | capability.tll (3KB) | capability/capability.tll (14KB) | Different layers |
| `crypto` | crypto.tll (16KB) | crypto/ (4 files, 36KB) | Different algorithms |
| `identity` | — (no flat) | identity/identity.tll (11KB) | Canonical |
| `authority` | — (no flat) | authority/authority.tll (14KB) | Canonical |
| `evidence` | — (no flat) | evidence/evidence.tll (16KB) | Canonical |
| `trust` | — (no flat) | trust/trust.tll (20KB) | Canonical |

---

## Layer 1: Legacy Runtime Modules (Flat)

### agent.tll (15,459 bytes)
**Role**: Agent Runtime — runtime management of agent lifecycles
**APIs** (38 functions):
- Runtime: `agent_createRuntime`, `agent_generateId`, `agent_create`, `agent_get`, `agent_list`
- Lifecycle: `agent_start`, `agent_stop`, `agent_pause`, `agent_resume`, `agent_status`, `agent_destroy`
- Messaging: `agent_send`, `agent_recv`, `agent_tryRecv`, `agent_reply`, `agent_broadcast`
- State: `agent_stateGet`, `agent_stateSet`, `agent_stateDelete`, `agent_stateExists`, `agent_stateKeys`
- Capabilities (simple string-based): `agent_hasCapability`, `agent_requireCapability`, `agent_grantCapability`, `agent_revokeCapability`, `agent_listCapabilities`
- Tools: `agent_toolCall`, `agent_registerTool`
- Events: `agent_onEvent`, `agent_awaitEvent`, `agent_emitEvent`
- Supervisor: `supervisor_create`, `supervisor_monitor`, `supervisor_unmonitor`
- Context: `agent_context`

**Semantic Layer**: Runtime execution environment for agents.

### capability.tll (3,145 bytes)
**Role**: Simple string-based permission set
**APIs** (10 functions):
- `capability_create`, `capability_with`, `capability_has`, `capability_require`
- `capability_grant`, `capability_revoke`, `capability_list`
- `capability_hasAny`, `capability_hasAll`, `capability_merge`

**Semantic Layer**: Simple runtime permission checking (string names only, no IDs, no signatures).

### crypto.tll (16,061 bytes)
**Role**: Hash algorithms (SHA-256, SHA-512, HMAC)
**APIs** (20+ functions):
- SHA-256: `sha256`, `sha256Bytes`, `sha256_core`, `sha256_pad_bytes`
- SHA-512: `sha512`, `sha512Bytes`, `sha512_core`, `sha512_pad_bytes`
- HMAC: `hmacSha256`
- Utilities: `rotr`, `shr64`, `rotr64`, `hexCharVal`, `hexToBytes`, `constantTimeEquals`

**Semantic Layer**: Cryptographic hash functions (no public-key crypto).

---

## Layer 2: P0-15.21 Agent Identity Protocol Stack (Subdirectories)

This is a coherent protocol stack introduced in P0-15.21, with clear dependency relationships.

### Dependency Graph
```
identity/identity.tll
    ↑
capability/capability.tll
    ↑
authority/authority.tll
    ↑
evidence/evidence.tll
    ↑
trust/trust.tll
    ↑
agent/agent_ecosystem.tll
```

### identity/identity.tll (10,929 bytes)
**Role**: Identity Primitive — Ed25519-based digital identity
**APIs** (15 functions):
- `identity_generate`, `identity_from_public_key`, `identity_validate`
- `identity_sign`, `identity_verify`
- `identity_encode`, `identity_decode`, `identity_equals`
- `identity_build_canonical_material`, `identity_compute_id`
- Constants: `IDENTITY_VERSION`, `IDENTITY_ALGORITHM` ("Ed25519"), `IDENTITY_PUBLIC_KEY_SIZE` (32), `IDENTITY_AGENT_ID_SIZE` (32), `IDENTITY_PRIVATE_KEY_SIZE` (64)

**Key characteristic**: 32-byte identity IDs, canonical material hashing, Ed25519 signatures.

### capability/capability.tll (14,317 bytes)
**Role**: Capability Primitive — cryptographically identifiable capability definitions
**APIs** (20 functions):
- `capability_create`, `capability_validate`, `capability_encode`, `capability_decode`, `capability_equals`
- `capability_build_canonical_material`, `capability_compute_id`
- Capability sets: `capability_set_create`, `capability_set_contains`, `capability_set_add`, `capability_set_remove`, `capability_set_sort`, `capability_set_encode`, `capability_set_decode`
- Constants: `CAPABILITY_VERSION`, `CAPABILITY_ID_SIZE` (32)

**Key characteristic**: 32-byte capability IDs derived from canonical material (name + description + parameters), deterministic encoding of capability sets.

### authority/authority.tll (13,549 bytes)
**Role**: Authority Primitive — signed capability grants with expiry
**APIs** (14 functions):
- `authority_create`, `authority_validate`, `authority_is_expired`, `authority_verify_signature`
- `authority_encode`, `authority_decode`, `authority_equals`
- `authority_build_canonical_material`, `authority_compute_id`
- Constants: `AUTHORITY_VERSION`, `AUTHORITY_ID_SIZE` (32), `AUTHORITY_SIGNATURE_SIZE` (64)

**Key characteristic**: Binds agent_id + capability_id + constraints + issuer + expiry, signed by issuer's private key.

### evidence/evidence.tll (15,748 bytes)
**Role**: Evidence Primitive — tamper-evident action records with chaining
**APIs** (14 functions):
- `evidence_create`, `evidence_validate`, `evidence_verify_signature`, `evidence_chain_verify`
- `evidence_encode`, `evidence_decode`, `evidence_equals`
- `evidence_build_canonical_material`, `evidence_compute_id`
- Constants: `EVIDENCE_VERSION`, `EVIDENCE_ID_SIZE` (32), `EVIDENCE_HASH_SIZE` (32), `EVIDENCE_SIGNATURE_SIZE` (64)

**Key characteristic**: Records agent actions with input/output hashes, timestamps, and previous_evidence_id for chain verification.

### trust/trust.tll (20,060 bytes)
**Role**: Trust Evaluation — combines identity/capability/authority/evidence into trust decisions
**APIs** (14 functions + 11 reason constants):
- `trust_evaluate`, `trust_validate`, `trust_verify_signature`
- `trust_encode`, `trust_decode`, `trust_equals`
- `trust_build_canonical_material`, `trust_compute_id`
- Reason constants: `REASON_ALL_VALID`, `REASON_IDENTITY_INVALID`, `REASON_CAPABILITY_INVALID`, `REASON_AUTHORITY_INVALID`, `REASON_AUTHORITY_EXPIRED`, `REASON_AGENT_MISMATCH`, `REASON_CAPABILITY_MISMATCH`, `REASON_EVIDENCE_INVALID`, `REASON_EVIDENCE_MISSING`, `REASON_EVIDENCE_SIGNATURE_INVALID`, `REASON_EVIDENCE_CHAIN_BROKEN`

**Key characteristic**: Top-level evaluation that validates the entire chain (identity → capability → authority → evidence) and produces a trust score with reasons.

### agent/agent_ecosystem.tll (20,240 bytes)
**Role**: Agent Profile & Discovery — combines all primitives into agent profiles
**APIs** (20 functions):
- Profile: `agent_profile_create`, `agent_profile_build_canonical`, `agent_profile_validate`, `agent_profile_verify_signature`
- Encoding: `agent_profile_encode`, `agent_profile_decode`, `agent_profile_equals`
- Query: `agent_profile_find_capability`, `agent_profile_has_capability`, `agent_profile_check_authority`, `agent_profile_verify_evidence`, `agent_profile_evaluate_trust`
- Discovery: `agent_discovery_create_registry`, `agent_discovery_register`, `agent_discovery_unregister`, `agent_discovery_find_by_capability`, `agent_discovery_find_by_id`, `agent_discovery_list_capabilities`
- Protocol constants: `AGENT_PROTOCOL_VERSION` (1), `AGENT_PROFILE_MAGIC` ("TLLAP"), `AGENT_PROFILE_MAGIC_BYTES`

**Imports**: identity, capability, authority, evidence, trust (the entire stack)

### crypto/ (4 files, 35,976 bytes total)
**Role**: Ed25519 public-key signature implementation
**Files**:
- `ed25519_field.tll` (15,886 bytes): Field arithmetic (fe_* functions)
- `ed25519_curve.tll` (7,238 bytes): Curve/point operations (point_* functions)
- `ed25519_scalar.tll` (4,917 bytes): Scalar arithmetic (scalar_* functions)
- `ed25519.tll` (7,935 bytes): High-level API (generate_keypair, sign, verify, generate_random_keypair)

**Dependency**: ed25519.tll → ed25519_curve.tll → (field + scalar)

---

## Import Relationships

### Internal (stdlib → stdlib)
```
agent/agent_ecosystem.tll → identity, capability, authority, evidence, trust
trust/trust.tll → identity, capability, authority, evidence
crypto/ed25519.tll → crypto/ed25519_curve.tll
```

### External (tests → stdlib)
All P0-15.21 protocol tests import from **subdirectory modules**:
- `tests/agent/test_agent_ecosystem_gates.tll` → identity/, capability/, authority/, evidence/
- `tests/capability/test_capability_gates.tll` → capability/capability
- `tests/identity/test_identity_gates.tll` → identity/identity
- `tests/authority/test_authority_gates.tll` → identity/, capability/, authority/
- `tests/evidence/test_evidence_gates.tll` → identity/, capability/, evidence/
- `tests/trust/test_trust_gates.tll` → identity/, capability/, authority/, evidence/, trust/
- `tests/crypto/test_ed25519_curve_math.tll` → crypto/ed25519_curve

**No tests import from legacy flat modules** (agent.tll, capability.tll, crypto.tll) for the P0-15.21 protocol features.

---

## Code Duplication Within New Stack

The following utility functions are duplicated across multiple subdirectory modules:

| Function | identity | capability | authority | evidence | trust | agent/ |
|----------|----------|------------|-----------|----------|-------|--------|
| `uint32_to_bytes_be` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `bytes_to_uint32_be` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `string_to_bytes` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `bytes_to_string` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `bytes_append` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `bytes_equal` | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ascii_lookup` | — | ✅ | ✅ | ✅ | ✅ | — |
| `uint64_to_bytes_be` | — | — | ✅ | ✅ | ✅ | — |
| `copy_bytes` | — | — | — | ✅ | ✅ | ✅ |

**This is a real code quality issue**, but it is consistent across the protocol stack and does not affect correctness. A future `stdlib/encoding/bytes.tll` shared module could consolidate these.

---

## Canonical Namespace Recommendations

### Already Canonical (no conflict)
- `identity/` — Identity Primitive (no flat module)
- `authority/` — Authority Primitive (no flat module)
- `evidence/` — Evidence Primitive (no flat module)
- `trust/` — Trust Evaluation (no flat module)

### Namespace Conflict (needs resolution strategy)

| Namespace | Recommendation | Rationale |
|-----------|---------------|-----------|
| `crypto/` | **Canonical crypto namespace** | Contains ed25519 (public-key), future home for all crypto |
| `crypto.tll` | **Rename to `hash.tll` or move to `crypto/hash.tll`** | Contains only SHA-256/SHA-512/HMAC (hash algorithms), not general crypto |
| `capability/` | **Canonical capability namespace** | P0-15.21 Capability Primitive with IDs, signatures, deterministic encoding |
| `capability.tll` | **Rename to `permissions.tll`** | Simple string-based runtime permission set, different semantic layer |
| `agent/` | **Canonical agent namespace** | P0-15.21 Agent Profile/Ecosystem with full identity protocol |
| `agent.tll` | **Rename to `agent_runtime.tll` or move to `agent/runtime.tll`** | Runtime execution/lifecycle management, different from identity protocol |

### Compatibility Strategy
1. **Do not delete** legacy modules — they may be used by existing code
2. **Rename** legacy modules to disambiguate (e.g., `crypto.tll` → `hash.tll`)
3. **Add deprecation notices** in legacy module headers
4. **Update imports** in any code that still uses legacy modules
5. **Consolidate** byte utility functions into `stdlib/encoding/bytes.tll`

---

## GAPs Identified

1. **Namespace collision**: 3 namespaces (agent, capability, crypto) have both flat and subdirectory modules with different semantics
2. **Code duplication**: 8+ byte utility functions duplicated across 6+ modules
3. **No shared encoding module**: `stdlib/encoding/` does not exist
4. **Legacy module usage unknown**: Need to audit whether agent.tll, capability.tll, crypto.tll are still imported anywhere
5. **No deprecation mechanism**: TLL has no formal `@deprecated` annotation

---

## Conclusion

The stdlib namespace situation is **NOT a case of duplicate wheels**. It is a case of **two coherent architectural layers** sharing namespace names:

- **Layer 1 (Legacy)**: Runtime-oriented modules (agent runtime, simple permissions, hash utilities)
- **Layer 2 (P0-15.21)**: Agent Identity Protocol Stack (identity → capability → authority → evidence → trust → agent profile)

Both layers are real, functional, and tested. The conflict is purely **naming**, not implementation duplication.

**Recommended next step**: Rename legacy flat modules to disambiguate (crypto.tll → hash.tll, capability.tll → permissions.tll, agent.tll → agent_runtime.tll), then consolidate byte utilities into a shared encoding module. This should be done as a dedicated refactoring phase with full test coverage, NOT as part of tree cleanup.

---

**Audit Status**: COMPLETE
**Actions taken**: NONE (audit only)
**Files modified**: NONE
**Recommendations**: See Canonical Namespace Recommendations above
