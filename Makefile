EXT_NAME=postings
SRC=src/postings.c
BUILD_DIR_MACOS=build/macos
BUILD_DIR_LINUX=build/linux

# Override if needed: make SQLITE_INCLUDE=/path/to/sqlite/headers
SQLITE_INCLUDE?=

CC?=clang
CFLAGS=-O3 -fPIC -shared

INCLUDES=-I.
ifneq ($(strip $(SQLITE_INCLUDE)),)
  INCLUDES+=-I$(SQLITE_INCLUDE)
else
  INCLUDES+=-I/opt/homebrew/include -I/usr/local/include
endif

.PHONY: all macos linux clean

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
  DEFAULT_TARGET = macos
else
  DEFAULT_TARGET = linux
endif

all: $(DEFAULT_TARGET)

macos:
	@mkdir -p $(BUILD_DIR_MACOS)
	$(CC) $(CFLAGS) $(INCLUDES) -o $(BUILD_DIR_MACOS)/$(EXT_NAME).dylib $(SRC)

linux:
	@mkdir -p $(BUILD_DIR_LINUX)
	$(CC) $(CFLAGS) $(INCLUDES) -o $(BUILD_DIR_LINUX)/$(EXT_NAME).so $(SRC)

clean:
	rm -rf build
