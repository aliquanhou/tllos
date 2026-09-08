# TLL Native Launcher Makefile
# Builds tllvm - the bootstrap/host VM for TLL
#
# P2-01-B.6 Build & Source Convergence:
#   Bytecode VM now uses Shared TLL Runtime Core (runtime/) instead of
#   the old host/c/value.c. This ensures Bytecode and Native targets
#   share the exact same value semantics, reference counting, and
#   arithmetic/comparison implementations.
#
# Shared Runtime Core files:
#   ../../runtime/tll_runtime.h  - core data structures (Binary Compatible with old tllvm.h)
#   ../../runtime/value.c         - value creation, refcount, truthy, equals, Array/Map
#   ../../runtime/arithmetic.c    - arithmetic and comparison operations
#   ../../runtime/io.c            - basic IO and runtime lifecycle

CC = gcc
CFLAGS = -O2 -Wall -Wextra -std=c99 -D_POSIX_C_SOURCE=200809L -I../../runtime
LDFLAGS = -lm

# Windows-specific
ifeq ($(OS),Windows_NT)
    EXE = tllvm.exe
    CFLAGS += -D_WIN32
    LDFLAGS += -lbcrypt -lwinhttp -lws2_32
else
    EXE = tllvm
endif

# Shared TLL Runtime Core (replaces old host/c/value.c)
RUNTIME_CORE_SRCS = ../../runtime/value.c ../../runtime/arithmetic.c ../../runtime/io.c

# VM-specific sources (host/c/)
VM_SRCS = main.c vm.c json.c builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c http_client_builtin.c ffi_builtin.c

SRCS = $(VM_SRCS) $(RUNTIME_CORE_SRCS)
OBJS = $(SRCS:.c=.o)

all: $(EXE)

$(EXE): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS)

%.o: %.c tllvm.h ../../runtime/tll_runtime.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(EXE)

.PHONY: all clean
