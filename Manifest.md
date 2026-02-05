

# MANIFEST.md

Postings Extension for SQLite
(Platform-native C extension: macOS `.dylib`, Linux `.so`, Windows `.dll`)

## Purpose

Dette repoet inneholder en **SQLite C-extension** som implementerer postings-baserte operasjoner for store korpusser:

* `post_intersect(blobA, blobB)`
* `post_intersect_offset(blobA, blobB, off_min, off_max)`
* `post_sample(blob, index)`

BLOB-ene inneholder **delta+varint-kodede postingslister** (tokenposisjoner).
Extension brukes til sekvenssøk, nærhetssøk, sampling og kollokasjoner.

Ingen eksterne dependencies.
Kun standard C + SQLite’s `sqlite3ext.h`.

---

## Project Structure

```
sqlite-postings/
  MANIFEST.md        <-- this file
  README.md
  Makefile
  src/
    postings.c       <-- main extension implementation
    postings.h       <-- optional
    varint.c         <-- optional (future expansion)
    varint.h         <-- optional
  build/
    macos/           <-- platform-specific builds (ignored initially)
    linux/
    windows/
  test/
    test_postings.c  <-- optional test runner
```

---

## Build Targets

### macOS (Apple Silicon or Intel)

Produces:

```
build/macos/postings.dylib
```

Command (default):

```
clang -O3 -fPIC -shared \
  -I/opt/homebrew/include -I/usr/local/include -I. \
  -o build/macos/postings.dylib src/postings.c
```

### Linux

Produces:

```
build/linux/postings.so
```

Command:

```
gcc -O3 -fPIC -shared \
  -I/usr/include -I. \
  -o build/linux/postings.so src/postings.c
```

### Windows (optional)

Produces:

```
build/windows/postings.dll
```

Command (MSVC):

```
cl /LD src\postings.c /Fe:build\windows\postings.dll
```

---

## How the extension is loaded

### SQLite CLI

macOS:
```
sqlite> .load ./build/macos/postings.dylib
```

Linux:
```
sqlite> .load ./build/linux/postings.so
```

### Python

```python
db.enable_load_extension(True)
# macOS: build/macos/postings.dylib
# Linux: build/linux/postings.so
db.load_extension("build/linux/postings.so")
```

### Julia

```julia
using SQLite
db = SQLite.DB("shard.db")
# macOS: build/macos/postings.dylib
# Linux: build/linux/postings.so
SQLite.load_extension(db, "build/linux/postings.so")
```

---

## Requirements

* SQLite with extension loading enabled
* `sqlite3ext.h` available (Homebrew, system install, or included manually)
* C compiler (clang/gcc/MSVC)

---

## Tasks Codex is allowed to do

Codex may:

1. Generate cross-platform Makefile rules.
2. Improve `postings.c` (SIMD, galloping search, varint optimisering).
3. Add new SQLite UDFs (e.g. `post_union`, `post_andnot`).
4. Implement tests (`test/test_postings.c`).
5. Generate benchmarks in Python/Julia.
6. Add CI (GitHub Actions) for multi-platform builds.

Codex must **not** introduce external dependencies unless requested.

---

## Goals

* Fast C-level postings intersection for 200M–1B token shards
* Small extensions (<50 KB compiled)
* Deterministic, reproducible, platform-native builds
* Compatible med alle SQLite-baserte DH-prosjekter


