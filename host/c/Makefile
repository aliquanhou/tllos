# TLL Native Launcher Makefile
# Builds tllvm - the bootstrap/host VM for TLL

CC = gcc
CFLAGS = -O2 -Wall -Wextra -std=c99 -D_POSIX_C_SOURCE=200809L
LDFLAGS = -lm

# Windows-specific
ifeq ($(OS),Windows_NT)
    EXE = tllvm.exe
    CFLAGS += -D_WIN32
    LDFLAGS += -lbcrypt
else
    EXE = tllvm
endif

SRCS = main.c vm.c value.c json.c builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c http_client_builtin.c
OBJS = $(SRCS:.c=.o)

all: $(EXE)

$(EXE): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS)

%.o: %.c tllvm.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(EXE)

.PHONY: all clean
