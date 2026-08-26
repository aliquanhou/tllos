# Contributing to TLL OS

Thank you for your interest in contributing to TLL OS! This document outlines the process and guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/tllos.git`
3. Build the Native Launcher (requires a C compiler):
   ```bash
   cd host/c
   # MSVC
   cl /O2 /D_CRT_SECURE_NO_WARNINGS /Dalloca=_alloca /Fe:tllvm.exe main.c vm.c value.c json.c builtin.c
   # or gcc/clang
   gcc -O2 -o tllvm main.c vm.c value.c json.c builtin.c
   ```
4. Verify the bootstrap seed runs:
   ```bash
   tllvm ../../compiler/compiler.tllbc
   ```
5. Run existing tests:
   ```bash
   tllvm tests/acceptance/01_hello.tllbc
   ```

**TLL OS does not require Node.js, npm, TypeScript, or JavaScript.** The only external build dependency is a C compiler for the Stage-0 Native Launcher.

## Development Workflow

### Branching

- Create feature branches from `main`
- Use descriptive branch names: `feature/your-feature`, `fix/your-fix`

### Commit Messages

Use clear, descriptive commit messages:
```
<type>: <short description>

<optional longer description>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

### Testing

- All changes must include tests
- Run relevant tests via `tllvm tests/<path>/<test>.tllbc` before submitting
- For compiler changes, verify self-hosting: run `tllvm compiler/compiler.tllbc` and confirm the output bytecode matches the seed SHA256
- Do not modify existing tests to make them pass
- For Native VM changes, run ASAN builds to verify memory safety

### Code Style

- TLL files: follow existing style in `compiler/` and `runtime/`
- C files (host/c/): follow existing style, C99 compatible
- The Native Launcher in `host/c/` must only implement bytecode loading, opcode dispatch, and Host ABI. It must NOT implement TLL language semantics.

## Frozen Items (Do Not Modify)

The following are frozen at v1.1 and require a major version bump to change:

- Opcode contract 0-45 (especially 42-45: closure/upvalue/box)
- Closure semantics (UpvalueBox, shared box, isolation)
- Bytecode schema
- Builtin function indices 0-97
- Module import syntax

See `spec/` and `docs/architecture/language-core-freeze.md` for details.

## Pull Request Process

1. Ensure all relevant tests pass
2. Update documentation if needed
3. Create a Pull Request with a clear description
4. Link any related issues
5. Wait for review

## Reporting Issues

- Use GitHub Issues
- Include: TLL OS version, OS, C compiler used
- Include minimal reproduction steps
- For compiler bugs, include the source file and expected vs actual output
- For Native VM bugs, include the `.tllbc` file and any ASAN output

## Questions?

Open a discussion on GitHub or reach out via issues.
