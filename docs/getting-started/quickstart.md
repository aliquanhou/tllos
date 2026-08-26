# Getting Started with TLL OS

## Prerequisites

TLL OS requires only a C compiler to build the Stage-0 Native Launcher. No Node.js, npm, TypeScript, or JavaScript is needed.

Supported C compilers: MSVC, GCC, Clang, TCC.

## Installation

```bash
git clone https://github.com/aliquanhou/tllos.git
cd tllos
```

## Build the Native Launcher

### Windows (MSVC)

```bash
cd host/c
cl /O2 /D_CRT_SECURE_NO_WARNINGS /Dalloca=_alloca /Fe:tllvm.exe main.c vm.c value.c json.c builtin.c
```

### Linux/macOS

```bash
cd host/c
gcc -O2 -o tllvm main.c vm.c value.c json.c builtin.c
```

## Run Your First Program

TLL programs are compiled to `.tllbc` bytecode, then executed by the Native Launcher.

Run an existing example:

```bash
tllvm ../../tests/acceptance/01_hello.tllbc
# Output: Hello, TLL!
```

## Your First TLL Program

Create `hello.tll`:

```tll
fn main() {
    io.println("Hello, TLL OS!")
}
```

To compile and run, use the TLL compiler seed (`compiler/compiler.tllbc`) to compile your source, then execute the resulting bytecode with `tllvm`.

## Language Basics

### Variables

```tll
let x = 42
const name = "TLL"
```

### Functions

```tll
fn add(a, b) {
    return a + b
}

let result = add(3, 4)  // 7
```

### Closures

```tll
fn makeAdder(x) {
    fn add(y) {
        return x + y
    }
    return add
}

let add5 = makeAdder(5)
io.println(add5(10))  // 15
```

### Modules

```tll
// math.tll
export fn square(x) {
    return x * x
}

// main.tll
from "./math" import square
io.println(square(5))  // 25
```

### Control Flow

```tll
if x > 10 {
    io.println("big")
} else {
    io.println("small")
}

let i = 0
while i < 5 {
    io.println(i)
    i = i + 1
}
```

### Exceptions

```tll
try {
    throw "something went wrong"
} catch e {
    io.println("caught: " + e)
}
```

## Native Self-Hosting

TLL OS can compile itself. The repository includes a compiler seed (`compiler/compiler.tllbc`):

```bash
# The seed compiler compiles compiler.tll
tllvm compiler/compiler.tllbc
# Output: compiler_self_compiled.tllbc

# The new compiler compiles compiler.tll again
tllvm compiler_self_compiled.tllbc

# Both generations produce identical bytecode (SHA256 match)
```

Deterministic bootstrap SHA256:
`7D45DC155804854EE08263E0A61D956FA28CC03E49B9140D4004C200A4624315`

## Architecture

```
C Compiler (Stage-0)
    ↓
tllvm (Native Launcher)
    ↓
compiler.tllbc (Bootstrap Seed)
    ↓
TLL Compiler (pure TLL)
    ↓
user.tll → user.tllbc
    ↓
tllvm → execution
```

The C Native Launcher only loads bytecode, dispatches opcodes, and provides Host ABI (stdout, filesystem, etc.). All TLL language semantics — lexer, parser, typechecker, codegen, closure, module — are implemented in TLL itself.

## Next Steps

- Read the [Language Specification](../../spec/LANGUAGE.md)
- Read the [Architecture Document](../../ARCHITECTURE.md)
- Explore [examples](../../examples/)
- See [OPCODES.md](../../spec/OPCODES.md) for bytecode reference
- See [VALUE_MODEL.md](../../spec/VALUE_MODEL.md) for value and ownership semantics
