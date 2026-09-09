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

/* Scheduler trace dump (defined in vm.c) */
extern void sched_trace_dump(void);

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

    /* Seed random number generator (TLL-017: xorshift seeded from CSPRNG in vm.c) */
    srand((unsigned int)time(NULL));
    /* TLL-013: allow disabling hard-exit on uncaught exception for long-running processes */
    if (getenv("TLL_NO_EXIT_ON_UNCAUGHT")) tll_exit_on_uncaught = 0;

    tll_vm_run(vm);

    /* Dump scheduler trace if enabled */
    sched_trace_dump();

    tll_vm_free(vm);
    /* TLL-027: free program and its resources */
    if (prog) {
        for (int fi = 0; fi < prog->functionCount; fi++) {
            if (prog->functions[fi].name) free(prog->functions[fi].name);
            if (prog->functions[fi].instructions) free(prog->functions[fi].instructions);
        }
        if (prog->functions) free(prog->functions);
        if (prog->constants) free(prog->constants);
        free(prog);
    }

    return tll_exit_code;
}
