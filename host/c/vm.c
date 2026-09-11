/* TLL Bootstrap VM - executes bytecode opcodes.
 * This is the Host/Bootstrap layer. Language semantics live in runtime/vm.tll.
 */
#include "tllvm.h"
#include <stdint.h>


/* === P2-01-C-D2: True Multi-Worker Runtime === */
/* Thread-local current worker. When set, tll_vm_exec uses worker->ctx
 * instead of vm->ctx, enabling true per-worker independent execution. */
#ifdef _WIN32
__declspec(thread) TLLWorker *g_tll_current_worker = NULL;
__declspec(thread) int g_worker_yield_requested = 0;
#else
__thread TLLWorker *g_tll_current_worker = NULL;
__thread int g_worker_yield_requested = 0;
#endif

/* Get current execution context: worker's ctx if in worker thread, else vm->ctx */
#define TLL_CTX(vm) (g_tll_current_worker ? &g_tll_current_worker->ctx : &(vm)->ctx)

/* Debug counters for Heisenbug diagnosis */
static long long dbg_yield_calls = 0;
static long long dbg_pass0_no_runnable = 0;
static long long dbg_pass1_no_runnable = 0;
static long long dbg_timer_wait_sleepers = 0;
static long long dbg_timer_wait_no_sleepers = 0;
static long long dbg_wake_expired = 0;
static long long dbg_restore_self = 0;

/* === Scheduler Timer First-Fault Trace (R3-DIAG-2) ===
 * Fixed-size in-memory ring buffer. Only writes memory, no printf/fprintf,
 * no malloc, no sleep, does not change scheduler behavior.
 * Dumped at program exit if TLL_SCHED_TRACE=1.
 */
#define SCHED_TRACE_SIZE 65536
typedef enum {
    TRACE_COROUTINE_SLEEP = 1,
    TRACE_SCHED_SCAN = 2,
    TRACE_TIMER_WAIT = 3,
    TRACE_WAKE = 4,
    TRACE_SELECT = 5,
    TRACE_RESUME = 6,
    TRACE_NO_RUNNABLE = 7,
    TRACE_RESTORE_SELF = 8,
    TRACE_OPCODE = 9,
    TRACE_SAVE = 10,
    TRACE_RETURN = 11,
    TRACE_LOAD_GLOBAL = 12,
    TRACE_STORE_GLOBAL = 13
} TraceEventType;

typedef struct {
    unsigned long long seq;
    int eventType;
    int currentCoroutine;
    int selectedCoroutine;
    int pass;
    int coroutineCount;
    int sleepCount;
    int runnableCount;
    int deadCount;
    unsigned long long now;
    unsigned long long minWake;
    unsigned long long wakeTime;
    int state;
} SchedulerTraceEntry;

static SchedulerTraceEntry g_schedTrace[SCHED_TRACE_SIZE];
static volatile unsigned long long g_schedTraceSeq = 0;
static volatile int g_schedTraceIdx = 0;
static int g_schedTraceEnabled = -1; /* -1 = not checked yet */
static int g_traceTargetCo = 40001; /* Hardcoded for diagnosis */
static int g_traceTargetChecked = 0;

/* Forward declaration */
void sched_trace_dump(void);

static void sched_trace_record(int eventType, int current, int selected,
                                int pass, int count, int sleepCount,
                                int runnableCount, int deadCount,
                                unsigned long long now, unsigned long long minWake,
                                unsigned long long wakeTime, int state) {
    if (g_schedTraceEnabled < 0) {
        const char *env = getenv("TLL_SCHED_TRACE");
        g_schedTraceEnabled = (env && env[0] == '1') ? 1 : 0;
        if (g_schedTraceEnabled) {
            atexit(sched_trace_dump);
            /* Target hardcoded to 40001 for diagnosis */
        }
    }
    if (!g_schedTraceEnabled) return;
    /* Filter by target coroutine if specified, but skip filter for global events and main (co=0) */
    if (g_traceTargetCo >= 0 &&
        eventType != TRACE_STORE_GLOBAL && eventType != TRACE_LOAD_GLOBAL &&
        current != 0 && selected != 0) {
        if (current != g_traceTargetCo && selected != g_traceTargetCo) {
            return;
        }
    }
    int idx = g_schedTraceIdx;
    SchedulerTraceEntry *e = &g_schedTrace[idx];
    e->seq = g_schedTraceSeq++;
    e->eventType = eventType;
    e->currentCoroutine = current;
    e->selectedCoroutine = selected;
    e->pass = pass;
    e->coroutineCount = count;
    e->sleepCount = sleepCount;
    e->runnableCount = runnableCount;
    e->deadCount = deadCount;
    e->now = now;
    e->minWake = minWake;
    e->wakeTime = wakeTime;
    e->state = state;
    g_schedTraceIdx = (idx + 1) % SCHED_TRACE_SIZE;
}

/* Opcode-level trace for a specific coroutine */
static void sched_trace_opcode(int co, int frameIdx, const char *funcName,
                                int pc, int opcode, int hasClosureEnv, int upvalueIdx) {
    if (!g_schedTraceEnabled) return;
    if (g_traceTargetCo >= 0 && co != g_traceTargetCo) return;
    int idx = g_schedTraceIdx;
    SchedulerTraceEntry *e = &g_schedTrace[idx];
    e->seq = g_schedTraceSeq++;
    e->eventType = TRACE_OPCODE;
    e->currentCoroutine = co;
    e->selectedCoroutine = frameIdx;
    e->pass = pc;
    e->coroutineCount = opcode;
    e->sleepCount = hasClosureEnv;
    e->runnableCount = upvalueIdx;
    e->deadCount = 0;
    e->now = 0;
    e->minWake = 0;
    e->wakeTime = 0;
    e->state = 0;
    g_schedTraceIdx = (idx + 1) % SCHED_TRACE_SIZE;
}

void sched_trace_dump(void) {
    if (g_schedTraceEnabled <= 0) return;
    FILE *f = fopen("sched_trace.log", "w");
    if (!f) return;
    int i;
    int start = g_schedTraceIdx;
    for (i = 0; i < SCHED_TRACE_SIZE; i++) {
        int idx = (start + i) % SCHED_TRACE_SIZE;
        SchedulerTraceEntry *e = &g_schedTrace[idx];
        if (e->seq == 0 && i > 0) continue; /* skip empty entries */
        const char *typeName = "UNKNOWN";
        switch (e->eventType) {
            case TRACE_COROUTINE_SLEEP: typeName = "SLEEP"; break;
            case TRACE_SCHED_SCAN: typeName = "SCAN"; break;
            case TRACE_TIMER_WAIT: typeName = "TIMER_WAIT"; break;
            case TRACE_WAKE: typeName = "WAKE"; break;
            case TRACE_SELECT: typeName = "SELECT"; break;
            case TRACE_RESUME: typeName = "RESUME"; break;
            case TRACE_NO_RUNNABLE: typeName = "NO_RUNNABLE"; break;
            case TRACE_RESTORE_SELF: typeName = "RESTORE_SELF"; break;
            case TRACE_OPCODE: typeName = "OPCODE"; break;
            case TRACE_SAVE: typeName = "SAVE"; break;
            case TRACE_RETURN: typeName = "RETURN"; break;
            case TRACE_LOAD_GLOBAL: typeName = "LOAD_GLOBAL"; break;
            case TRACE_STORE_GLOBAL: typeName = "STORE_GLOBAL"; break;
        }
        if (e->eventType == TRACE_OPCODE) {
            fprintf(f, "[%llu] %s co=%d frame=%d pc=%d op=%d hasEnv=%d upIdx=%d\n",
                    (unsigned long long)e->seq, typeName, e->currentCoroutine,
                    e->selectedCoroutine, e->pass, e->coroutineCount,
                    e->sleepCount, e->runnableCount);
        } else if (e->eventType == TRACE_STORE_GLOBAL) {
            fprintf(f, "[%llu] %s co=%d idx=%d old=%d new=%d vm=0x%llx globals=0x%llx type=%d\n",
                    (unsigned long long)e->seq, typeName, e->currentCoroutine,
                    e->selectedCoroutine, e->pass, e->coroutineCount,
                    (unsigned long long)e->now, (unsigned long long)e->minWake, e->state);
        } else if (e->eventType == TRACE_LOAD_GLOBAL) {
            fprintf(f, "[%llu] %s co=%d idx=%d val=%d vm=0x%llx globals=0x%llx type=%d\n",
                    (unsigned long long)e->seq, typeName, e->currentCoroutine,
                    e->selectedCoroutine, e->pass,
                    (unsigned long long)e->now, (unsigned long long)e->minWake, e->state);
        } else if (e->eventType == TRACE_SAVE || e->eventType == TRACE_RESUME) {
            fprintf(f, "[%llu] %s co=%d stackSize=%d pc=%d\n",
                    (unsigned long long)e->seq, typeName,
                    (e->eventType == TRACE_SAVE) ? e->currentCoroutine : e->selectedCoroutine,
                    e->pass, e->state);
        } else {
            fprintf(f, "[%llu] %s cur=%d sel=%d pass=%d count=%d sleep=%d run=%d dead=%d now=%llu minWake=%llu wake=%llu state=%d\n",
                    (unsigned long long)e->seq, typeName, e->currentCoroutine,
                    e->selectedCoroutine, e->pass, e->coroutineCount,
                    e->sleepCount, e->runnableCount, e->deadCount,
                    (unsigned long long)e->now, (unsigned long long)e->minWake,
                    (unsigned long long)e->wakeTime, e->state);
        }
    }
    fclose(f);
}
#ifdef _WIN32
#include <malloc.h>  /* MSVC alloca */
#ifdef _MSC_VER
/* MSVC: use system winsock2.h. Define FD_SETSIZE before include to support large socket handles. */
#define FD_SETSIZE 1024
#include <winsock2.h>
#include <ws2tcpip.h>
#else
/* TCC: winsock2.h not available, manual declarations below */
#include <windows.h>   /* FILETIME, ULARGE_INTEGER, Sleep, DWORD for unified scheduler timer */
/* Minimal Winsock select declarations (TCC lacks winsock2.h) */
typedef UINT_PTR SOCKET;
#define FD_SETSIZE 64
typedef struct fd_set { unsigned int fd_count; SOCKET fd_array[FD_SETSIZE]; } fd_set;
#define FD_ZERO(s) ((s)->fd_count = 0)
#define FD_SET(fd,s) do { if ((s)->fd_count < FD_SETSIZE) (s)->fd_array[(s)->fd_count++] = (SOCKET)(fd); } while(0)
static int fd_isset(SOCKET fd, fd_set *s) { int _i=0; while(_i<s->fd_count){if(s->fd_array[_i]==fd) return 1;_i++;} return 0; }
#define FD_ISSET(fd,s) fd_isset((SOCKET)(fd), s)
#ifndef _TIMEVAL_DEFINED
#define _TIMEVAL_DEFINED
struct timeval { long tv_sec; long tv_usec; };
#endif
int PASCAL select(int, fd_set*, fd_set*, fd_set*, const struct timeval*);
#endif /* _MSC_VER */
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
#define SOCKET_ERROR (-1)
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

/* P2-01-C-D1: Dynamic Frame — acquire with required register count. */
static TLLFrame *frame_pool_acquire(int requiredRegCount) {
    if (g_frame_pool_size > 0) {
        TLLFrame *frame = g_frame_pool[--g_frame_pool_size];
        if (frame->registerCount < requiredRegCount) {
            free(frame->registers);
            frame->registers = (TLLValue*)calloc(requiredRegCount, sizeof(TLLValue));
            frame->registerCount = requiredRegCount;
        }
        return frame;
    }
    /* Pool empty: allocate fresh frame with all arrays */
    TLLFrame *frame = (TLLFrame*)calloc(1, sizeof(TLLFrame));
    frame->registerCount = requiredRegCount;
    frame->registers = (TLLValue*)calloc(requiredRegCount, sizeof(TLLValue));
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

/* TLL-017: xorshift64* PRNG seeded from OS CSPRNG, replaces predictable rand() */
unsigned long long tll_rng_state = 0x9E3779B97F4A7C15ULL;
int tll_rng_seeded = 0;
void tll_rng_seed(void) {
    if (tll_rng_seeded) return;
    tll_rng_seeded = 1;
#ifdef _WIN32
    unsigned long long seed = 0;
    /* Use BCryptGenRandom (already linked via bcrypt.lib) */
    BCryptGenRandom(NULL, (PUCHAR)&seed, sizeof(seed), BCRYPT_USE_SYSTEM_PREFERRED_RNG);
#else
    unsigned long long seed = 0;
    FILE *f = fopen("/dev/urandom", "rb");
    if (f) { fread(&seed, sizeof(seed), 1, f); fclose(f); }
#endif
    if (seed == 0) seed = 0x9E3779B97F4A7C15ULL ^ (unsigned long long)time(NULL);
    tll_rng_state = seed;
}
unsigned long long tll_rng_next(void) {
    unsigned long long x = tll_rng_state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    tll_rng_state = x;
    return x * 0x2545F4914F6CDD1DULL;
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
    TLL_CTX(vm)->currentCoroutine = 0;
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

    /* P4-2 O1: No-free diagnostic mode - skip all deallocation */
    if (no_free_is_on()) {
        /* Just remove from array, leak the object intentionally for diagnosis */
        int last = vm->coroutineCount - 1;
        if (idx != last) { vm->coroutines[idx] = vm->coroutines[last]; }
        vm->coroutines[last] = NULL;
        vm->coroutineCount--;
        return;
    }

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
    if (TLL_CTX(vm)->currentCoroutine == last) {
        /* current was the last element, now swapped to idx */
        TLL_CTX(vm)->currentCoroutine = idx;
    } else if (TLL_CTX(vm)->currentCoroutine >= vm->coroutineCount) {
        TLL_CTX(vm)->currentCoroutine = 0;
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

    /* P2-01-C-D3: Thread-safe coroutine table insertion.
     * Lock if multi-worker runtime is active to prevent realloc race
     * with worker threads accessing vm->coroutines[]. */
    int co_locked = 0;
    if (vm->coroutine_table_lock) {
#ifdef _WIN32
        EnterCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
        pthread_mutex_lock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
        co_locked = 1;
    }
    if (vm->coroutineCount >= vm->coroutineCapacity) {
        vm->coroutineCapacity *= 2;
        vm->coroutines = (TLLCoroutine**)realloc(vm->coroutines, vm->coroutineCapacity * sizeof(TLLCoroutine*));
    }
    vm->coroutines[vm->coroutineCount++] = co;
    if (co_locked) {
#ifdef _WIN32
        LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
        pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
    }
    return co;
}

static void coroutine_save_current(TLLVM *vm) {
    if (TLL_CTX(vm)->currentCoroutine < 0 || TLL_CTX(vm)->currentCoroutine >= vm->coroutineCount) return;
    TLLCoroutine *co = vm->coroutines[TLL_CTX(vm)->currentCoroutine];
    if (!co) return;
    co->callStack = TLL_CTX(vm)->callStack;
    co->callStackSize = TLL_CTX(vm)->callStackSize;
    co->callStackCapacity = TLL_CTX(vm)->callStackCapacity;
    co->invokeTargetStackSize = TLL_CTX(vm)->invokeTargetStackSize;
    /* Trace save */
    if (g_schedTraceEnabled && (g_traceTargetCo < 0 || TLL_CTX(vm)->currentCoroutine == g_traceTargetCo)) {
        int pc = (TLL_CTX(vm)->callStackSize > 0) ? TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1]->pc : -1;
        sched_trace_record(TRACE_SAVE, TLL_CTX(vm)->currentCoroutine, -1, -1,
                vm->coroutineCount, 0, 0, 0, 0, 0, 0, pc);
    }
}

static void coroutine_restore(TLLVM *vm, int idx) {
    if (idx < 0 || idx >= vm->coroutineCount) return;
    TLLCoroutine *co = vm->coroutines[idx];
    if (!co) return;
    TLL_CTX(vm)->callStack = co->callStack;
    TLL_CTX(vm)->callStackSize = co->callStackSize;
    TLL_CTX(vm)->callStackCapacity = co->callStackCapacity;
    TLL_CTX(vm)->invokeTargetStackSize = co->invokeTargetStackSize;
    TLL_CTX(vm)->currentCoroutine = idx;
    /* Trace restore */
    if (g_schedTraceEnabled && (g_traceTargetCo < 0 || idx == g_traceTargetCo)) {
        int pc = -1;
        int stackSize = TLL_CTX(vm)->callStackSize;
        if (stackSize > 0 && TLL_CTX(vm)->callStack[stackSize - 1]) {
            pc = TLL_CTX(vm)->callStack[stackSize - 1]->pc;
        }
        sched_trace_record(TRACE_RESUME, -1, idx, stackSize,
                vm->coroutineCount, 0, 0, 0, 0, 0, 0, pc);
    }
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
    if (!co || co->state == TLL_COROUTINE_COMPLETED) return 0;  /* completed */
    if (co->wakeTime > 0) return 0;         /* sleeping */
    if (co->waitingFd > 0) return 0;         /* waiting on IO */
    if (co->waitingChannel != NULL) return 0; /* waiting on channel */
    return 1;
}

/* P0-15.16: Wake all coroutines waiting on a specific channel pointer.
 * Called from builtin coroutine.wakeChannel(). Returns number woken. */
int coroutine_wake_channel(TLLVM *vm, void *channelPtr) {
    int woken = 0;
    int i;
    /* D2-R3.1-closure: Dynamically allocated wake list.
     * FAIL-CLOSED: if malloc fails, do NOT change any coroutine state.
     * Either all wakes are recorded, or no state transition happens. */
    int *wakeList = NULL;
    int wakeCount = 0;
    if (vm->coroutineCount > 0) {
        wakeList = (int*)malloc(vm->coroutineCount * sizeof(int));
        if (wakeList == NULL) {
            /* malloc failed: fail-closed, no state changes, no enqueue */
            return 0;
        }
    }

#ifdef _WIN32
    EnterCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_lock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
    for (i = 0; i < vm->coroutineCount; i++) {
        TLLCoroutine *co = vm->coroutines[i];
        if (co && co->waitingChannel == channelPtr) {
            co->waitingChannel = NULL;
            /* D2-R3.1: Only record if this is a true WAITING -> RUNNABLE transition.
             * Already-RUNNABLE coroutines are NOT enqueued again. */
            if (co->state == TLL_COROUTINE_WAITING) {
                co->state = TLL_COROUTINE_RUNNABLE;
                if (wakeCount < vm->coroutineCount) {
                    wakeList[wakeCount++] = i;
                }
            }
            woken++;
        }
    }
#ifdef _WIN32
    LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif

    /* D2-R3.1: Enqueue ONLY the recorded wake list — exact-once, no full-table scan. */
    if (vm->multi_worker_initialized && wakeCount > 0) {
        for (i = 0; i < wakeCount; i++) {
            tll_runnable_queue_enqueue(&vm->runnable_queue, wakeList[i]);
        }
    }
    free(wakeList);
    return woken;
}
/* Yield: save current, destroy if dead, round-robin to next runnable.
 * P0-15.15: Sleeping coroutines (wakeTime > now) are skipped.
 * P0-15.16: IO-aware - if no runnable coroutines, collect WAITING_IO fds,
 * call select() with timeout from earliest sleeper, wake ready fds.
 * WAITING_CHANNEL coroutines skipped until explicitly woken via wakeChannel.
 */
static void coroutine_yield(TLLVM *vm) {
    int old = TLL_CTX(vm)->currentCoroutine;
    int selfDead = 0;
    dbg_yield_calls++;

    /* D2-R2: In worker mode, do NOT internally switch coroutines.
     * Save current state, set yield flag, and return.
     * Worker outer loop handles scheduling. Prevents context corruption. */
    if (g_tll_current_worker != NULL) {
        coroutine_save_current(vm);
        g_worker_yield_requested = 1;
        return;
    }

    /* Save current coroutine state */
    coroutine_save_current(vm);

    /* If current is dead, mark it but do NOT destroy immediately.
     * P0-06-R3: immediate destruction frees the call stack, which may
     * invalidate captured locals referenced by other still-running coroutines.
     * Dead coroutines are collected and destroyed when all coroutines finish. */
    if (old >= 0 && old < vm->coroutineCount && vm->coroutines[old] && vm->coroutines[old]->state == 2) {
        selfDead = 1;
    }

    /* No coroutines left - nothing to restore */
    if (vm->coroutineCount == 0) return;

    /* Try up to 2 times: first pass find runnable, second after IO/timer wait */
    int pass;
    for (pass = 0; pass < 2; pass++) {
        /* Wake expired sleepers */
        long long now = current_time_ms();
        int i;
        int wokeCount = 0;
        for (i = 0; i < vm->coroutineCount; i++) {
            TLLCoroutine *co = vm->coroutines[i];
            if (co && co->wakeTime > 0 && co->wakeTime <= now) {
                co->wakeTime = 0;
                wokeCount++;
            }
        }
        if (wokeCount > 0) {
            sched_trace_record(TRACE_WAKE, old, -1, pass,
                    vm->coroutineCount, 0, 0, 0,
                    (unsigned long long)now, 0, 0, -1);
        }

        /* Find next runnable coroutine */
        int next = -1;
        int runnableCount = 0, deadCount = 0, sleepingCount = 0;
        for (i = 0; i < vm->coroutineCount; i++) {
            int idx = (old + 1 + i) % vm->coroutineCount;
            TLLCoroutine *co = vm->coroutines[idx];
            if (!co || co->state == TLL_COROUTINE_COMPLETED) { deadCount++; continue; }
            if (co->wakeTime > 0) { sleepingCount++; continue; }
            if (co->waitingFd > 0 || co->waitingChannel != NULL) continue;
            runnableCount++;
            /* P0-COMPILER-06 BUG-A: in pass 0, exclude self so that
             * yield() with no other runnable coroutine enters timer/IO wait
             * instead of immediately selecting itself. */
            if (pass == 0 && !selfDead && idx == old) continue;
            if (next < 0) next = idx;
        }

        sched_trace_record(TRACE_SCHED_SCAN, old, next, pass,
                vm->coroutineCount, sleepingCount, runnableCount, deadCount,
                (unsigned long long)now, 0, 0, -1);

        if (next >= 0) {
            sched_trace_record(TRACE_SELECT, old, next, pass,
                    vm->coroutineCount, sleepingCount, runnableCount, deadCount,
                    (unsigned long long)now, 0, 0, -1);
            coroutine_restore(vm, next);
            sched_trace_record(TRACE_RESUME, old, next, pass,
                    vm->coroutineCount, sleepingCount, runnableCount, deadCount,
                    (unsigned long long)now, 0, 0, -1);
            return;
        }

        /* No runnable. On first pass, wait for IO or timers. */
        if (pass == 0) {
            dbg_pass0_no_runnable++;
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
                /* P0-RUNTIME-08-R2: IO wait deadline also contributes to select() timeout */
                if (co->waitDeadline > 0) {
                    if (minWake == 0 || co->waitDeadline < minWake) minWake = co->waitDeadline;
                    sleepCount++;
                }
            }

            /* Nothing to wait on (only channel-waiters) -> restore self */
            if (ioCount == 0 && sleepCount == 0) {
                dbg_timer_wait_no_sleepers++;
                sched_trace_record(TRACE_RESTORE_SELF, old, old, pass,
                        vm->coroutineCount, 0, 0, 0,
                        (unsigned long long)now, 0, 0, -1);
                coroutine_restore(vm, old);
                dbg_restore_self++;
                return;
            }
            /* P0-RUNTIME-08-R2: If only IO waiters and no sleepers/timers,
             * and the current (main) coroutine is dead, do NOT block forever.
             * This happens when the main coroutine finishes while worker
             * coroutines are still waiting on IO (e.g. accept loops).
             * Return to let the VM exit cleanly instead of hanging in select(). */
            if (ioCount > 0 && sleepCount == 0 && selfDead) {
                int allNonDeadAreIO = 1;
                for (i = 0; i < vm->coroutineCount; i++) {
                    TLLCoroutine *co = vm->coroutines[i];
                    if (!co || co->state == TLL_COROUTINE_COMPLETED) continue;
                    if (co->waitingFd <= 0 && co->waitingChannel == NULL) {
                        allNonDeadAreIO = 0;
                        break;
                    }
                }
                if (allNonDeadAreIO) {
                    sched_trace_record(TRACE_RESTORE_SELF, old, old, pass,
                            vm->coroutineCount, 0, 0, 0,
                            (unsigned long long)now, 0, 0, -1);
                    return;
                }
            }

            sched_trace_record(TRACE_TIMER_WAIT, old, -1, pass,
                    vm->coroutineCount, sleepCount, 0, 0,
                    (unsigned long long)now, (unsigned long long)minWake, 0, -1);

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
                            co->waitDeadline = 0;
                            co->waitResult = 1;  /* fd ready */
                        }
                    }
                }
                /* P0-RUNTIME-08-R2: Wake IO waiters whose waitDeadline has expired.
                 * This gives coroutine.waitReadWithTimeout() true bounded semantics. */
                now = current_time_ms();
                for (i = 0; i < vm->coroutineCount; i++) {
                    TLLCoroutine *co = vm->coroutines[i];
                    if (!co || co->waitingFd <= 0) continue;
                    if (co->waitDeadline > 0 && co->waitDeadline <= now) {
                        co->waitingFd = 0;
                        co->waitingEvents = 0;
                        co->waitDeadline = 0;
                        co->waitResult = 0;  /* timeout expired */
                    }
                }
                /* P0-RUNTIME-08-R2: Handle select() SOCKET_ERROR.
                 * On Windows, if any fd in the set is invalid (not a real socket),
                 * select() returns SOCKET_ERROR instead of timing out. This causes
                 * an infinite busy-loop because no IO waiter is woken and no timer
                 * progresses. Wake all IO waiters to break the loop and let them
                 * re-evaluate their fd state. */
                if (ready == SOCKET_ERROR) {
                    for (i = 0; i < vm->coroutineCount; i++) {
                        TLLCoroutine *co = vm->coroutines[i];
                        if (!co || co->waitingFd <= 0) continue;
                        co->waitingFd = 0;
                        co->waitingEvents = 0;
                        co->waitDeadline = 0;
                        co->waitResult = 0;  /* socket error, treat as failure */
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
            sched_trace_record(TRACE_NO_RUNNABLE, old, -1, pass,
                    vm->coroutineCount, 0, 0, 0,
                    (unsigned long long)now, 0, 0, -1);

        /* P0-RUNTIME-07-R3: If there are still sleepers or IO waiters,
             * the timer wait returned early (usleep/select interrupted).
             * Loop back and wait again instead of restoring a sleeping coroutine. */
            int hasSleepers = 0;
            int hasIO = 0;
            for (i = 0; i < vm->coroutineCount; i++) {
                TLLCoroutine *co = vm->coroutines[i];
                if (!co || co->state == 2) continue;
                if (co->wakeTime > 0) hasSleepers = 1;
                if (co->waitingFd > 0) hasIO = 1;
            }
            if (hasSleepers || hasIO) {
                /* Set pass = -1 so pass++ makes it 0, looping back to
                 * pass 0 which will do another timer wait. */
                pass = -1;
                continue;
            }
            /* No sleepers and no IO - restore first alive to avoid crash */
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
    TLL_CTX(vm)->callStackCapacity = 64;
    TLL_CTX(vm)->callStack = (TLLFrame**)calloc(64, sizeof(TLLFrame*));
    TLL_CTX(vm)->invokeTargetStackSize = -1;
    /* P0-15.15: per-VM coroutine scheduler starts empty */
    vm->coroutines = NULL;
    vm->coroutineCount = 0;
    vm->coroutineCapacity = 0;
    TLL_CTX(vm)->currentCoroutine = 0;
    return vm;
}

static TLLFrame *create_frame(TLLFunction *fn, int returnReg, TLLClosureEnv *env) {
    /* Acquire frame from pool (or allocate if pool empty) */
    /* P2-01-C-D1: Dynamic Frame — allocate maxRegister+1 (program regs + INVOKE_RET_REG) */
    int requiredRegCount = (fn->maxRegister > 0 ? fn->maxRegister : 1) + 1;
    TLLFrame *frame = frame_pool_acquire(requiredRegCount);
    frame->pc = 0;
    frame->function = fn;
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
    if (TLL_CTX(vm)->callStackSize >= TLL_CTX(vm)->callStackCapacity) {
        TLL_CTX(vm)->callStackCapacity *= 2;
        TLL_CTX(vm)->callStack = (TLLFrame**)realloc(TLL_CTX(vm)->callStack, TLL_CTX(vm)->callStackCapacity * sizeof(TLLFrame*));
    }
    TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize++] = frame;
    /* P0-RUNTIME-07-R2: Sync current coroutine callStackSize with TLL_CTX(vm)->callStackSize.
     * Prevents double-free: coroutine_destroy() must not re-free frames already
     * freed by OP_RET / natural return. */
    if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine >= 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
        vm->coroutines[TLL_CTX(vm)->currentCoroutine]->callStackSize = TLL_CTX(vm)->callStackSize;
    }
}

static TLLFrame *pop_frame(TLLVM *vm) {
    if (TLL_CTX(vm)->callStackSize <= 0) return NULL;
    TLLFrame *f = TLL_CTX(vm)->callStack[--TLL_CTX(vm)->callStackSize];
    /* P0-RUNTIME-07-R2: Sync current coroutine callStackSize after pop. */
    if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine >= 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
        vm->coroutines[TLL_CTX(vm)->currentCoroutine]->callStackSize = TLL_CTX(vm)->callStackSize;
    }
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

    /* Release pending exception (P0-COMPILER-05 fix) */
    tll_value_free(frame->pending_exception);
    frame->pending_exception = tll_null();
    frame->exception_pending = 0;

    /* Return frame to pool instead of freeing (P0-10 frame pool) */
    frame_pool_release(frame);
}

/* TLL-013: default to hard-exit on uncaught; set to 0 for long-running processes */
int tll_exit_on_uncaught = 1;

static void throw_exception(TLLVM *vm, TLLFrame *frame, TLLValue error) {
    tll_value_incref(error);
    frame->exception_pending = 1;
    tll_value_incref(error);  /* extra ref for pending_exception (avoids double-free in free_frame) */
    frame->pending_exception = error;
    /* Search current frame's try stack first */
    while (frame->tryStackSize > 0) {
        int catchPc = pop_try(frame);
        frame->pc = catchPc;
        frame->registers[0] = error;
        return;
    }
    /* Search up the call stack */
    while (TLL_CTX(vm)->callStackSize > 1) {
        TLLFrame *f = pop_frame(vm);
        free_frame(f);
        TLLFrame *parent = TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1];
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
    /* Compiler diagnostic errors (TLL-E###) are printed cleanly without prefix */
    if (strncmp(msg, "TLL-E", 5) == 0) {
        fprintf(stderr, "%s\n", msg);
    } else {
        fprintf(stderr, "Uncaught exception: %s\n", msg);
    }
    free(msg);
    tll_value_free(error);
    if (tll_exit_on_uncaught) {
        exit(1);
    } else {
        tll_should_exit = 1;
        tll_exit_code = 1;
    }
}

/* Forward declaration */
TLLValue tll_call_builtin(TLLVM *vm, int idx, TLLValue *args, int argCount);

static void do_call(TLLVM *vm, TLLFrame *frame, int resultReg, int fnIdx, int argCount) {
    if (argCount > 4096) argCount = 4096;  /* TLL-024: prevent stack overflow from alloca */
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
    int targetStack = (TLL_CTX(vm)->invokeTargetStackSize < 0) ? 0 : TLL_CTX(vm)->invokeTargetStackSize;
    int isInvokeMode = (TLL_CTX(vm)->invokeTargetStackSize >= 0);
    while (!tll_should_exit) {
        /* D2-R2: In worker mode, if coroutine_yield was called, return to worker. */
        if (g_worker_yield_requested) {
            g_worker_yield_requested = 0;
            return;
        }
        /* If current call stack reached target:
         * - Invoke mode: invoked function returned, just exit this exec call.
         *   (P0-15.15 fix: previously this incorrectly marked the coroutine dead.)
         * - Normal run mode: current coroutine finished; recycle it and switch.
         */
        if (TLL_CTX(vm)->callStackSize <= targetStack) {
            if (isInvokeMode) {
                break;
            }
            /* Normal run: mark current coroutine dead, then yield will recycle it */
            if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
                vm->coroutines[TLL_CTX(vm)->currentCoroutine]->state = 2; /* dead */
            }
            /* If no coroutines left, exit */
            if (vm->coroutineCount == 0) break;
            /* P0-06-R3: check if ALL coroutines are dead. If so, destroy
             * them all and exit. This ensures captured locals remain valid
             * until every coroutine has finished. */
            {
                int allDead = 1;
                int ci;
                for (ci = 0; ci < vm->coroutineCount; ci++) {
                    if (vm->coroutines[ci] && vm->coroutines[ci]->state != 2) {
                        allDead = 0;
                        break;
                    }
                }
                if (allDead) {
                    while (vm->coroutineCount > 0) {
                        coroutine_destroy(vm, 0);
                    }
                    TLL_CTX(vm)->callStack = NULL;
                    TLL_CTX(vm)->callStackSize = 0;
                    TLL_CTX(vm)->callStackCapacity = 0;
                    break;
                }
            }
            coroutine_yield(vm);
            /* P0-RUNTIME-08-R2: If the current (main) coroutine is dead and
             * all remaining non-dead coroutines are only waiting on IO (no
             * runnable, no sleepers), the program should exit instead of
             * looping forever on a dead coroutine. */
            if (TLL_CTX(vm)->currentCoroutine >= 0 &&
                TLL_CTX(vm)->currentCoroutine < vm->coroutineCount &&
                vm->coroutines[TLL_CTX(vm)->currentCoroutine] &&
                vm->coroutines[TLL_CTX(vm)->currentCoroutine]->state == 2) {
                int onlyIOWaiters = 1;
                int ci2;
                for (ci2 = 0; ci2 < vm->coroutineCount; ci2++) {
                    TLLCoroutine *co = vm->coroutines[ci2];
                    if (!co || co->state == TLL_COROUTINE_COMPLETED) continue;
                    if (co->waitingFd <= 0 && co->waitingChannel == NULL) {
                        onlyIOWaiters = 0;
                        break;
                    }
                }
                if (onlyIOWaiters) {
                    /* Destroy all coroutines and exit */
                    while (vm->coroutineCount > 0) {
                        coroutine_destroy(vm, 0);
                    }
                    TLL_CTX(vm)->callStack = NULL;
                    TLL_CTX(vm)->callStackSize = 0;
                    TLL_CTX(vm)->callStackCapacity = 0;
                    break;
                }
            }
            continue;
        }
        TLLFrame *frame = TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1];
        if (frame->pc >= frame->function->instructionCount) {
            TLLFrame *f = pop_frame(vm);
            if (TLL_CTX(vm)->callStackSize > 0 && f->returnReg >= 0) {
                TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1]->registers[f->returnReg] = tll_null();
            }
            free_frame(f);
            continue;
        }

        TLLInstruction *inst = &frame->function->instructions[frame->pc];
        int execPc = frame->pc;
        frame->pc++;
        int a = inst->operandCount > 0 ? inst->operands[0] : 0;
        int b = inst->operandCount > 1 ? inst->operands[1] : 0;
        int c = inst->operandCount > 2 ? inst->operands[2] : 0;
        TLLValue *regs = frame->registers;
        TLLValue *consts = vm->program->constants;

        /* Opcode trace for target coroutine */
        if (g_schedTraceEnabled && (g_traceTargetCo < 0 || TLL_CTX(vm)->currentCoroutine == g_traceTargetCo)) {
            int hasEnv = frame->closureEnv ? 1 : 0;
            int upIdx = -1;
            if (inst->op == 40 || inst->op == 41) upIdx = a; /* OP_LOAD_VAR / OP_STORE_VAR */
            sched_trace_opcode(TLL_CTX(vm)->currentCoroutine, TLL_CTX(vm)->callStackSize - 1,
                    frame->function->name, execPc, inst->op, hasEnv, upIdx);
        }

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
            case OP_LOAD_GLOBAL: {
                tll_value_incref(vm->globals[b]);
                regs[a] = vm->globals[b];
                /* Trace all global loads */
                if (g_schedTraceEnabled) {
                    int valInt = (vm->globals[b].type == TLL_INT) ? (int)vm->globals[b].as.integer : -999999;
                    sched_trace_record(TRACE_LOAD_GLOBAL, TLL_CTX(vm)->currentCoroutine, b,
                            valInt, 0, 0, 0, 0,
                            (unsigned long long)(uintptr_t)vm,
                            (unsigned long long)(uintptr_t)vm->globals, 0,
                            vm->globals[b].type);
                }
                break;
            }
            case OP_STORE_GLOBAL: {
                TLLValue oldVal = vm->globals[a];
                tll_value_free(vm->globals[a]);
                tll_value_incref(regs[b]);
                vm->globals[a] = regs[b];
                /* Trace all global stores */
                if (g_schedTraceEnabled) {
                    int oldInt = (oldVal.type == TLL_INT) ? (int)oldVal.as.integer : -999999;
                    int newInt = (regs[b].type == TLL_INT) ? (int)regs[b].as.integer : -999999;
                    sched_trace_record(TRACE_STORE_GLOBAL, TLL_CTX(vm)->currentCoroutine, a,
                            oldInt, newInt, 0, 0, 0,
                            (unsigned long long)(uintptr_t)vm,
                            (unsigned long long)(uintptr_t)vm->globals, 0,
                            regs[b].type);
                }
                break;
            }
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
                regs[a] = tll_int(x << (y & 63));
                break;
            }
            case OP_SHR: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                regs[a] = tll_int((long long)((unsigned long long)x >> (y & 63)));
                break;
            }
            case OP_ROTR: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                unsigned long long ux = (unsigned long long)x;
                unsigned long long uy = (unsigned long long)(y & 63);
                regs[a] = tll_int((long long)((ux >> uy) | (ux << (64 - uy))));
                break;
            }
            case OP_ROTL: {
                long long x = (regs[b].type==TLL_INT)?regs[b].as.integer:(long long)regs[b].as.floating;
                long long y = (regs[c].type==TLL_INT)?regs[c].as.integer:(long long)regs[c].as.floating;
                unsigned long long ux = (unsigned long long)x;
                unsigned long long uy = (unsigned long long)(y & 63);
                regs[a] = tll_int((long long)((ux << uy) | (ux >> (64 - uy))));
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
            case OP_MUL: {
                TLLValue x = regs[b], y = regs[c];
                if (x.type == TLL_STRING && y.type == TLL_INT) {
                    const char *s = x.as.string;
                    int n = y.as.integer;
                    if (n <= 0) { regs[a] = tll_string(""); }
                    else {
                        int len = (int)strlen(s);
                        if (n > 1000000) n = 1000000;
                        if (len > 0 && n > 2147483647 / len) { throw_exception(vm, frame, tll_string("string multiplication overflow")); break; }
                        char *buf = (char*)malloc(sizeof(int) + len * n + 1);
                        *(int*)buf = 1;
                        for (int i = 0; i < n; i++) memcpy(buf + sizeof(int) + i * len, s, len);
                        buf[sizeof(int) + len * n] = '\0';
                        TLLValue v; v.type = TLL_STRING; v.as.string = buf + sizeof(int);
                        regs[a] = v;
                    }
                } else if (x.type == TLL_INT && y.type == TLL_STRING) {
                    const char *s = y.as.string;
                    int n = x.as.integer;
                    if (n <= 0) { regs[a] = tll_string(""); }
                    else {
                        int len = (int)strlen(s);
                        if (n > 1000000) n = 1000000;
                        if (len > 0 && n > 2147483647 / len) { throw_exception(vm, frame, tll_string("string multiplication overflow")); break; }
                        char *buf = (char*)malloc(sizeof(int) + len * n + 1);
                        *(int*)buf = 1;
                        for (int i = 0; i < n; i++) memcpy(buf + sizeof(int) + i * len, s, len);
                        buf[sizeof(int) + len * n] = '\0';
                        TLLValue v; v.type = TLL_STRING; v.as.string = buf + sizeof(int);
                        regs[a] = v;
                    }
                } else if (x.type == TLL_FLOAT || y.type == TLL_FLOAT) {
                    regs[a] = tll_float((x.type==TLL_INT?(double)x.as.integer:x.as.floating) *
                                        (y.type==TLL_INT?(double)y.as.integer:y.as.floating));
                } else {
                    regs[a] = tll_int(x.as.integer * y.as.integer);
                }
                break;
            }
            case OP_DIV: {
                double dx = (regs[b].type==TLL_INT?(double)regs[b].as.integer:regs[b].as.floating);
                double dy = (regs[c].type==TLL_INT?(double)regs[c].as.integer:regs[c].as.floating);
                regs[a] = tll_float(dx / dy);
                break;
            }
            case OP_MOD:
                if (regs[c].as.integer == 0) {
                    throw_exception(vm, frame, tll_string("modulo by zero"));
                    break;
                }
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
            case OP_MOV:
                tll_value_incref(regs[b]);
                tll_value_free(regs[a]);
                regs[a] = regs[b];
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
                if (TLL_CTX(vm)->callStackSize > 0 && retReg >= 0) {
                    tll_value_incref(retVal);
                    TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1]->registers[retReg] = retVal;
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
                    if (argCount > 16) argCount = 16;
                    TLLValue args[16];
                    int i;
                    for (i = 0; i < argCount; i++) {
                        args[i] = pop_arg(frame);
                    }
                    /* Reverse args */
                    for (i = 0; i < argCount / 2; i++) {
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
                frame = TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1];
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
                if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[TLL_CTX(vm)->currentCoroutine];
                    if (co) {
                        long long now = current_time_ms();
                        co->wakeTime = now + sleepMs;
                        sched_trace_record(TRACE_COROUTINE_SLEEP,
                                TLL_CTX(vm)->currentCoroutine, -1, -1,
                                vm->coroutineCount, 0, 0, 0,
                                (unsigned long long)now, 0, (unsigned long long)co->wakeTime,
                                co ? co->state : -1);
                    }
                }
                coroutine_yield(vm);
                /* After yield, frame may have changed, re-fetch */
                frame = TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1];
                regs = frame->registers;
                break;
            }
            case OP_WAIT_READ: {
                /* P0-15.16: Wait for socket fd to become readable.
                 * Sets current coroutine to WAITING_IO, then yields.
                 * Scheduler will call select() and wake when fd is ready.
                 * operand a = register holding socket fd.
                 * operand b = timeout in ms (0=no timeout, >0=waitDeadline; P0-RUNTIME-08-R2)
                 */
                int fd = 0;
                if (regs[a].type == TLL_INT) fd = (int)regs[a].as.integer;
                if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[TLL_CTX(vm)->currentCoroutine];
                    if (co && fd > 0) {
                        co->waitingFd = fd;
                        co->waitingEvents = 1;  /* READ */
                        co->waitDeadline = 0;
                        /* P0-RUNTIME-08-R2: only set deadline when timeout operand is present */
                        if (inst->operandCount > 1 && regs[b].type == TLL_INT && regs[b].as.integer > 0) {
                            long long now = current_time_ms();
                            co->waitDeadline = now + (long long)regs[b].as.integer;
                        }
                    }
                }
                coroutine_yield(vm);
                frame = TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1];
                regs = frame->registers;
                /* Return waitResult in regs[a]: 1=fd ready, 0=timeout */
                if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[TLL_CTX(vm)->currentCoroutine];
                    if (co) regs[a] = tll_int(co->waitResult);
                }
                break;
            }
            case OP_WAIT_WRITE: {
                /* P0-15.16: Wait for socket fd to become writable. */
                int fd = 0;
                if (regs[a].type == TLL_INT) fd = (int)regs[a].as.integer;
                if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[TLL_CTX(vm)->currentCoroutine];
                    if (co && fd > 0) {
                        co->waitingFd = fd;
                        co->waitingEvents = 2;  /* WRITE */
                        co->waitDeadline = 0;
                        /* P0-RUNTIME-08-R2: only set deadline when timeout operand is present */
                        if (inst->operandCount > 1 && regs[b].type == TLL_INT && regs[b].as.integer > 0) {
                            long long now = current_time_ms();
                            co->waitDeadline = now + (long long)regs[b].as.integer;
                        }
                    }
                }
                coroutine_yield(vm);
                frame = TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1];
                regs = frame->registers;
                /* Return waitResult in regs[a]: 1=fd ready, 0=timeout */
                if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[TLL_CTX(vm)->currentCoroutine];
                    if (co) regs[a] = tll_int(co->waitResult);
                }
                break;
            }
            case OP_WAIT_CHANNEL: {
                /* P0-15.16: Wait for a channel send.
                 * operand a = register holding channel map value.
                 * Stores the map pointer in coroutine.waitingChannel.
                 * Woken by builtin coroutine.wakeChannel(channelMap).
                 */
                if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
                    TLLCoroutine *co = vm->coroutines[TLL_CTX(vm)->currentCoroutine];
                    if (co && regs[a].type == TLL_MAP) {
                        co->waitingChannel = (void*)regs[a].as.map;
                    }
                }
                coroutine_yield(vm);
                frame = TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1];
                regs = frame->registers;
                break;
            }
            case OP_HALT: {
                /* HALT: mark current coroutine dead, switch to next.
                 * P0-15.15: dead coroutine is recycled in coroutine_yield.
                 */
                if (vm->coroutineCount > 0 && TLL_CTX(vm)->currentCoroutine < vm->coroutineCount) {
                    vm->coroutines[TLL_CTX(vm)->currentCoroutine]->state = 2; /* dead */
                }
                if (vm->coroutineCount <= 1) {
                    /* Only this coroutine remains: save, destroy, exit */
                    int idx = TLL_CTX(vm)->currentCoroutine;
                    if (idx >= 0 && idx < vm->coroutineCount) {
                        coroutine_save_current(vm);
                        coroutine_destroy(vm, idx);
                    }
                    TLL_CTX(vm)->callStack = NULL;
                    TLL_CTX(vm)->callStackSize = 0;
                    TLL_CTX(vm)->callStackCapacity = 0;
                    return;
                }
                coroutine_yield(vm);
                /* After yield, frame may have changed, re-fetch */
                frame = TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1];
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
            case OP_CATCH_ENTER:
                frame->exception_pending = 0;
                tll_value_free(frame->pending_exception);
                frame->pending_exception = tll_null();
                break;
            case OP_FINALLY_END:
                if (frame->exception_pending) {
                    /* Re-throw the saved exception (not reg[0], which may be overwritten by finally) */
                    TLLValue err = frame->pending_exception;
                    frame->pending_exception = tll_null();
                    throw_exception(vm, frame, err);
                }
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
    mainCo->callStack = TLL_CTX(vm)->callStack;
    mainCo->callStackSize = TLL_CTX(vm)->callStackSize;
    mainCo->callStackCapacity = TLL_CTX(vm)->callStackCapacity;
    mainCo->state = 0;
    mainCo->invokeTargetStackSize = TLL_CTX(vm)->invokeTargetStackSize;
    mainCo->result = tll_null();
    vm->coroutines[vm->coroutineCount++] = mainCo;
    TLL_CTX(vm)->currentCoroutine = 0;

    tll_vm_exec(vm);

    /* P0-15.15: Destroy any remaining coroutines (should be none if all
     * finished naturally, but be defensive). This also frees the main
     * coroutine's callStack which is shared with TLL_CTX(vm)->callStack. */
    while (vm->coroutineCount > 0) {
        coroutine_destroy(vm, 0);
    }
    TLL_CTX(vm)->callStack = NULL;
    TLL_CTX(vm)->callStackSize = 0;
    TLL_CTX(vm)->callStackCapacity = 0;
}

/* Invoke a TLL function from builtin context (synchronous callback).
 * Uses register 4095 as scratch return slot (last register, unused by programs). */
TLLValue tll_vm_invoke(TLLVM *vm, TLLValue fnValue, TLLValue *args, int argCount) {
    int fnIdx = -1;
    TLLClosureEnv *env = NULL;

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
    TLLFrame *parentFrame = TLL_CTX(vm)->callStack[TLL_CTX(vm)->callStackSize - 1];
    /* P2-01-C-D1: Dynamic INVOKE_RET_REG = last register of parent frame (program never uses it) */
    int INVOKE_RET_REG = parentFrame->registerCount - 1;

    tll_value_free(parentFrame->registers[INVOKE_RET_REG]);
    parentFrame->registers[INVOKE_RET_REG] = tll_null();

    TLLFrame *newFrame = create_frame(fn, INVOKE_RET_REG, env);
    for (int i = 0; i < argCount && i < fn->paramCount; i++) {
        tll_value_free(newFrame->locals[i]);
        tll_value_incref(args[i]);
        newFrame->locals[i] = args[i];
    }

    int savedTarget = TLL_CTX(vm)->invokeTargetStackSize;
    TLL_CTX(vm)->invokeTargetStackSize = TLL_CTX(vm)->callStackSize;
    push_frame(vm, newFrame);
    tll_vm_exec(vm);
    TLL_CTX(vm)->invokeTargetStackSize = savedTarget;

    TLLValue result = parentFrame->registers[INVOKE_RET_REG];
    tll_value_incref(result);
    return result;
}

void tll_vm_free(TLLVM *vm) {
    /* P0-15.15: Destroy any remaining coroutines.
     * If tll_vm_run was called, all coroutines were already destroyed there
     * and TLL_CTX(vm)->callStack was set to NULL. If vm was never run, coroutines
     * may be NULL and callStack is owned by the VM directly.
     */
    if (vm->coroutines) {
        while (vm->coroutineCount > 0) {
            TLLCoroutine *co = vm->coroutines[0];
            if (co && !no_free_is_on()) {
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
    if (TLL_CTX(vm)->callStack) {
        while (TLL_CTX(vm)->callStackSize > 0) {
            TLLFrame *f = pop_frame(vm);
            free_frame(f);
        }
        free(TLL_CTX(vm)->callStack);
    }

    int i;
    for (i = 0; i < vm->globalCount; i++) tll_value_free(vm->globals[i]);
    free(vm->globals);
    free(vm);
}


/* === P2-01-C-D2: True Multi-Worker Runtime === */

/* Shutdown sentinel value for runnable queue */
#define TLL_SHUTDOWN_SENTINEL (-1)

/* Initialize global runnable queue (thread-safe) */
static void tll_runnable_queue_init(TLLRunnableQueue *q) {
    q->head = NULL;
    q->tail = NULL;
    q->count = 0;
#ifdef _WIN32
    q->lock = malloc(sizeof(CRITICAL_SECTION)); InitializeCriticalSection((CRITICAL_SECTION*)q->lock);
    q->sem = CreateSemaphore(NULL, 0, 1000000, NULL);
#else
    q->lock = malloc(sizeof(pthread_mutex_t)); pthread_mutex_init((pthread_mutex_t*)q->lock, NULL);
    pthread_cond_init(&q->cond, NULL);
#endif
}

/* Enqueue coroutine index to global runnable queue (thread-safe) */
static void tll_runnable_queue_enqueue(TLLRunnableQueue *q, int coroutine_idx) {
    TLLRunnableNode *node = (TLLRunnableNode*)malloc(sizeof(TLLRunnableNode));
    node->coroutine_idx = coroutine_idx;
    node->next = NULL;
#ifdef _WIN32
    EnterCriticalSection((CRITICAL_SECTION*)q->lock);
#else
    pthread_mutex_lock((pthread_mutex_t*)q->lock);
#endif
    if (q->tail) {
        q->tail->next = node;
    } else {
        q->head = node;
    }
    q->tail = node;
    q->count++;
#ifdef _WIN32
    LeaveCriticalSection((CRITICAL_SECTION*)q->lock);
    ReleaseSemaphore(q->sem, 1, NULL);
#else
    pthread_mutex_unlock((pthread_mutex_t*)q->lock);
    pthread_cond_signal(&q->cond);
#endif
}

/* P2-01-C-D3: Non-blocking try dequeue.
 * Returns coroutine index if available, -1 if queue empty.
 * Used for worker-local queue first-try before falling back to global queue. */
static int tll_runnable_queue_try_dequeue(TLLRunnableQueue *q) {
#ifdef _WIN32
    /* Non-blocking: check semaphore first */
    DWORD wr = WaitForSingleObject((HANDLE)q->sem, 0);
    if (wr != WAIT_OBJECT_0) return -1;  /* queue empty */
    EnterCriticalSection((CRITICAL_SECTION*)q->lock);
#else
    if (pthread_mutex_trylock((pthread_mutex_t*)q->lock) != 0) return -1;
#endif
    TLLRunnableNode *node = q->head;
    int idx = -1;
    if (node) {
        q->head = node->next;
        if (!q->head) q->tail = NULL;
        q->count--;
        idx = node->coroutine_idx;
    }
#ifdef _WIN32
    LeaveCriticalSection((CRITICAL_SECTION*)q->lock);
#else
    pthread_mutex_unlock((pthread_mutex_t*)q->lock);
#endif
    if (node) free(node);
    return idx;
}

/* Dequeue coroutine index from global runnable queue (blocks until available) */
static int tll_runnable_queue_dequeue(TLLRunnableQueue *q) {
#ifdef _WIN32
    WaitForSingleObject(q->sem, INFINITE);
    EnterCriticalSection((CRITICAL_SECTION*)q->lock);
#else
    pthread_mutex_lock((pthread_mutex_t*)q->lock);
    while (!q->head) {
        pthread_cond_wait(&q->cond, &q->lock);
    }
#endif
    TLLRunnableNode *node = q->head;
    if (node) {
        q->head = node->next;
        if (!q->head) q->tail = NULL;
        q->count--;
    }
#ifdef _WIN32
    LeaveCriticalSection((CRITICAL_SECTION*)q->lock);
#else
    pthread_mutex_unlock((pthread_mutex_t*)q->lock);
#endif
    int idx = node ? node->coroutine_idx : -1;
    free(node);
    return idx;
}

/* Dequeue with timeout (ms). Returns -1 on timeout. D2-R2: allows worker to check timers. */
static int tll_runnable_queue_dequeue_timeout(TLLRunnableQueue *q, int timeoutMs) {
#ifdef _WIN32
    DWORD wr = WaitForSingleObject((HANDLE)q->sem, (DWORD)timeoutMs);
    if (wr == WAIT_TIMEOUT) return -1;
    if (wr != WAIT_OBJECT_0) return -1;
    EnterCriticalSection((CRITICAL_SECTION*)q->lock);
#else
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec += timeoutMs / 1000;
    ts.tv_nsec += (timeoutMs % 1000) * 1000000;
    if (ts.tv_nsec >= 1000000000) { ts.tv_sec++; ts.tv_nsec -= 1000000000; }
    pthread_mutex_lock((pthread_mutex_t*)q->lock);
    while (!q->head) {
        if (pthread_cond_timedwait((pthread_cond_t*)q->cond, (pthread_mutex_t*)q->lock, &ts) == ETIMEDOUT) {
            pthread_mutex_unlock((pthread_mutex_t*)q->lock);
            return -1;
        }
    }
#endif
    TLLRunnableNode *node = q->head;
    if (node) {
        q->head = node->next;
        if (!q->head) q->tail = NULL;
        q->count--;
    }
#ifdef _WIN32
    LeaveCriticalSection((CRITICAL_SECTION*)q->lock);
#else
    pthread_mutex_unlock((pthread_mutex_t*)q->lock);
#endif
    int idx = node ? node->coroutine_idx : -1;
    free(node);
    return idx;
}

/* D2-R2: Wake coroutines whose sleep timer has expired. Called by worker loop. */
/* D2-R3: Wake coroutines whose sleep timer has expired. All state transitions under coroutine_table_lock. */
/* D2-R3.1: Wake coroutines whose sleep timer has expired. Uses wake list for exact-once enqueue. */
static void tll_wake_expired_sleepers(TLLVM *vm) {
    long long now = current_time_ms();
    int i;
    /* D2-R3.1-closure: Dynamically allocated wake list.
     * FAIL-CLOSED: if malloc fails, do NOT change any coroutine state. */
    int *wakeList = NULL;
    int wakeCount = 0;
    if (vm->coroutineCount > 0) {
        wakeList = (int*)malloc(vm->coroutineCount * sizeof(int));
        if (wakeList == NULL) {
            /* malloc failed: fail-closed, no state changes, no enqueue */
            return;
        }
    }

#ifdef _WIN32
    EnterCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_lock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
    for (i = 0; i < vm->coroutineCount; i++) {
        TLLCoroutine *co = vm->coroutines[i];
        if (!co) continue;
        if (co->wakeTime > 0 && co->wakeTime <= now) {
            co->wakeTime = 0;
            /* D2-R3.1: Only record if this is a true WAITING -> RUNNABLE transition. */
            if (co->state == TLL_COROUTINE_WAITING) {
                co->state = TLL_COROUTINE_RUNNABLE;
                if (wakeCount < vm->coroutineCount) {
                    wakeList[wakeCount++] = i;
                }
            }
        }
    }
#ifdef _WIN32
    LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif

    /* D2-R3.1: Enqueue ONLY the recorded wake list — exact-once, no full-table scan. */
    if (vm->multi_worker_initialized && wakeCount > 0) {
        for (i = 0; i < wakeCount; i++) {
            tll_runnable_queue_enqueue(&vm->runnable_queue, wakeList[i]);
        }
    }
    free(wakeList);
}
/* D2-R3: Check IO readiness and wake waiting coroutines. Used by worker scheduler.
 * Collects all waitingFd, calls select(), wakes ready ones, handles timeouts.
 * Returns number of coroutines woken. */
/* D2-R3.1: Check IO readiness and wake waiting coroutines. Uses wake list for exact-once enqueue. */
static int tll_wake_io_ready(TLLVM *vm, int timeoutMs) {
    int woken = 0;
    int i;
    int ioCount = 0;
    int maxFd = 0;
    /* D2-R3.1-closure: Dynamically allocated wake list.
     * FAIL-CLOSED: if malloc fails, do NOT change any coroutine state. */
    int *wakeList = NULL;
    int wakeCount = 0;
    if (vm->coroutineCount > 0) {
        wakeList = (int*)malloc(vm->coroutineCount * sizeof(int));
        if (wakeList == NULL) {
            /* malloc failed: fail-closed, no state changes, no enqueue */
            return 0;
        }
    }
    fd_set readfds, writefds, exceptfds;
    FD_ZERO(&readfds);
    FD_ZERO(&writefds);
    FD_ZERO(&exceptfds);

    /* Collect waiting fds under lock */
#ifdef _WIN32
    EnterCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_lock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
    for (i = 0; i < vm->coroutineCount; i++) {
        TLLCoroutine *co = vm->coroutines[i];
        if (!co || co->waitingFd <= 0) continue;
        SOCKET s = (SOCKET)co->waitingFd;
        if ((int)s > maxFd) maxFd = (int)s;
        if (co->waitingEvents & 1) FD_SET(s, &readfds);
        if (co->waitingEvents & 2) FD_SET(s, &writefds);
        FD_SET(s, &exceptfds);
        ioCount++;
    }
#ifdef _WIN32
    LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif

    if (ioCount == 0) {
        free(wakeList);
        return 0;
    }

    /* Call select */
    struct timeval tv, *ptv = NULL;
    if (timeoutMs > 0) {
        tv.tv_sec = timeoutMs / 1000;
        tv.tv_usec = (timeoutMs % 1000) * 1000;
        ptv = &tv;
    }
    int ready = select(maxFd + 1, &readfds, &writefds, &exceptfds, ptv);

    /* Wake ready coroutines under lock */
#ifdef _WIN32
    EnterCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_lock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
    long long now = current_time_ms();
    for (i = 0; i < vm->coroutineCount; i++) {
        TLLCoroutine *co = vm->coroutines[i];
        if (!co || co->waitingFd <= 0) continue;
        SOCKET s = (SOCKET)co->waitingFd;
        int isReady = 0;
        if (ready > 0) {
            if ((co->waitingEvents & 1) && FD_ISSET(s, &readfds)) isReady = 1;
            if ((co->waitingEvents & 2) && FD_ISSET(s, &writefds)) isReady = 1;
            if (FD_ISSET(s, &exceptfds)) isReady = 1;
        }
        /* Check deadline timeout */
        if (!isReady && co->waitDeadline > 0 && co->waitDeadline <= now) {
            isReady = 1;
            co->waitResult = 0;  /* timeout */
        }
        /* Handle select error: wake all to avoid infinite loop */
        if (ready == SOCKET_ERROR) {
            isReady = 1;
            co->waitResult = 0;
        }
        if (isReady) {
            co->waitingFd = 0;
            co->waitingEvents = 0;
            co->waitDeadline = 0;
            if (co->waitResult != 0) co->waitResult = 1;  /* fd ready */
            /* D2-R3.1: Only record if this is a true WAITING -> RUNNABLE transition. */
            if (co->state == TLL_COROUTINE_WAITING) {
                co->state = TLL_COROUTINE_RUNNABLE;
                if (wakeCount < vm->coroutineCount) {
                    wakeList[wakeCount++] = i;
                }
            }
            woken++;
        }
    }
#ifdef _WIN32
    LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif

    /* D2-R3.1: Enqueue ONLY the recorded wake list — exact-once, no full-table scan. */
    if (wakeCount > 0 && vm->multi_worker_initialized) {
        for (i = 0; i < wakeCount; i++) {
            tll_runnable_queue_enqueue(&vm->runnable_queue, wakeList[i]);
        }
    }
    free(wakeList);
    return woken;
}
/* Initialize worker execution context.
 * D2-R1: do NOT allocate callStack here — worker borrows coroutine's callStack.
 * Allocating here and then overwriting with coro->callStack caused a leak. */
static void tll_worker_ctx_init(TLLExecutionContext *ctx) {
    ctx->callStackCapacity = 0;
    ctx->callStack = NULL;  /* borrowed from coroutine during execution */
    ctx->callStackSize = 0;
    ctx->currentCoroutine = -1;
    ctx->invokeTargetStackSize = -1;
}

/* Free worker execution context.
 * D2-R1: do NOT free callStack — it is owned by the coroutine, not the worker.
 * Worker only borrows it during execution and sets it back to NULL when done. */
static void tll_worker_ctx_free(TLLExecutionContext *ctx) {
    /* callStack is borrowed from coroutine; worker must not free it.
     * If worker is being destroyed while still holding a callStack, that's
     * a lifecycle bug — but we don't free it here to avoid double-free. */
    ctx->callStack = NULL;
    ctx->callStackSize = 0;
    ctx->callStackCapacity = 0;
}

/* Worker thread function - executes coroutines from global queue */
#ifdef _WIN32
static DWORD WINAPI tll_worker_thread(LPVOID param) {
#else
static void *tll_worker_thread(void *param) {
#endif
    TLLWorker *worker = (TLLWorker*)param;
    TLLVM *vm = worker->vm;

    /* Set thread-local current worker - this makes TLL_CTX(vm) use worker->ctx */
    g_tll_current_worker = worker;

    /* Initialize independent execution context */
    tll_worker_ctx_init(&worker->ctx);

    /* P2-01-C-D3: Initialize worker-local runnable queue */
    tll_runnable_queue_init(&worker->local_queue);
    worker->local_enqueue_count = 0;
    worker->local_dequeue_count = 0;

    worker->running = 1;

    while (!vm->shutdown_requested) {
        /* D2-R2: Wake expired sleepers before checking queue */
        tll_wake_expired_sleepers(vm);

        /* P2-01-C-D3-R2-P3: Queue OFF experiment - scan coroutines directly */
        int coro_idx = -1;
        if (queue_is_off()) {
            /* Queue OFF: scan vm->coroutines[] for RUNNABLE coroutine.
             * No queue node malloc/free involved. */
#ifdef _WIN32
            EnterCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
            pthread_mutex_lock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
            int scan_idx = -1;
            for (int si = 0; si < vm->coroutineCount; si++) {
                if (vm->coroutines[si] && vm->coroutines[si]->state == TLL_COROUTINE_RUNNABLE) {
                    scan_idx = si;
                    vm->coroutines[si]->state = TLL_COROUTINE_RUNNING;
                    break;
                }
            }
#ifdef _WIN32
            LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
            pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
            if (scan_idx == -1) {
                /* No runnable coroutine - sleep briefly then retry */
#ifdef _WIN32
                Sleep(1);
#else
                usleep(1000);
#endif
                continue;
            }
            coro_idx = scan_idx;
        } else {
        /* P2-01-C-D3: Local-first dequeue.
         * Try worker-local queue first (non-blocking),
         * then fall back to global queue (with timeout). */
        coro_idx = tll_runnable_queue_try_dequeue(&worker->local_queue);
        if (coro_idx != -1) {
            worker->local_dequeue_count++;
        } else {
            /* Local queue empty — try global queue with timeout */
            coro_idx = tll_runnable_queue_dequeue_timeout(&vm->runnable_queue, 50);
            if (coro_idx == -1) {
                /* D2-R3: Check IO readiness when queue is empty */
                tll_wake_io_ready(vm, 0);
                continue;
            }
        }
        } /* end queue_is_off else */

        /* Check for shutdown sentinel */
        if (coro_idx == TLL_SHUTDOWN_SENTINEL) {
            break;
        }

        /* Validate coroutine index */
        if (coro_idx < 0 || coro_idx >= vm->coroutineCount) {
            continue;
        }

        /* D2-R1: Claim coroutine exactly-once using coroutine_table_lock.
         * Only RUNNABLE coroutines can be claimed; this prevents two workers
         * from simultaneously executing the same coroutine.
         * P2-01-C-D3-R2-P3: In Queue OFF mode, claim was already done during scan. */
        TLLCoroutine *coro = NULL;
        if (!queue_is_off()) {
#ifdef _WIN32
            EnterCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
            pthread_mutex_lock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
            coro = vm->coroutines[coro_idx];
            if (!coro || coro->state != TLL_COROUTINE_RUNNABLE) {
                /* Already claimed by another worker, completed, or invalid */
#ifdef _WIN32
                LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
                pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
                continue;
            }
            coro->state = TLL_COROUTINE_RUNNING;  /* claim: RUNNABLE -> RUNNING */
#ifdef _WIN32
            LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
            pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
        } else {
            /* Queue OFF mode: coro was already claimed during scan (P4-5 fix) */
            coro = scan_coro;
        }

        worker->ctx.currentCoroutine = coro_idx;

        /* Load coroutine's call stack into worker's independent context */
        worker->ctx.callStack = coro->callStack;
        worker->ctx.callStackSize = coro->callStackSize;
        worker->ctx.callStackCapacity = coro->callStackCapacity;
        worker->ctx.invokeTargetStackSize = 0; /* stop when call stack empty */

        /* Execute the coroutine */
        tll_vm_exec(vm);

        /* Save call stack back to coroutine */
        coro->callStack = worker->ctx.callStack;
        coro->callStackSize = worker->ctx.callStackSize;
        coro->callStackCapacity = worker->ctx.callStackCapacity;

        /* D2-R2: Final state transition under coroutine_table_lock.
         * Correctly distinguish COMPLETED / RUNNABLE / WAITING.
         * - COMPLETED: callStack empty
         * - RUNNABLE: callStack non-empty AND not waiting (yield)
         * - WAITING: callStack non-empty AND waiting (sleep/IO/channel)
         * WAITING coroutines are NOT requeued — timer/IO/channel will wake them. */
        int should_requeue = 0;
#ifdef _WIN32
        EnterCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
        pthread_mutex_lock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
        if (coro->callStackSize == 0) {
            coro->state = TLL_COROUTINE_COMPLETED;
        } else if (coroutine_is_runnable(coro)) {
            /* Yielded but not waiting — requeue for immediate execution */
            coro->state = TLL_COROUTINE_RUNNABLE;
            should_requeue = 1;
        } else {
            /* Waiting on sleep/IO/channel — do NOT requeue.
             * Timer/IO/channel scheduler will wake and requeue later. */
            coro->state = TLL_COROUTINE_WAITING;
            should_requeue = 0;
        }
#ifdef _WIN32
        LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
        pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif

        /* P2-01-C-D3: Requeue to worker-local queue first.
         * This worker just executed this coroutine, so cache locality
         * favors re-executing it on the same worker.
         * Only RUNNABLE coroutines are requeued; WAITING ones stay until woken. */
        if (should_requeue) {
            tll_runnable_queue_enqueue(&worker->local_queue, coro_idx);
            worker->local_enqueue_count++;
        }

        worker->tasks_completed++;
        worker->ctx.callStack = NULL;
        worker->ctx.callStackSize = 0;
        worker->ctx.currentCoroutine = -1;
    }

    worker->running = 0;
    /* P2-01-C-D3: Cleanup worker-local runnable queue */
    tll_runnable_queue_cleanup(&worker->local_queue);
    tll_worker_ctx_free(&worker->ctx);
    g_tll_current_worker = NULL;

#ifdef _WIN32
    return 0;
#else
    return NULL;
#endif
}

/* Start N worker threads */
int tll_runtime_start_workers(TLLVM *vm, int count) {
    if (vm->multi_worker_initialized) return -1;
    if (count <= 0 || count > 64) return -1;

    /* Initialize global runnable queue */
    tll_runnable_queue_init(&vm->runnable_queue);

    /* Initialize coroutine table lock */
#ifdef _WIN32
    vm->coroutine_table_lock = malloc(sizeof(CRITICAL_SECTION)); InitializeCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    vm->coroutine_table_lock = malloc(sizeof(pthread_mutex_t)); pthread_mutex_init((pthread_mutex_t*)vm->coroutine_table_lock, NULL);
#endif

    /* P2-01-C-D3-R2-P3: Preallocate coroutine table to avoid realloc during worker execution */
    if (prealloc_table_is_on()) {
        int prealloc_size = 65536;
        vm->coroutines = (TLLCoroutine**)realloc(vm->coroutines, prealloc_size * sizeof(TLLCoroutine*));
        if (vm->coroutines) {
            memset(vm->coroutines + vm->coroutineCount, 0, (prealloc_size - vm->coroutineCount) * sizeof(TLLCoroutine*));
            vm->coroutineCapacity = prealloc_size;
        }
    }

    /* Allocate worker array */
    vm->workers = (TLLWorker**)calloc(count, sizeof(TLLWorker*));
    vm->workerCount = count;
    vm->shutdown_requested = 0;

    /* Create and start each worker */
    for (int i = 0; i < count; i++) {
        TLLWorker *worker = (TLLWorker*)calloc(1, sizeof(TLLWorker));
        worker->worker_id = i;
        worker->vm = vm;
        worker->running = 0;
        worker->tasks_completed = 0;
        vm->workers[i] = worker;

#ifdef _WIN32
        worker->thread = CreateThread(NULL, 0, tll_worker_thread, worker, 0, NULL);
        if (!worker->thread) {
            fprintf(stderr, "tllvm: failed to create worker thread %d\n", i);
            return -1;
        }
#else
        if (pthread_create(&worker->thread, NULL, tll_worker_thread, worker) != 0) {
            fprintf(stderr, "tllvm: failed to create worker thread %d\n", i);
            return -1;
        }
#endif
    }

    vm->multi_worker_initialized = 1;
    fprintf(stderr, "tllvm: started %d worker threads (true multi-worker runtime)\n", count);
    return 0;
}

/* Submit a coroutine to the global runnable queue.
 * D2-R1: state transition under coroutine_table_lock to ensure
 * a coroutine is not submitted while another worker holds it. */
int tll_runtime_submit_coroutine(TLLVM *vm, int coroutine_idx) {
    if (!vm->multi_worker_initialized) return -1;
    if (coroutine_idx < 0 || coroutine_idx >= vm->coroutineCount) return -1;

#ifdef _WIN32
    EnterCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_lock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
    TLLCoroutine *coro = vm->coroutines[coroutine_idx];
    if (!coro) {
#ifdef _WIN32
        LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
        pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
        return -1;
    }
    /* Only accept submission if not already RUNNING (held by a worker) */
    if (coro->state == TLL_COROUTINE_RUNNING) {
#ifdef _WIN32
        LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
        pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif
        return -1;
    }
    coro->state = TLL_COROUTINE_RUNNABLE;
#ifdef _WIN32
    LeaveCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
#else
    pthread_mutex_unlock((pthread_mutex_t*)vm->coroutine_table_lock);
#endif

    tll_runnable_queue_enqueue(&vm->runnable_queue, coroutine_idx);
    return 0;
}

/* D2-R1: Clean up global runnable queue resources (lock, semaphore, nodes) */
static void tll_runnable_queue_cleanup(TLLRunnableQueue *q) {
    /* Free remaining nodes */
    TLLRunnableNode *node = q->head;
    while (node) {
        TLLRunnableNode *next = node->next;
        free(node);
        node = next;
    }
    q->head = q->tail = NULL;
    q->count = 0;

#ifdef _WIN32
    if (q->sem) {
        CloseHandle((HANDLE)q->sem);
        q->sem = NULL;
    }
    if (q->lock) {
        DeleteCriticalSection((CRITICAL_SECTION*)q->lock);
        free(q->lock);
        q->lock = NULL;
    }
#else
    if (q->cond) {
        pthread_cond_destroy((pthread_cond_t*)q->cond);
        free(q->cond);
        q->cond = NULL;
    }
    if (q->lock) {
        pthread_mutex_destroy((pthread_mutex_t*)q->lock);
        free(q->lock);
        q->lock = NULL;
    }
#endif
}

/* Shutdown all worker threads */
void tll_runtime_shutdown_workers(TLLVM *vm) {
    if (!vm->multi_worker_initialized) return;

    vm->shutdown_requested = 1;

    /* Send shutdown sentinel to wake all workers */
    for (int i = 0; i < vm->workerCount; i++) {
        tll_runnable_queue_enqueue(&vm->runnable_queue, TLL_SHUTDOWN_SENTINEL);
    }

    /* Wait for workers to finish */
#ifdef _WIN32
    for (int i = 0; i < vm->workerCount; i++) {
        if (vm->workers[i] && vm->workers[i]->thread) {
            WaitForSingleObject(vm->workers[i]->thread, 5000);
            CloseHandle(vm->workers[i]->thread);
        }
    }
#else
    for (int i = 0; i < vm->workerCount; i++) {
        if (vm->workers[i]) {
            pthread_join(vm->workers[i]->thread, NULL);
        }
    }
#endif

    /* Free workers */
    for (int i = 0; i < vm->workerCount; i++) {
        if (vm->workers[i]) free(vm->workers[i]);
    }
    free(vm->workers);
    vm->workers = NULL;
    vm->workerCount = 0;
    vm->multi_worker_initialized = 0;
    vm->shutdown_requested = 0;

    /* D2-R1: Clean up queue resources (lock, semaphore, remaining nodes) */
    tll_runnable_queue_cleanup(&vm->runnable_queue);

    /* D2-R1: Clean up coroutine_table_lock */
#ifdef _WIN32
    if (vm->coroutine_table_lock) {
        DeleteCriticalSection((CRITICAL_SECTION*)vm->coroutine_table_lock);
        free(vm->coroutine_table_lock);
        vm->coroutine_table_lock = NULL;
    }
#else
    if (vm->coroutine_table_lock) {
        pthread_mutex_destroy((pthread_mutex_t*)vm->coroutine_table_lock);
        free(vm->coroutine_table_lock);
        vm->coroutine_table_lock = NULL;
    }
#endif
}