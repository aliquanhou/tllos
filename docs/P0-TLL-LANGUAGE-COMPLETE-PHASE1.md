# P0-TLL-LANGUAGE-COMPLETE: Language Richness Expansion

## Phase 1: Core Language Capabilities (Tuple → Destructuring → Generic → ADT)

### Status: IMPLEMENTED + VERIFIED (LOCAL)

---

## 1. Tuple Type

**Commit**: `f231286`

**Syntax**:
```tll
let p = (10, 20)
io.println(p.0)  // 10
io.println(p.1)  // 20

fn getPoint() { return (30, 40) }
let mixed = (1, "hello", true)  // mixed types
```

**Implementation**:
- Parser: `parsePrimary` LPAREN handling — comma-separated expressions → Tuple node
- Codegen: Tuple reuses `cg_compileArray` (underlying array representation)
- Numeric member access: `p.0` → `arrays.get(p, 0)`

**Tests**:
- Basic tuple creation: PASS
- Numeric index access: PASS
- Mixed types: PASS
- Function return tuple: PASS

**Known Limitations**:
- Chained numeric access `obj.0.1` parsed as float `0.1`; use `(obj.0).1`
- DEFERRED, non-blocking

---

## 2. Destructuring Assignment

**Commit**: `4406ed9`

**Syntax**:
```tll
let (x, y) = (10, 20)          // x=10, y=20
let (a, b, c) = getValues()    // from function return
let (first, second) = [1, 2]   // from array
```

**Implementation**:
- Parser: `parseLetStatement` — detect `let (names) = value` pattern
- AST: Let node with `names` array and `isDestructuring=true` flag
- Codegen: compile RHS to tuple/array, then iterate elements with `OP_INDEX_GET` + `OP_STORE_VAR`

**Tests**:
- Basic tuple destructuring: PASS
- Mixed types: PASS
- Function return destructuring: PASS
- Array destructuring: PASS

**Combination**: Generic + Tuple + Destructuring all work together.

---

## 3. Generic / Parametric Types

**Commit**: `f834d66`

**Syntax**:
```tll
fn identity<T>(x: T) -> T { return x }
let a = identity<int>(10)
let b = identity<string>("hello")

fn pair<T, U>(x: T, y: U) { return (x, y) }
let p = pair<int, string>(1, "one")

fn first<T>(arr: List<T>) -> T { return arr[0] }
```

**Implementation**:
- Parser: 
  - `parseFnDeclaration` — optional `<T, U>` after function name
  - `parsePostfix` Call handling — lookahead for `<Type>` before `(`
  - `parsePrimaryType` — `List<T>`, `Map<K,V>` generic type annotations
- Codegen: Type parameters stored in AST; runtime uses type erasure (dynamic typing)
- No VM/runtime changes needed

**Tests**:
- `identity<int>(10)` = 10: PASS
- `identity<string>("hello")` = hello: PASS
- `identity(3.14)` (no type args): PASS
- `pair<int, string>` multi-type: PASS
- Generic + Tuple + Destructuring: PASS
- `List<T>` type annotation: PASS

**Strategy**: Type Erasure — generics are compile-time syntax, runtime remains dynamically typed. This is the minimal viable implementation.

**Known Limitations** (DEFERRED):
- Generic constraints / trait bounds
- Higher-kinded types
- Variance (covariance/contravariance)
- Monomorphization optimization
- Complex type inference

---

## 4. ADT / Algebraic Data Types (Enum Enhancement)

**Commit**: `35fdfc9`

**Syntax**:
```tll
// Simple enum (backward compatible)
enum Color { Red, Green, Blue }

// Generic enum with payload
enum Result<T> {
    Ok(T),
    Err(string)
}

// Multi-payload variant
enum Shape {
    Circle(float),
    Rectangle(float, float)
}

let r = Result.Ok(42)
// r = { tag: "Ok", value: 42, __enum: "Result" }
```

**Implementation**:
- Parser: `parseEnumDeclaration` — generic params `<T>`, payload `(Type, Type)` in variants
- Codegen:
  - Enum collection stores `{ value, hasPayload, payloadCount }` per variant (TWO collection points unified)
  - Member access: no-payload → integer constant; with-payload → marker string `"Enum.Variant"`
  - Call handling: detect ADT constructor `Enum.Variant(args)` → generate `OP_MAKE_MAP` with `{tag, value, __enum}`
- ADT representation: `{ tag: "VariantName", value: payload, __enum: "EnumName" }`
  - Single payload: `value` is direct data
  - Multi payload: `value` is array

**Bug Found & Fixed**:
- `cg_enumMap` had TWO collection points (line 462 and 548). First was updated to new format, second remained old format → all enum values returned null. Fixed by unifying both.

**Tests**:
- Simple enum `Color.Red` = 0: PASS
- `Result.Ok(42)` tag/value/__enum: PASS
- `Result.Err("msg")`: PASS
- `Shape.Circle(3.14)` single payload: PASS
- `Shape.Rectangle(10, 20)` multi payload: PASS
- ADT + match combination: PASS

**Known Limitations** (DEFERRED):
- Pattern matching on ADT payload (`match Result.Ok(x) => ...` direct binding)
- Enum variant as function parameter type constraint
- Recursive ADT (`enum List<T> { Nil, Cons(T, List<T>) }`)
- ADT equality comparison

---

## Regression Results (Local)

| Probe | Result |
|-------|--------|
| P0-01 Function Capability | ALL PASSED |
| P0-02 Control Flow | 1 known failure (for-string, DEFERRED) |
| P0-03 Data & Type | ALL PASSED |
| P0-05 Error / Resource | ALL PASSED |
| P0-06 Async / Concurrency | 19/19 PASSED |
| New Language Capabilities | ALL PASSED |

## Persistent Regression Test

- `tests/compiler/probe_language_capabilities.tll` — covers Generic + ADT + Tuple + Destructuring combinations

## CI Status

- PENDING: push will trigger GitHub Actions (Ubuntu / Windows / macOS)

## Working Tree

- CLEAN after commit

---

## Next Phase Candidates

Per ladder: Interface / Trait / Protocol → Error/Resource Enhancement → Module/Package → Concurrency → FFI

Decision: pending architect review.
