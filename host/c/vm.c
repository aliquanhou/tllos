/* TLL Bootstrap VM - executes bytecode opcodes.
 * This is the Host/Bootstrap layer. Language semantics live in runtime/vm.tll.
 */
#include "tllvm.h"
#ifdef _WIN32
#include <malloc.h>  /* MSVC alloca */
/* winsock2.h not available in TCC; manual declarations below */
#include <windows.h>   /* FILETIME, ULARGE_INTEGER, Sleep, DWORD for unified scheduler timer */
/* Minimal Winsock select declarations (TCC lacks winsock2.h) */
typedef UINT_PTR SOCKET;
#define FD_SETSIZE 64
typedef struct fd_set { unsigned int fd_count; SOCKET fd_array[FD_SETSIZE]; } fd_set;
#define FD_ZERO(s) ((s)->fd_count = 0)
#define FD_SET(fd,s) ((s)->fd_array[(s)->fd_count++] = (SOCKET)(fd))
static int fd_isset(SOCKET fd, fd_set *s) { int _i=0; while(_i<s->fd_count){if(s->fd_array[_i]==fd) return 1;_i++;} return 0; }
#define FD_ISSET(fd,s) fd_isset((SOCKET)(fd), s)
#ifndef _TIMEVAL_DEFINED
#define _TIMEVAL_DEFINED
struct timeval { long tv_sec; long tv_usec; };
#endif
int PASCAL select(int, fd_set*, fd_set*, fd_set*, const struct timeval*);
#else
/* POSIX (Linux/macOS) headers */
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <alloca.h>
typedef int SOCKET;
#define INVALID_SOCKET (-1)
#define closesocket(s) close(s)
#endif

/* === Frame Pool (P0-10.1) ===
 * Pre-allocated pool of TLLFrame objects to eliminate calloc/free per function call.
 * Frames are recycled: acquire from pool on create_frame, release back to pool on free_frame.
 * Pool grows dynamically, capped at FRAME_POOL_MAX to avoid unbounded memory.
 */
#define FRAME_POOL_INITIAL 64
#define FRAME_POOL_MAX 512

static TLLFrame **g_frame_pool = NULL;
static int g_frame_pool_size = 0;
static int g_frame_pool_capacity = 0;

static TLLFrame *frame_pool_acquire(void) {
    if (g_frame_pool_size > 0) {
        return g_frame_pool[--g_frame_pool_size];
    }
    /* Pool empty: allocate fresh frame with all arrays */
    TLLFrame *frame = (TLLFrame*)calloc(1, sizeof(TLLFrame));
    frame->registerCount = 4096;
    frame->registers = (TLLValue*)calloc(4096, sizeof(TLLValue));
    frame->argStackCapacity = 64;
    frame->argStack = (TLLValue*)calloc(64, sizeof(TLLValue));
    frame->tryStackCapacity = 16;
    frame->tryStack = (int*)calloc(16, sizeof(int));
    frame->localCapacity = 0;
    frame->locals = NULL;
    return frame;
}

static void frame_pool_release(TLLFrame *frame) {
    if (g_frame_pool_size >= FRAME_POOL_MAX) {
        /* Pool full: actually free */
        free(frame->registers);
        free(frame->locals);
        free(frame->argStack);
        free(frame->tryStack);
        free(frame);
        return;
    }
    if (g_frame_pool_size >= g_frame_pool_capacity) {
        g_frame_pool_capacity = g_frame_pool_capacity ? g_frame_pool_capacity * 2 : FRAME_POOL_INITIAL;
        g_frame_pool = (TLLFrame**)realloc(g_frame_pool, g_frame_pool_capacity * sizeof(TLLFrame*));
    }
    g_frame_pool[g_frame_pool_size++] = frame;
}

static void push_arg(TLLFrame *frame, TLLValue v) {
    if (frame->argStackSize >= frame->argStackCapacity) {
        frame->argStackCapacity = frame->argStackCapacity ? frame->argStackCapacity * 2 : 16;
        frame->argStack = (TLLValue*)realloc(frame->argStack, frame->argStackCapacity * sizeof(TLLValue));
    }
    frame->argStack[frame->argStackSize++] = v;
}

static TLLValue pop_arg(TLLFrame *frame) {
    if (frame->argStackSize <= 0) return tll_null();
    return frame->argStack[--frame->argStackSize];
}

static void push_try(TLLFrame *frame, int pc) {
    if (frame->tryStackSize >= frame->tryStackCapacity) {
        frame->tryStackCapacity = frame->tryStackCapacity ? frame->tryStackCapacity * 2 : 8;
        frame->tryStack = (int*)realloc(frame->tryStack, frame->tryStackCapacity * sizeof(int));
    }
    frame->tryStack[frame->tryStackSize++] = pc;
}

static int pop_try(TLLFrame *frame) {
    if (frame->tryStackSize <= 0) return -1;
    return frame->tryStack[--frame->tryStackSize];
}

/* Forward declarations for coroutine support */
static TLLFrame *create_frame(TLLFunction *fn, int returnReg, TLLClosureEnv *env);
static void free_frame(TLLFrame *frame);

/* === Coroutine support (P0-15.14: VM-level yield/resume) ===
 * P0-15.15: Moved from global static state to per-VM state.
 * Each TLLVM owns its own coroutine scheduler, enabling multi-VM
 * scenarios (Agent Runtime, sandbox VMs, plugin VMs).
 */

static void coroutine_init(TLLVM *vm) {
    vm->coroutineCount = 0;
    vm->currentCoroutine = 0;
    if (vm->coroutines) { free(vm->coroutines); vm->coroutines = NULL; }
    vm->coroutineCapacity = 16;
    vm->coroutines = (TLLCoroutine**)calloc(16, sizeof(TLLCoroutine*));
}

/* Destroy a coroutine: free all frames (return to pool), free callStack,
 * free result, free struct, swap-remove from scheduler array.
 * P0-15.15: Proper lifecycle recycling.
 */
static void coroutine_destroy(TLLVM *vm, int idx) {
    if (idx < 0 || idx >= vm->coroutineCount) return;
    TLLCoroutine *co = vm->coroutines[idx];
    if (!co) return;

    /* Free all frames in this coroutine's call stack */
    int i;
    for (i = 0; i < co->callStackSize; i++) {
        if (co->callStack[i]) {
            free_frame(co->callStack[i]);
        }
    }
    free(co->callStack);

    /* Free result value (may hold references to arrays/maps/strings) */
    tll_value_free(co->result);

    /* Free the coroutine struct itself */
    free(co);

    /* Swap-remove from scheduler array */
    int last = vm->coroutineCount - 1;
    if (idx != last) {
        vm->coroutines[idx] = vm->coroutines[last];
    }
    vm->coroutines[last] = NULL;
    vm->coroutineCount--;

    /* Adjust currentCoroutine if it was affected by the swap */
    if (vm->currentCoroutine == last) {
        /* current was the last element, now swapped to idx */
        vm->currentCoroutine = idx;
    } else if (vm->currentCoroutine >= vm->coroutineCount) {
        vm->currentCoroutine = 0;
    }
}

static TLLCoroutine *coroutine_create(TLLVM *vm, TLLFunction *fn, TLLValue *args, int argCount, TLLClosureEnv *env) {
    TLLCoroutine *co = (TLLCoroutine*)calloc(1, sizeof(TLLCoroutine));
    co->callStackCapacity = 64;
    co->callStack = (TLLFrame**)calloc(64, sizeof(TLLFrame*));
    co->callStackSize = 0;
    co->state = 0;
    co->invokeTargetStackSize = -1;
    co->result = tll_null();

    TLLFrame *frame = create_frame(fn, -1, env);
    int i;
    for (i = 0; i < argCount && i < fn->paramCount; i++) {
        tll_value_free(frame->locals[i]);
        tll_value_incref(args[i]);
        frame->locals[i] = args[i];
    }
    co->callStack[co->callStackSize++] = frame;

    if (vm->coroutineCount >= vm->coroutineCapacity) {
        vm->coroutineCapacity *= 2;
        vm->coroutines = (TLLCoroutine**)realloc(vm->coroutines, vm->coroutineCapacity * sizeof(TLLCoroutine*));
    }
    vm->coroutines[vm->coroutineCount++] = co;
    return co;
}

static void coroutine_save_current(TLLVM *vm) {
    if (vm->currentCoroutine < 0 || vm->currentCoroutine >= vm->coroutineCount) return;
    TLLCoroutine *co = vm->coroutines[vm->currentCoroutine];
    if (!co) return;
    co->callStack = vm->callStack;
    co->callStackSize = vm->callStackSize;
    co->callStackCapacity = vm->callStackCapacity;
    co->invokeTargetStackSize = vm->invokeTargetStackSize;
}

static void coroutine_restore(TLLVM *vm, int idx) {
    if (idx < 0 || idx >= vm->coroutineCount) return;
    TLLCoroutine *co = vm->coroutines[idx];
    if (!co) return;
    vm->callStack = co->callStack;
    vm->callStackSize = co->callStackSize;
    vm->callStackCapacity = co->callStackCapacity;
    vm->invokeTargetStackSize = co->invokeTargetStackSize;
    vm->currentCoroutine = idx;
}

/* Get current time in milliseconds (unix epoch).
 * Used by unified scheduler for coroutine sleep/wakeup. */
static long long current_time_ms(void) {
#ifdef _WIN32
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    ULARGE_INTEGER uli;
    uli.LowPart = ft.dwLowDateTime;
    uli.HighPart = ft.dwHighDateTime;
    return (long long)(uli.QuadPart / 10000LL) - 11644473600000LL;
#else
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (long long)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
#endif
}

/* P0-15.16: Check if a coroutine is runnable (not dead, not sleeping, not waiting on IO/channel). */
static int coroutine_is_runnable(TLLCoroutine *co) {
    if (!co || co->state == 2) return 0;  /* dead */
    if (co->wakeTime > 0) return 0;         /* sleeping */
    if (co->waitingFd > 0) return 0;        /* waiting on IO */
    if (co->waitingChannel != NULL) return 0; /* waiting on channel */
    return 1;
}

/* P0-15.16: Wake all coroutines waiting on a specific channel pointer.
 * Called from builtin coroutine.wakeChannel(). Returns number woken. */
int coroutine_wake_channel(TLLVM *vm, void *channelPtr) {
    int woken = 0;
    int i;
    for (i = 0; i < vm->coroutineCount; i++) {
        TLLCoroutine *co = vm->coroutines[i];
        if (co && co->waitingChannel == channelPtr) {
            co->waitingChannel = NULL;
            woken++;
        }
    }
    return woken;
}

/* Yield: save current, destroy if dead, round-robin to next runnable.
 * P0-15.15: Sleeping coroutines (wakeTime > now) are skipped.
 * P0-15.16: IO-aware - if no runnable coroutines, collect WAITING_IO fds,
 * call select() with timeout from earliest sleeper, wake ready fds.
 * WAITING_CHANNEL coroutines skipped until explicitly woken via wakeChannel.
 */
static void coroutine_yield(TLLVM *vm) {
    int old = vm->currentCoroutine;

    /* Save current coroutine state */
    coroutine_save_current(vm);

    /* If current is dead, destroy it now (after save, before switch) */
    if (old >= 0 && old < vm->coroutineCount && vm->coroutines[old] && vm->coroutines[old]->state == 2) {
        coroutine_destroy(vm, old);
        if (old >= vm->coroutineCount) old = (vm->coroutineCount > 0) ? vm->coroutineCount - 1 : 0;
    }

    /* No coroutines left - nothing to restore */
    if (vm->coroutineCount == 0) return;

    /* Try up to 2 times: first pass find runnable, second after IO/timer wait */
    int pass;
    for (pass = 0; pass < 2; pass++) {
        /* Wake expired sleepers */
        long long now = current_time_ms();
        int i;
        for (i = 0; i < vm->coroutineCount; i++) {
            TLLCoroutine *co = vm->coroutines[i];
            if (co && co->wakeTime > 0 && co->wakeTime <= now) {
                co->wakeTime = 0;
            }
        }

        /* Find next runnable coroutine */
        int next = -1;
        for (i = 0; i < vm->coroutineCount; i++) {
            int idx = (old + 1 + i) % vm->coroutineCount;
            if (coroutine_is_runnable(vm->coroutines[idx])) {
                next = idx;
                break;
            }
        }

        if (next >= 0) {
            coroutine_restore(vm, next);
            return;
        }

        /* No runnable. On first pass, wait for IO or timers. */
        if (pass == 0) {
            fd_set readfds, writefds, exceptfds;
            FD_ZERO(&readfds);
            FD_ZERO(&writefds);
            FD_ZERO(&exceptfds);
            int maxFd = 0;
            int ioCount = 0;
            long long minWake = 0;
            int sleepCount = 0;

            for (i = 0; i < vm->coroutineCount; i++) {
                TLLCoroutine *co = vm->coroutines[i];
                if (!co || co->state == 2) continue;
                if (co->waitingFd > 0) {
                    SOCKET s = (SOCKET)co->waitingFd;
                    if (co->waitingEvents & 1) FD_SET(s, &readfds);
                    if (co->waitingEvents & 2) FD_SET(s, &writefds);
                    FD_SET(s, &exceptfds);
                    if ((int)s > maxFd) maxFd = (int)s;
                    ioCount++;
                }
                if (co->wakeTime > 0) {
                    if (minWake == 0 || co->wakeTime < minWake) minWake = co->wakeTime;
                    sleepCount++;
                }
            }

            /* Nothing to wait on (only channel-waiters) 鈫?exit cleanly */
            if (ioCount == 0 && sleepCount == 0) return;

            if (ioCount > 0) {
                struct timeval tv, *ptv = NULL;
                if (sleepCount > 0) {
                    now = current_time_ms();
                    long long timeoutMs = (minWake > now) ? (minWake - now) : 0;
                    tv.tv_sec = (long)(timeoutMs / 1000);
                    tv.tv_usec = (long)((timeoutMs % 1000) * 1000);
                    ptv = &tv;
                }
                int ready = select(maxFd + 1, &readfds, &writefds, &exceptfds, ptv);
                if (ready > 0) {
                    for (i = 0; i < vm->coroutineCount; i++) {
                        TLLCoroutine *co = vm->coroutines[i];
                        if (!co || co->waitingFd <= 0) continue;
                        SOCKET s = (SOCKET)co->waitingFd;
                        int isReady = 0;
                        if ((co->waitingEvents & 1) && FD_ISSET(s, &readfds)) isReady = 1;
                        if ((co->waitingEvents & 2) && FD_ISSET(s, &writefds)) isReady = 1;
                        if (FD_ISSET(s, &exceptfds)) isReady = 1;
                        if (isReady) {
                            co->waitingFd = 0;
                            co->waitingEvents = 0;
                        }
                    }
                }
            } else {
                /* Only sleepers, no IO */
                now = current_time_ms();
                if (minWake > now) {
                    long long sleepMs = minWake - now;
                    if (sleepMs > 0) {
#ifdef _WIN32
                        Sleep((DWORD)sleepMs);
#else
                        usleep((useconds_t)(sleepMs * 1000));
#endif
                    }
                }
            }
            /* loop back to wake expired sleepers and find runnable */
        } else {
            /* Second pass still no runnable - restore first alive to avoid crash */
            for (i = 0; i < vm->coroutineCount; i++) {
                if (vm->coroutines[i] && vm->coroutines[i]->state != 2) {
                    coroutine_restore(vm, i);
                    return;
                }
            }
            return;
        }
    }
}

TLLVM *tll_vm_create(TLLProgram *prog) {
    TLLVM *vm = (TLLVM*)calloc(1, sizeof(TLLVM));
    vm->program = prog;
    vm->globalCount = prog->globalCount;
    vm->globals = (TLLValue*)calloc(prog->globalCount, sizeof(TLLValue));
    for (int i = 0; i < prog->globalCount; i++) vm->globals[i] = tll_null();
    vm->callStackCapacity = 64;
    vm->callStack = (TLLFrame**)calloc(64, sizeof(TLLFrame*));
    vm->invokeTargetStackSize = -1;
    /* P0-15.15: per-VM coroutine scheduler starts empty */
    vm->coroutines = NULL;
    vm->coroutineCount = 0;
    vm->coroutineCapacity = 0;
    vm->currentCoroutine = 0;
    return vm;
}

static TLLFrame *create_frame(TLLFunction *fn, int returnReg, TLLClosureEnv *env) {
    /* Acquire frame from pool (or allocate if pool empty) */
    TLLFrame *frame = frame_pool_acquire();
    frame->function = fn;
    frame->pc = 0;
    /* Reset only registers actually used by this function (P0-10) */
    int regCount = fn->maxRegister > 0 ? fn->maxRegister : 1;
    for (int i = 0; i < regCount; i++) frame->registers[i] = tll_null();
    frame->localCount = fn->localCount;
    /* locals array: reallocate if function needs more locals than current capacity */
    int needed_locals = fn->localCount > 0 ? fn->localCount : 1;
    if (frame->localCapacity < needed_locals) {
        if (frame->locals) free(frame->locals);
        frame->locals = (TLLValue*)calloc(needed_locals, sizeof(TLLValue));
        frame->localCapacity = needed_locals;
    }
    for (int i = 0; i < fn->localCount; i++) frame->locals[i] = tll_null();
    frame->argStackSize = 0;
    frame->tryStackSize = 0;
    frame->returnReg = returnReg;
    frame->closureEnv = env;
    return frame;
}

static void push_frame(TLLVM *vm, TLLFrame *frame) {
    if (vm->callStackSize >= vm->callStackCapacity) {
        vm->callStackCapacity *= 2;
        vm->callStack = (TLLFrame**)realloc(vm->callStack, vm->callStackCapacity * sizeof(TLLFrame*));
    }
    vm->callStack[vm->callStackSize++] = frame;
}

static TLLFrame *pop_frame(TLLVM *vm) {
    if (vm->callStackSize <= 0) return NULL;
    TLLFrame *f = vm->callStack[--vm->callStackSize];
    return f;
}

static void free_frame(TLLFrame *frame) {
    /* Detach closureEnv first: registers/locals may hold TLL_FUNCTION values
       whose env == frame->closureEnv.  We must release those before the
       final closureEnv decref, otherwise a returned closure gets a freed env. */
    TLLClosureEnv *env = frame->closureEnv;
    frame->closureEnv = NULL;

    /* Release only registers actually used by this function (P0-10) */
    int regCount = frame->function->maxRegister > 0 ? frame->function->maxRegister : 1;
    for (int i = 0; i < regCount; i++) tll_value_free(frame->registers[i]);
    for (int i = 0; i < frame->localCount; i++) tll_value_free(frame->locals[i]);
    for (int i = 0; i < frame->argStackSize; i++) tll_value_free(frame->argStack[i]);

    if (env && --env->refCount == 0) {
        for (int i = 0; i < env->count; i++) {
            TLLUpvalue *box = env->upvalues[i];
            if (box && --box->refCount == 0) {
                tll_value_free(box->value);
                free(box);
            }
        }
        free(env->upvalues);
        free(env);
    }

    /* Return frame to pool instead of freeing (P0-10 frame pool) */
    frame_pool_release(frame);
}

static void throw_exception(TLLVM *vm, TLLFrame *frame, TLLValue error) {
    tll_value_incref(error);
    /* Search current frame's try stack first */
    while (frame->tryStackSize > 0) {
        int catchPc = pop_try(frame);
        frame->pc = catchPc;
        frame->registers[0] = error;
        return;
    }
    /* Search up the call stack */
    while (vm->callStackSize > 1) {
        TLLFrame *f = pop_frame(vm);
        free_frame(f);
        TLLFrame *parent = vm->callStack[vm->callStackSize - 1];
        if (parent->tryStackSize > 0) {
            int catchPc = pop_try(parent);
            parent->pc = catchPc;
            parent->registers[0] = error;
            return;
        }
        frame = parent;
    }
    /* No handler - fatal */
    char *msg = tll_to_string(error);
    fprintf(stderr, "Uncaught exception: %s\n", msg);
    free(msg);
    tll_value_free(error);
    exit(1);
}

/* Forward declaration */
TLLValue tll_call_builtin(TLLVM *vm, int idx, TLLValue *args, int argCount);

static void do_call(TLLVM *vm, TLLFrame *frame, int resultReg, int fnIdx, int argCount) {
    TLLValue *args = (TLLValue*)alloca(argCount * sizeof(TLLValue));
    for (int i = argCount - 1; i >= 0; i--) args[i] = pop_arg(frame);

    if (fnIdx >= 100000) {
        /* Indirect call */
        int regNum = fnIdx - 100000;
        TLLValue possibleFn = frame->registers[regNum];
        /* Handle function value represented as map {"__fn":true, "fnIdx":N, "env":...} */
        if (possibleFn.type == TLL_MAP) {
            TLLValue fnFlag = map_get(possibleFn.as.map, "__fn");
            if (fnFlag.type == TLL_BOOL && fnFlag.as.boolean) {
                TLLValue idxVal = map_get(possibleFn.as.map, "fnIdx");
                int actualFnIdx = (idxVal.type == TLL_INT) ? (int)idxVal.as.integer : 0;
                TLLValue envVal = map_get(possibleFn.as.map, "env");
                TLLClosureEnv *env = NULL;
                if (envVal.type != TLL_NULL) {
                    env = (TLLClosureEnv*)calloc(1, sizeof(TLLClosureEnv));
                    env->capacity = 1;
                    env->upvalues = (TLLUpvalue**)calloc(1, sizeof(TLLUpvalue*));
                    env->refCount = 1;
                }
                possibleFn = tll_function(actualFnIdx, env);
            }
        }
        if (possibleFn.type == TLL_BUILTIN) {
            TLLValue result = tll_call_builtin(vm, possibleFn.as.builtin.idx, args, argCount);
            frame->registers[resultReg] = result;
            return;
        }
        if (possibleFn.type == TLL_FUNCTION) {
            int actualFnIdx = possibleFn.as.func.fnIdx;
            TLLClosureEnv *env = possibleFn.as.func.env;
            if (env) env->refCount++;  /* newFrame shares this env */
            if (actualFnIdx >= 0 && actualFnIdx < vm->program->functionCount) {
                TLLFunction *fn = &vm->program->functions[actualFnIdx];
                TLLFrame *newFrame = create_frame(fn, resultReg, env);
                for (int i = 0; i < argCount && i < fn->paramCount; i++) {
                    tll_value_free(newFrame->locals[i]);
                    newFrame->locals[i] = args[i];
                }
                push_frame(vm, newFrame);
                return;
            }
        }
        /* Not callable - return null */
        frame->registers[resultReg] = tll_null();
        return;
    }

    /* Direct call */
    if (fnIdx >= 0 && fnIdx < vm->program->functionCount) {
        TLLFunction *fn = &vm->program->functions[fnIdx];
        TLLFrame *newFrame = create_frame(fn, resultReg, NULL);
        for (int i = 0; i < argCount && i < fn->paramCount; i++) {
            tll_value_free(newFrame->locals[i]);
            newFrame->locals[i] = args[i];
        }
        push_frame(vm, newFrame);
    }
}

static void tll_vm_exec(TLLVM *vm) {
    int targetStack = (vm->invokeTargetStackSize < 0) ? 0 : vm->invokeTargetStackSize;
    int isInvokeMode = (vm->invokeTargetStackSize >= 0);
    while (!tll_should_exit) {
        /* If current call stack reached target:
         * - Invoke mode: invoked function returned, just exit this exec call.
         *   (P0-15.15 fix: previously this incorrectly marked the coroutine dead.)
         * - Normal run mode: current coroutine finished; recycle it and switch.
         */
        if (vm->callStackSize <= targetStack) {
            if (isInvokeMode) {
                break;
            }
            /* Normal run: mark current coroutine dead, then yield will recycle it */
            if (vm->coroutineCount > 0 && vm->currentCoroutine < vm->coroutineCount) {
                vm->coroutines[vm->currentCoroutine]->state = 2; /* dead */
            }
            /* If no coroutines left (or only this dead one), exit */
            if (vm->coroutineCount == 0) break;
            if (vm->coroutineCount == 1 && vm->coroutines[0]->state == 2) {
                /* Save and destroy the last dead coroutine */
                int idx = vm->currentCoroutine;
                if (idx >= 0 && idx < vm->coroutineCount) {
                    coroutine_save_current(vm);
                    coroutine_destroy(vm, idx);
                }
                vm->callStack = NULL;
                vm->callStackSize = 0;
                vm->callStackCapacity = 0;
                break;
            }
            coroutine_yield(vm);
            continue;
        }
        TLLFrame *frame = vm->callStack[vm->callStackSize - 1];
        if (frame->pc >= frame->function->instructionCount) {
            TLLFrame *f = pop_frame(vm);
            if (vm->callStackSize > 0 && f->returnReg >= 0) {
                vm->callStack[vm->callStackSize - 1]->registers[f->returnReg] = tll_null();
            }
            free_frame(f);
            continue;
        }

        TLLInstruction *inst = &frame->function->instructions[frame->pc];
        frame->pc++;
        int a = inst->operandCount > 0 ? inst->operands[0] : 0;
        int b = inst->operandCount > 1 ? inst->operands[1] : 0;
        int c = inst->operandCount > 2 ? inst->operands[2] : 0;
        TLLValue *regs = frame->registers;
        TLLValue *consts = vm->program->constants;

        switch (inst->op) {
            case OP_LOAD_CONST:
                tll_value_incref(consts[b]);
                regs[a] = consts[b];
                break;
            case OP_LOAD_VAR:
                tll_value_incref(frame->locals[b]);
                regs[a] = frame->locals[b];
                break;
            case OP_STORE_VAR:
                tll_value_free(frame->locals[a]);
                tll_value_incref(regs[b]);
                frame->locals[a] = regs[b];
                break;
            case OP_LOAD_GLOBAL:
                tll_value_incref(vm->globals[b]);
                regs[a] = vm->globals[b];
                break;
            case OP_STORE_GLOBAL:
                tll_value_free(vm->globals[a]);
                tll_value_incref(regs[b]);
                vm->globals[a] = regs[b];
                break;
            case OP_BOX_LOCAL: {
                if (!frame->closureEnv) {
                    frame->closureEnv = (TLLClosureEnv*)calloc(1, sizeof(TLLClosureEnv));
                    frame->closureEnv->capacity = 8;
                    frame->closureEnv->upvalues = (TLLUpvalue**)calloc(8, sizeof(TLLUpvalue*));
                    frame->closureEnv->refCount = 1;
                }
                while (frame->closureEnv->count <= b) {
                    if (frame->closureEnv->count >= frame->closureEnv->capacity) {
                        frame->closureEnv->capacity *= 2;
                        frame->closureEnv->upvalues = (TLLUpvalue**)realloc(frame->closureEnv->upvalues, frame->closureEnv->capacity * sizeof(TLLUpvalue*));
                    }
                    frame->closureEnv->upvalues[frame->closureEnv->count++] = NULL;
                }
                TLLUpvalue *box = (TLLUpvalue*)calloc(1, sizeof(TLLUpvalue));
                box->value = frame->locals[a];  /* Move value from local to box */
                frame->locals[a] = tll_null();  /* Clear original to avoid double-free */
                box->refCount = 1;
                frame->closureEnv->upvalues[b] = box;
                break;
            }
            case OP_GET_UPVALUE: {
                if (frame->closureEnv && b < frame->closureEnv->count && frame->closureEnv->upvalues[b]) {
                    tll_value_incref(frame->closureEnv->upvalues[b]->value);
                    regs[a] = frame->closureEnv->upvalues[b]->value;
                } else {
                    regs[a] = tll_null();
                }
                break;
            }
            case OP_SET_UPVALUE: {
                if (frame->closureEnv && a < frame->closureEnv->count && frame->closureEnv->upvalues[a]) {
                    tll_value_free(frame->closureEnv->upvalues[a]->value);
                    tll_value_incref(regs[b]);
                    frame->closureEnv->upvalues[a]->value = regs[b];
                }
                break;
            }
            case OP_CLOSURE: {
                int captureCount = c;
                TLLClosureEnv *newEnv = (TLLClosureEnv*)calloc(1, sizeof(TLLClosureEnv));
                newEnv->capacity = captureCount > 0 ? captureCount : 1;
                newEnv->upvalues = (TLLUpvalue**)calloc(newEnv->capacity, sizeof(TLLUpvalue*));
                newEnv->count = captureCount;
                newEnv->refCount = 1;
                if (frame->closureEnv) {
                    for (int i = 0; i < captureCount; i++) {
                        int slot = inst->operands[3 + i];
                        if (slot < frame->closureEnv->count && frame->closureEnv->upvalues[slot]) {
                            newEnv->upvalues[i] = frame->closureEnv->upvalues[slot];
                            newEnv->upvalues[i]->refCount++;
                        }
                    }
                }
                regs[a] = tll_function(b, newEnv);
                break;
            }
            /* Bitwise operations (P0-15) */
            case OP_BAND: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                regs[a] = tll_int(x & y);
                break;
            }
            case OP_BOR: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                regs[a] = tll_int(x | y);
                break;
            }
            case OP_BXOR: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                regs[a] = tll_int(x ^ y);
                break;
            }
            case OP_BNOT: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                regs[a] = tll_int(~x);
                break;
            }
            case OP_SHL: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                regs[a] = tll_int(x << y);
                break;
            }
            case OP_SHR: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                regs[a] = tll_int((unsigned long long)x >> y);
                break;
            }
            case OP_ROTR: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                unsigned int ux = (unsigned int)x;
                unsigned int uy = (unsigned int)(y & 31);
                regs[a] = tll_int((long long)((ux >> uy) | (ux << (32 - uy))));
                break;
            }
            case OP_ROTL: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                unsigned int ux = (unsigned int)x;
                unsigned int uy = (unsigned int)(y & 31);
                regs[a] = tll_int((long long)((ux << uy) | (ux >> (32 - uy))));
                break;
            }
            case OP_ADD: {
                TLLValue x = regs[b], y = regs[c];
                if (x.type == TLL_STRING || y.type == TLL_STRING) {
                    /* Optimized string concat: allocate RC string directly,
                       avoid 3x temp allocations from tll_to_string + tll_string */
                    const char *sx = NULL, *sy = NULL;
                    int lx = 0, ly = 0;
                    char *tmpx = NULL, *tmpy = NULL;

                    if (x.type == TLL_STRING) { sx = x.as.string; lx = (int)strlen(sx); }
                    else { tmpx = tll_to_string(x); sx = tmpx; lx = (int)strlen(sx); }

                    if (y.type == TLL_STRING) { sy = y.as.string; ly = (int)strlen(sy); }
                    else { tmpy = tll_to_string(y); sy = tmpy; ly = (int)strlen(sy); }

                    /* Allocate refCounted string directly: [int rc][data...] */
                    char *buf = (char*)malloc(sizeof(int) + lx + ly + 1);
                    *(int*)buf = 1;
                    if (lx > 0) memcpy(buf + sizeof(int), sx, lx);
                    if (ly > 0) memcpy(buf + sizeof(int) + lx, sy, ly);
                    buf[sizeof(int) + lx + ly] = '\0';

                    TLLValue v;
                    v.type = TLL_STRING;
                    v.as.string = buf + sizeof(int);
                    regs[a] = v;

                    if (tmpx) free(tmpx);
                    if (tmpy) free(tmpy);
                } else if (x.type == TLL_FLOAT || y.type == TLL_FLOAT) {
                    double dx = (x.type == TLL_INT) ? (double)x.as.integer : x.as.floating;
                    double dy = (y.type == TLL_INT) ? (double)y.as.integer : y.as.floating;
                    regs[a] = tll_float(dx + dy);
                } else {
                    regs[a] = tll_int(x.as.integer + y.as.integer);
                }
                break;
            }
            case OP_SUB:
                regs[a] = (regs[b].type == TLL_FLOAT || regs[c].type == TLL_FLOAT) ?
                    tll_float((regs[b].type==TLL_INT?(double)regs[b].as.integer:regs[b].as.floating) -
                              (regs[c].type==TLL_INT?(double)regs[c].as.integer:regs[c].as.floating)) :
                    tll_int(regs[b].as.integer - regs[c].as.integer);
                break;
            case OP_MUL:
                regs[a] = (regs[b].type == TLL_FLOAT || regs[c].type == TLL_FLOAT) ?
                    tll_float((regs[b].type==TLL_INT?(double)regs[b].as.integer:regs[b].as.floating) *
                              (regs[c].type==TLL_INT?(double)regs[c].as.integer:regs[c].as.floating)) :
                    tll_int(regs[b].as.integer * regs[c].as.integer);
                break;
            case OP_DIV: {
                double dx = (regs[b].type==TLL_INT?(double)regs[b].as.integer:regs[b].as.floating);
                double dy = (regs[c].type==TLL_INT?(double)regs[c].as.integer:regs[c].as.floating);
                regs[a] = tll_float(dx / dy);
                break;
            }
            case OP_MOD:
                regs[a] = tll_int(regs[b].as.integer % regs[c].as.integer);
                break;
            case OP_POW: {
                double dx = (regs[b].type==TLL_INT?(double)regs[b].as.integer:regs[b].as.floating);
                double dy = (regs[c].type==TLL_INT?(double)regs[c].as.integer:regs[c].as.floating);
                regs[a] = tll_float(pow(dx, dy));
                break;
            }
            case OP_EQ: regs[a] = tll_bool(tll_equals(regs[b], regs[c])); break;
            case OP_NEQ: regs[a] = tll_bool(!tll_equals(regs[b], regs[c])); break;
            case OP_LT: {
                if (regs[b].type == TLL_STRING && regs[c].type == TLL_STRING)
                    regs[a] = tll_bool(strcmp(regs[b].as.string, regs[c].as.string) < 0);
                else {
                    double dx = (regs[b].type==TLL_INT?(double)regs[b].as.integer:regs[b].as.floating);
                    double dy = (regs[c].type==TLL_INT?(double)regs[c].as.integer:regs[c].as.floating);
                    regs[a] = tll_bool(dx < dy);
                }
                break;
            }
            case OP_GT: {
                if (regs[b].type == TLL_STRING && regs[c].type == TLL_STRING)
                    regs[a] = tll_bool(strcmp(regs[b].as.string, regs[c].as.string) > 0);
                else {
                    double dx = (regs[b].type==TLL_INT?(double)regs[b].as.integer:regs[b].as.floating);
                    double dy = (regs[c].type==TLL_INT?(double)regs[c].as.integer:regs[c].as.floating);
                    regs[a] = tll_bool(dx > dy);
                }
                break;
            }
            case OP_LE: {
                if (regs[b].type == TLL_STRING && regs[c].type == TLL_STRING)
                    regs[a] = tll_bool(strcmp(regs[b].as.string, regs[c].as.string) <= 0);
                else {
                    double dx = (regs[b].type==TLL_INT?(double)regs[b].as.integer:regs[b].as.floating);
                    double dy = (regs[c].type==TLL_INT?(double)regs[c].as.integer:regs[c].as.floating);
                    regs[a] = tll_bool(dx <= dy);
                }
                break;
            }
            case OP_GE: {
                if (regs[b].type == TLL_STRING && regs[c].type == TLL_STRING)
                    regs[a] = tll_bool(strcmp(regs[b].as.string, regs[c].as.string) >= 0);
                else {
                    double dx = (regs[b].type==TLL_INT?(double)regs[b].as.integer:regs[b].as.floating);
                    double dy = (regs[c].type==TLL_INT?(double)regs[c].as.integer:regs[c].as.floating);
                    regs[a] = tll_bool(dx >= dy);
                }
                break;
            }
            case OP_AND: regs[a] = tll_bool(tll_truthy(regs[b]) && tll_truthy(regs[c])); break;
            case OP_OR: regs[a] = tll_bool(tll_truthy(regs[b]) || tll_truthy(regs[c])); break;
            case OP_NOT: regs[a] = tll_bool(!tll_truthy(regs[b])); break;
            case OP_NEG:
                regs[a] = (regs[b].type == TLL_FLOAT) ? tll_float(-regs[b].as.floating) : tll_int(-regs[b].as.integer);
                break;
            case OP_JMP: frame->pc = a; break;
            case OP_JMP_IF_FALSE:
                if (!tll_truthy(regs[a])) frame->pc = b;
                break;
            case OP_CALL:
                do_call(vm, frame, a, b, c);
                break;
            case OP_RET: {
                TLLValue retVal = regs[a];
                int retReg = frame->returnReg;
                TLLFrame *f = pop_frame(vm);
                if (vm->callStackSize > 0 && retReg >= 0) {
                    tll_value_incref(retVal);
                    vm->callStack[vm->callStackSize - 1]->registers[retReg] = retVal;
                }
                free_frame(f);
                break;
            }
            case OP_PRINT: {
                char *s = tll_to_string(regs[a]);
                fputs(s, stdout);
                free(s);
                break;
            }
            case OP_PRINTLN: {
                char *s = tll_to_string(regs[a]);
                puts(s);
                free(s);
                break;
            }
            case OP_MAKE_ARRAY: {
                TLLValue arr = tll_array();
                for (int i = 0; i < b; i++) {
                    TLLValue v = pop_arg(frame);
                    /* unshift: insert at beginning */
                    if (arr.as.array->length >= arr.as.array->capacity) {
                        arr.as.array->capacity *= 2;
                        arr.as.array->items = (TLLValue*)realloc(arr.as.array->items, arr.as.array->capacity * sizeof(TLLValue));
                    }
                    memmove(&arr.as.array->items[1], arr.as.array->items, arr.as.array->length * sizeof(TLLValue));
                    arr.as.array->items[0] = v;
                    arr.as.array->length++;
                }
                regs[a] = arr;
                break;
            }
            case OP_MAKE_MAP: {
                TLLValue map = tll_map();
                for (int i = 0; i < b; i++) {
                    TLLValue v = pop_arg(frame);
                    TLLValue k = pop_arg(frame);
                    char *ks = tll_to_string(k);
                    map_set(map.as.map, ks, v);
                    free(ks);
                }
                regs[a] = map;
                break;
            }
            case OP_MAKE_STRUCT: {
                /* Reserved opcode: struct represented as map.
                 * Operands: r=result, b=type_index(ignored), c=field_count */
                TLLValue map = tll_map();
                for (int i = 0; i < c; i++) {
                    TLLValue v = pop_arg(frame);
                    TLLValue k = pop_arg(frame);
                    char *ks = tll_to_string(k);
                    map_set(map.as.map, ks, v);
                    free(ks);
                }
                regs[a] = map;
                break;
            }
            case OP_INDEX_GET: {
                TLLValue obj = regs[b];
                if (obj.type == TLL_ARRAY) {
                    int idx = (regs[c].type == TLL_INT) ? (int)regs[c].as.integer : 0;
                    TLLValue val = array_get(obj.as.array, idx);
                    tll_value_incref(val);
                    regs[a] = val;
                } else if (obj.type == TLL_MAP) {
                    char *key = tll_to_string(regs[c]);
                    TLLValue val = map_get(obj.as.map, key);
                    tll_value_incref(val);
                    regs[a] = val;
                    free(key);
                } else {
                    regs[a] = tll_null();
                }
                break;
            }
            case OP_INDEX_SET: {
                TLLValue obj = regs[a];
                if (obj.type == TLL_ARRAY) {
                    int idx = (regs[b].type == TLL_INT) ? (int)regs[b].as.integer : 0;
                    tll_value_incref(regs[c]);
                    array_set(obj.as.array, idx, regs[c]);
                } else if (obj.type == TLL_MAP) {
                    char *key = tll_to_string(regs[b]);
                    tll_value_incref(regs[c]);
                    map_set(obj.as.map, key, regs[c]);
                    free(key);
                }
                break;
            }
            case OP_MEMBER_GET: {
                TLLValue obj = regs[b];
                const char *propName = (consts[c].type == TLL_STRING) ? consts[c].as.string : "";
                if (obj.type == TLL_ARRAY && strcmp(propName, "length") == 0) {
                    regs[a] = tll_int(obj.as.array->length);
                } else if (obj.type == TLL_MAP) {
                    TLLValue val = map_get(obj.as.map, propName);
                    tll_value_incref(val);
                    regs[a] = val;
                } else if (obj.type == TLL_FUNCTION || obj.type == TLL_BUILTIN) {
                    regs[a] = map_get((obj.type==TLL_MAP)?obj.as.map:NULL, propName);
                } else {
                    regs[a] = tll_null();
                }
                break;
            }
            case OP_MEMBER_SET: {
                TLLValue obj = regs[a];
                const char *propName = (consts[b].type == TLL_STRING) ? consts[b].as.string : "";
                if (obj.type == TLL_MAP) {
                    tll_value_incref(regs[c]);
                    map_set(obj.as.map, propName, regs[c]);
                }
                break;
            }
            case OP_SPAWN: {
                /* Spawn coroutine: reg[a] = function, b = arg count */
                TLLValue fnVal = regs[a];
                int argCount = b;
                int fnIdx = -1;
                TLLClosureEnv *env = NULL;
                if (fnVal.type == TLL_FUNCTION) {
                    fnIdx = fnVal.as.func.fnIdx;
                    env = fnVal.as.func.env;
                } else if (fnVal.type == TLL_MAP) {
                    TLLValue fnFlag = map_get(fnVal.as.map, "__fn");
                    if (fnFlag.type == TLL_BOOL && fnFlag.as.boolean) {
                        TLLValue idxVal = map_get(fnVal.as.map, "fnIdx");
                        fnIdx = (idxVal.type == TLL_INT) ? (int)idxVal.as.integer : 0;
                    }
                }
                if (fnIdx >= 0 && fnIdx < vm->program->functionCount) {
                    TLLFunction *fn = &vm->program->functions[fnIdx];
                    TLLValue args[16];
                    int i;
                    for (i = 0; i < argCount && i < 16; i++) {
                        args[i] = pop_arg(frame);
                    }
                    /* Reverse args */
                    for (i = 0; i < argCount / 2 && i < 16; i++) {
                        TLLValue tmp = args[i];
                        args[i] = args[argCount - 1 - i];
                        args[argCount - 1 - i] = tmp;
                    }
                    if (env) env->refCount++;
                    coroutine_create(vm, fn, args, argCount, env);
                    regs[a] = tll_int((long long)(vm->coroutineCount - 1));
                } else {
                    regs[a] = tll_int(-1);
                }
                break;
            }
            case OP_YIELD: {
                coroutine_yield(vm);
                /* After yield, frame may have changed, re-fetch */
                frame = vm->callStack[vm->callStackSize - 1];
                regs = frame->registers;
                break;
            }
            case OP_SLEEP: {
                /* Sleep current coroutine for N ms, then yield.
                 * P0-15.15: unified scheduler - timer-aware coroutine sleep.
                 * operand a = register holding sleep duration in ms.
                 */
                long long sleepMs = 0;
                if (regs[a].type == TLL_INT) {
                    sleepMs = regs[a].as.integer;
                } else if (regs[a].type == TLL_FLOAT) {
                    sleepMs = (long long)regs[a].as.floating;
                }
                if (vm->coroutineCount > 0 && vm->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[vm->currentCoroutine];
                    if (co) {
                        co->wakeTime = current_time_ms() + sleepMs;
                    }
                }
                coroutine_yield(vm);
                /* After yield, frame may have changed, re-fetch */
                frame = vm->callStack[vm->callStackSize - 1];
                regs = frame->registers;
                break;
            }
            case OP_WAIT_READ: {
                /* P0-15.16: Wait for socket fd to become readable.
                 * Sets current coroutine to WAITING_IO, then yields.
                 * Scheduler will call select() and wake when fd is ready.
                 * operand a = register holding socket fd.
                 */
                int fd = 0;
                if (regs[a].type == TLL_INT) fd = (int)regs[a].as.integer;
                if (vm->coroutineCount > 0 && vm->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[vm->currentCoroutine];
                    if (co && fd > 0) {
                        co->waitingFd = fd;
                        co->waitingEvents = 1;  /* READ */
                    }
                }
                coroutine_yield(vm);
                frame = vm->callStack[vm->callStackSize - 1];
                regs = frame->registers;
                break;
            }
            case OP_WAIT_WRITE: {
                /* P0-15.16: Wait for socket fd to become writable. */
                int fd = 0;
                if (regs[a].type == TLL_INT) fd = (int)regs[a].as.integer;
                if (vm->coroutineCount > 0 && vm->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[vm->currentCoroutine];
                    if (co && fd > 0) {
                        co->waitingFd = fd;
                        co->waitingEvents = 2;  /* WRITE */
                    }
                }
                coroutine_yield(vm);
                frame = vm->callStack[vm->callStackSize - 1];
                regs = frame->registers;
                break;
            }
            case OP_WAIT_CHANNEL: {
                /* P0-15.16: Wait for a channel send.
                 * operand a = register holding channel map value.
                 * Stores the map pointer in coroutine.waitingChannel.
                 * Woken by builtin coroutine.wakeChannel(channelMap).
                 */
                if (vm->coroutineCount > 0 && vm->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[vm->currentCoroutine];
                    if (co && regs[a].type == TLL_MAP) {
                        co->waitingChannel = (void*)regs[a].as.map;
                    }
                }
                coroutine_yield(vm);
                frame = vm->callStack[vm->callStackSize - 1];
                regs = frame->registers;
                break;
            }
            case OP_HALT: {
                /* HALT: mark current coroutine dead, switch to next.
                 * P0-15.15: dead coroutine is recycled in coroutine_yield.
                 */
                if (vm->coroutineCount > 0 && vm->currentCoroutine < vm->coroutineCount) {
                    vm->coroutines[vm->currentCoroutine]->state = 2; /* dead */
                }
                if (vm->coroutineCount <= 1) {
                    /* Only this coroutine remains: save, destroy, exit */
                    int idx = vm->currentCoroutine;
                    if (idx >= 0 && idx < vm->coroutineCount) {
                        coroutine_save_current(vm);
                        coroutine_destroy(vm, idx);
                    }
                    vm->callStack = NULL;
                    vm->callStackSize = 0;
                    vm->callStackCapacity = 0;
                    return;
                }
                coroutine_yield(vm);
                /* After yield, frame may have changed, re-fetch */
                frame = vm->callStack[vm->callStackSize - 1];
                regs = frame->registers;
                break;
            }
            case OP_NOP:
                break;
            case OP_PUSH:
                tll_value_incref(regs[a]);
                push_arg(frame, regs[a]);
                break;
            case OP_CONCAT: {
                char *sx = tll_to_string(regs[b]), *sy = tll_to_string(regs[c]);
                char *r = (char*)malloc(strlen(sx) + strlen(sy) + 1);
                strcpy(r, sx); strcat(r, sy);
                regs[a] = tll_string(r);
                free(sx); free(sy); free(r);
                break;
            }
            case OP_LOAD_BUILTIN:
                regs[a] = tll_builtin(b);
                break;
            case OP_TRY_START:
                push_try(frame, a);
                break;
            case OP_TRY_END:
                pop_try(frame);
                break;
            case OP_THROW:
                throw_exception(vm, frame, regs[a]);
                break;
            default:
                fprintf(stderr, "tllvm: unknown opcode %d at pc %d in %s\n", inst->op, frame->pc - 1, frame->function->name);
                exit(1);
        }
    }
}

void tll_vm_run(TLLVM *vm) {
    coroutine_init(vm);

    TLLFunction *mainFn = &vm->program->functions[vm->program->mainFunctionIndex];
    TLLFrame *mainFrame = create_frame(mainFn, -1, NULL);
    push_frame(vm, mainFrame);

    /* Create main coroutine wrapping existing callStack */
    TLLCoroutine *mainCo = (TLLCoroutine*)calloc(1, sizeof(TLLCoroutine));
    mainCo->callStack = vm->callStack;
    mainCo->callStackSize = vm->callStackSize;
    mainCo->callStackCapacity = vm->callStackCapacity;
    mainCo->state = 0;
    mainCo->invokeTargetStackSize = vm->invokeTargetStackSize;
    mainCo->result = tll_null();
    vm->coroutines[vm->coroutineCount++] = mainCo;
    vm->currentCoroutine = 0;

    tll_vm_exec(vm);

    /* P0-15.15: Destroy any remaining coroutines (should be none if all
     * finished naturally, but be defensive). This also frees the main
     * coroutine's callStack which is shared with vm->callStack. */
    while (vm->coroutineCount > 0) {
        coroutine_destroy(vm, 0);
    }
    vm->callStack = NULL;
    vm->callStackSize = 0;
    vm->callStackCapacity = 0;
}

/* Invoke a TLL function from builtin context (synchronous callback).
 * Uses register 4095 as scratch return slot (last register, unused by programs). */
TLLValue tll_vm_invoke(TLLVM *vm, TLLValue fnValue, TLLValue *args, int argCount) {
    int fnIdx = -1;
    TLLClosureEnv *env = NULL;
    const int INVOKE_RET_REG = 4095;

    if (fnValue.type == TLL_MAP) {
        TLLValue fnFlag = map_get(fnValue.as.map, "__fn");
        if (fnFlag.type == TLL_BOOL && fnFlag.as.boolean) {
            TLLValue idxVal = map_get(fnValue.as.map, "fnIdx");
            fnIdx = (idxVal.type == TLL_INT) ? (int)idxVal.as.integer : 0;
            TLLValue envVal = map_get(fnValue.as.map, "env");
            if (envVal.type != TLL_NULL) {
                env = (TLLClosureEnv*)calloc(1, sizeof(TLLClosureEnv));
                env->capacity = 1;
                env->upvalues = (TLLUpvalue**)calloc(1, sizeof(TLLUpvalue*));
            }
        }
    } else if (fnValue.type == TLL_FUNCTION) {
        fnIdx = fnValue.as.func.fnIdx;
        env = fnValue.as.func.env;
    }

    if (fnIdx < 0 || fnIdx >= vm->program->functionCount) return tll_null();

    TLLFunction *fn = &vm->program->functions[fnIdx];
    TLLFrame *parentFrame = vm->callStack[vm->callStackSize - 1];

    tll_value_free(parentFrame->registers[INVOKE_RET_REG]);
    parentFrame->registers[INVOKE_RET_REG] = tll_null();

    TLLFrame *newFrame = create_frame(fn, INVOKE_RET_REG, env);
    for (int i = 0; i < argCount && i < fn->paramCount; i++) {
        tll_value_free(newFrame->locals[i]);
        tll_value_incref(args[i]);
        newFrame->locals[i] = args[i];
    }

    int savedTarget = vm->invokeTargetStackSize;
    vm->invokeTargetStackSize = vm->callStackSize;
    push_frame(vm, newFrame);
    tll_vm_exec(vm);
    vm->invokeTargetStackSize = savedTarget;

    TLLValue result = parentFrame->registers[INVOKE_RET_REG];
    tll_value_incref(result);
    return result;
}

void tll_vm_free(TLLVM *vm) {
    /* P0-15.15: Destroy any remaining coroutines.
     * If tll_vm_run was called, all coroutines were already destroyed there
     * and vm->callStack was set to NULL. If vm was never run, coroutines
     * may be NULL and callStack is owned by the VM directly.
     */
    if (vm->coroutines) {
        while (vm->coroutineCount > 0) {
            TLLCoroutine *co = vm->coroutines[0];
            if (co) {
                int j;
                for (j = 0; j < co->callStackSize; j++) {
                    if (co->callStack[j]) free_frame(co->callStack[j]);
                }
                free(co->callStack);
                tll_value_free(co->result);
                free(co);
            }
            vm->coroutines[0] = vm->coroutines[vm->coroutineCount - 1];
            vm->coroutineCount--;
        }
        free(vm->coroutines);
        vm->coroutines = NULL;
    }

    /* Free callStack only if still owned by VM (not transferred to a
     * coroutine and freed there). tll_vm_run sets this to NULL. */
    if (vm->callStack) {
        while (vm->callStackSize > 0) {
            TLLFrame *f = pop_frame(vm);
            free_frame(f);
        }
        free(vm->callStack);
    }

    int i;
    for (i = 0; i < vm->globalCount; i++) tll_value_free(vm->globals[i]);
    free(vm->globals);
    free(vm);
}
