# TLL Language Scope Semantics

## TLL Scope Model

TLL uses a **function-level scope model**, not block-level scope.

```
Global Scope
    ↓
Function Scope
    ↓
Nested Function / Closure Scope
    ↓
Coroutine Scope
```

**There is NO block scope**: `if`, `while`, `for` do NOT create a new lexical scope. Variables declared inside these blocks are function-scoped.

---

## 1. Global Scope

Variables declared at the top level (outside any function) are **global variables**.

```tll
let x = 10  // global variable

fn getX() -> int {
    return x  // reads global x
}

fn setX(val: int) -> void {
    x = val   // modifies global x
}
```

Global variables are accessible from all functions defined in the same module.

---

## 2. Function Scope

Variables declared inside a function with `let` or `const` are **local to that function**. They do NOT affect global variables or variables in other functions.

```tll
let x = 10  // global

fn test() -> int {
    let x = 20  // local to test(), does NOT affect global x
    return x    // returns 20
}

// After calling test():
// global x is still 10
```

### Same-named local and global

When a function declares a local variable with the same name as a global variable, the local variable **shadows** the global within that function. The global variable is unaffected.

```tll
let i = 0  // global

fn worker() -> void {
    let i = 42  // local, shadows global i
    // i is 42 here
}

worker()
// global i is still 0
```

**This was the root cause of P0-15.18.4-RUNTIME.3 bug**: before the fix, `let i` inside a function incorrectly generated `OP_STORE_GLOBAL`, overwriting the global variable. The fix ensures non-main function `let`/`const` generates `OP_STORE_VAR` (local).

---

## 3. Function Parameters

Function parameters are **local variables** scoped to the function. Modifying a parameter does not affect the caller's variable.

```tll
fn modify(x: int) -> int {
    x = x + 10  // modifies local parameter, not caller's variable
    return x
}

let original = 5
let result = modify(original)
// original is still 5
// result is 15
```

Parameters can shadow global variables:

```tll
let x = 100  // global

fn test(x: int) -> int {
    // x is the parameter, shadows global x
    return x
}

test(42)  // returns 42
```

---

## 4. Nested Function Scope

Nested functions can access variables from all enclosing function scopes.

```tll
fn outer() -> int {
    let x = 10  // outer's local

    fn inner() -> int {
        let y = 20  // inner's local
        return x + y  // x from outer, y from inner
    }

    return inner()  // returns 30
}
```

Nested functions have their own local scope. Variables declared in a nested function do NOT affect the enclosing function's variables:

```tll
fn outer() -> list {
    let x = 10

    fn inner() -> int {
        let x = 20  // inner's local, does NOT affect outer's x
        return x
    }

    return [x, inner()]  // [10, 20]
}
```

---

## 5. Closure Scope (Upvalues)

Closures capture variables from their enclosing scope by reference. Modifying a captured variable inside a closure affects the original variable.

```tll
fn makeCounter() -> any {
    let count = 0

    fn increment() -> int {
        count = count + 1  // modifies captured upvalue
        return count
    }

    return increment
}

let counter = makeCounter()
counter()  // returns 1
counter()  // returns 2
counter()  // returns 3
```

Each closure instance has its own set of upvalues:

```tll
let c1 = makeCounter()
let c2 = makeCounter()
c1()  // 1
c1()  // 2
c2()  // 1 (independent upvalue)
```

---

## 6. NO Block Scope (Important!)

TLL does **NOT** have block-level scope. Variables declared inside `if`, `while`, or `for` blocks are **function-scoped**, not block-scoped.

```tll
fn test() -> int {
    let x = 10

    if true {
        let x = 20  // This is function-scoped, NOT block-scoped!
        // It modifies the function's x, not a new block-local x
    }

    return x  // returns 20, NOT 10!
}
```

### While loop example

```tll
fn test() -> list {
    let x = 10
    let results: list = []
    let i = 0

    while i < 3 {
        let x = i * 100  // function-scoped, modifies outer x
        arrays.push(results, x)
        i = i + 1
    }

    arrays.push(results, x)  // x is 200 (last loop value), NOT 10
    return results  // [0, 100, 200, 200]
}
```

### Why no block scope?

TLL's current compiler (`codegen.tll`) uses a flat local variable slot allocation per function. Block-level scope would require tracking variable lifetimes across blocks and potentially reusing slots, which adds complexity to the compiler.

This is a **deliberate language design choice** for the current phase of TLL. It may be revisited in a future version.

---

## 7. Coroutine Scope

Coroutines run in their own execution context but share the same variable scope rules as functions.

- Local variables in a coroutine are isolated from other coroutines.
- Coroutines can access and modify global variables and captured upvalues.
- Coroutine parameters are local to that coroutine instance.

```tll
let shared = 0

fn worker(id: int) -> void {
    let local = id * 10  // local to this coroutine instance
    coroutine.sleep(10)
    // local is still id*10, not corrupted by other coroutines
    shared = shared + 1  // modifies global
}

coroutine.spawn(worker, 1)
coroutine.spawn(worker, 2)
coroutine.spawn(worker, 3)
coroutine.sleep(100)
// shared is 3
```

---

## 8. Return Value Lifetime

Objects (maps, lists, structs) returned from a function **survive** the function's scope. They are managed by the VM's reference counting / garbage collection.

```tll
fn makeObject() -> map {
    let local = { value: 42, name: "test" }
    return local
}  // local goes out of scope, but the returned object survives

let obj = makeObject()
obj.value  // 42 - object is still valid
```

Nested objects also survive:

```tll
fn makeNested() -> map {
    let inner = { a: 1, b: 2 }
    let outer = { nested: inner, count: 2 }
    return outer
}

let result = makeNested()
result.nested.a  // 1
```

---

## 9. Recursion and Frame Isolation

Each recursive function call gets its own stack frame with independent local variables.

```tll
fn factorial(n: int) -> int {
    let x = n  // local to this frame
    if n <= 1 {
        return 1
    }
    let result = x * factorial(n - 1)
    // x is still n after recursive call (frame isolation)
    return result
}

factorial(5)  // 120
```

Mutual recursion also has frame isolation:

```tll
fn isEven(n: int) -> bool {
    let x = n
    if n == 0 { return true }
    return isOdd(x - 1)
}

fn isOdd(n: int) -> bool {
    let x = n
    if n == 0 { return false }
    return isEven(x - 1)
}
```

---

## 10. Scope Semantics Test Suite

The scope semantics are verified by 10 tests in `tests/scope/`:

| Test | Coverage |
|------|----------|
| `scope_01_global_local.tll` | Global vs function-local same-named variables |
| `scope_02_shadowing.tll` | Function-level variable shadowing, nested functions |
| `scope_03_params.tll` | Function parameter isolation and shadowing |
| `scope_04_nested_fn.tll` | Nested function access to all outer scopes |
| `scope_05_closure.tll` | Closure capture, upvalue modification, independence |
| `scope_06_block.tll` | Function-level block scope (if/while), no block scope |
| `scope_07_coroutine.tll` | Coroutine local isolation, params, shared globals |
| `scope_08_multi_fn_recursion.tll` | Multi-function same-named locals, recursion, mutual recursion |
| `scope_09_return_lifetime.tll` | Return value lifetime, nested objects, chained calls |
| `scope_10_complete_chain.tll` | Complete scope chain: global→function→nested→closure→coroutine |

These tests are automatically run by `scripts/run-tests.sh` and `scripts/run-tests.bat`, and are part of the CI pipeline.

---

## Summary

| Scope Type | Exists in TLL? | Notes |
|-----------|----------------|-------|
| Global | ✅ Yes | Top-level `let`/`const` |
| Function | ✅ Yes | `let`/`const` inside function |
| Function parameters | ✅ Yes | Local to function |
| Nested function | ✅ Yes | Accesses all enclosing scopes |
| Closure / Upvalue | ✅ Yes | Captured by reference |
| Coroutine | ✅ Yes | Own execution context, same scope rules |
| **Block (if/while/for)** | **❌ No** | Variables are function-scoped |

**Key takeaway**: TLL has function-level scope, not block-level scope. Variables declared inside `if`/`while`/`for` are visible throughout the entire function, not just the block.
