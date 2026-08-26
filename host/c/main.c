/*
 * tllvm - TLL Native Launcher
 *
 * Usage: tllvm <file.tllbc>
 *
 * This is the Bootstrap/Host layer. It:
 *   1. Loads a .tllbc (JSON bytecode) file
 *   2. Creates a minimal VM to execute the bytecode
 *   3. Provides Host ABI (io, fs, etc.)
 *
 * It does NOT implement TLL language semantics.
 * The TLL VM (runtime/vm.tll) is the source of truth for language semantics.
 *
 * Architecture:
 *   tllvm (this) -> vm_run.tllbc -> TLL VM (vm.tll) -> user program
 */
#include "tllvm.h"
#include <time.h>

/* Process API globals (P0-2.2) */
int tll_argc = 0;
char **tll_argv = NULL;
int tll_exit_code = 0;
int tll_should_exit = 0;

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: tllvm <file.tllbc>\n");
        fprintf(stderr, "TLL Native Launcher v1.1.0 - Bootstrap/Host layer only\n");
        return 1;
    }

    /* Save command-line arguments for process.argv builtin */
    tll_argc = argc;
    tll_argv = argv;

    const char *filename = argv[1];
    TLLProgram *prog = tll_load_program(filename);
    if (!prog) {
        fprintf(stderr, "tllvm: failed to load %s\n", filename);
        return 1;
    }

    TLLVM *vm = tll_vm_create(prog);

    /* Seed random number generator */
    srand((unsigned int)time(NULL));

    tll_vm_run(vm);

    tll_vm_free(vm);
    /* Note: program and constants are intentionally not freed to avoid
     * double-free issues with shared constant references. In a long-running
     * process this would need proper ownership tracking. */

    return tll_exit_code;
}
