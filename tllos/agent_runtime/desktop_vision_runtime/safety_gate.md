# TLL OS Vision Safety Gate

## Purpose

Safety rules for Vision Runtime.
Ensures only trusted observations enter Decision Layer.

---

## Safety Rules

### Rule 1: Confidence Threshold

- Minimum confidence: 0.5
- Objects below threshold are REJECTED
- Fake objects (confidence > 1.0) are REJECTED

### Rule 2: Frame Replay Defense

- Every frame must have valid SHA256 hash
- Modified frame → hash mismatch → REJECT
- Replay with correct hash only

### Rule 3: Object Tamper Defense

- objects.json must match frame_hash
- Tampered objects → hash mismatch → REJECT

### Rule 4: Evidence Binding

- Every object must have evidence_ref
- Every detection must be recorded in Audit Ledger
- No silent observations

### Rule 5: OCR Boundary

- If Tesseract engine missing → NOT_AVAILABLE
- No fake OCR claims
- OCR results must have confidence scores

### Rule 6: Temporal Consistency (P2-08.2)

- Frame sequence must have continuous timestamps
- Missing frames → sequence invalid
- Hash chain must be sequential

### Rule 7: Memory Integrity (P2-08.2)

- Memory can observe history only
- Memory cannot make action decisions
- Memory boundary: observe only

### Rule 8: Replay Verification (P2-08.2)

- Same frame → same hash → same objects
- Modified frame → different hash → REJECT
- Replay must be deterministic

---

## Rejection Rules

| Condition | Action |
|-----------|--------|
| confidence < 0.5 | REJECT |
| confidence > 1.0 | REJECT (fake) |
| frame hash mismatch | REJECT |
| objects.json tampered | REJECT |
| missing evidence_ref | REJECT |
| OCR NOT_AVAILABLE | SKIP OCR, continue vision |
| missing frame in sequence | REJECT sequence |
| memory action decision | REJECT |
| replay hash mismatch | REJECT |

---

*P2-08.2 Vision Safety Gate v1.1*
