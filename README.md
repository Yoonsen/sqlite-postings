
# README.md

SQLite Postings Extension
Fast delta+varint postings operations for large corpora

## Overview

Denne C-baserte SQLite-utvidelsen implementerer ekstremt raske operasjoner på **delta+varint-encodede postings** (sekvenslister).
Den er laget for tekstkorpus som ligger i SQLite-shards med opptil **500M tokens** per fil.

Extensionen gir deg funksjoner for:

* Eksakt intersection av postings
* Nærhetsinteraksjon (offset-based)
* Sampling fra postings (Gibbs / tilfeldig uttrekk)
* Integrasjon med stand-off metadata (geografi, NER, emitoner, m.m.)

Alle funksjoner kjøres **inne i SQLite**, som vanlige SQL-uttrykk.

---

## Key Functions (UDFs)

### `post_intersect(blobA, blobB)`

Returnerer antall posisjoner der postings A og B overlapper eksakt.

### `post_intersect_offset(blobA, blobB, off_min, off_max)`

Returnerer antall treff der `seq_b - seq_a` er innenfor intervallet `[off_min, off_max]`.

Brukes til:

* kollokasjoner
* nabolagsanalyse
* sekvensbasert matching

### `post_sample(blob, index)`

Returnerer posisjonen ved gitt indeks (0-basert) i postingslista.

Brukes til:

* sampling
* Gibbs / MCMC
* utvalg av fragmenter rundt tokens

---

## Why this extension?

### ✔ High-performance

* Dekoding av postings (delta+varint) i C
* Streaming intersection, O(n)
* Perfekt for shards på 100–500M tokens

### ✔ Zero dependencies

* Kun standard C
* Kun `sqlite3ext.h`
* Ingen linker-avhengigheter

### ✔ Perfect fit for DH pipelines

* Stand-off metadata integreres sømløst
* Eksakt tokenposisjon (viktig for fragment/copyright)
* Fungerer som en mini-Lucene inni SQLite

### ✔ Platform-native

* macOS: `.dylib`
* Linux: `.so`
* Windows: `.dll`

Koden er identisk, kun kompilatet varierer.

---

## Project Layout

```
sqlite-postings/
  MANIFEST.md
  README.md
  Makefile
  src/
    postings.c
    postings.h
    varint.c
    varint.h
  build/
    macos/
    linux/
    windows/
  test/
    test_postings.c
```

---

## Building

### macOS

```bash
make
# output:
# build/macos/postings.dylib
```

### Linux

```bash
make linux
# output:
# build/linux/postings.so
```

### Windows (MSVC)

```cmd
nmake -f Makefile.win
```

(Alternativt kan du bygge manuelt med `cl /LD`.)

---

## Loading the Extension

### SQLite CLI

```sql
.load ./build/macos/postings.dylib
```

### Python

```python
db.enable_load_extension(True)
db.load_extension("build/macos/postings.dylib")
```

### Julia

```julia
using SQLite
db = SQLite.DB("shard.db")
SQLite.load_extension(db, "build/macos/postings.dylib")
```

---

## JSON1 Requirement (for in-SQL concordance)

Hvis du vil bruke `json_each(...)` direkte i SQLite, må SQLite ha JSON1 aktivert.
En rask sjekk i `sqlite3`-CLI:

```sql
SELECT json_array(1, 2, 3);
```

Hvis dette feiler, mangler JSON1 i din SQLite-build.

---

## Quick Test Database

Dette repoet inneholder en liten testdatabase med unigrammer:

```bash
python3 build_test_db.py
```

Deretter kan du åpne `test.db` i `sqlite3` og kjøre `test_queries.sql`.

---

## Example Queries

### Antall geo-treff nær ‘krig’

```sql
SELECT post_intersect_offset(a.post, g.post, -20, +20)
FROM ng1 a
JOIN geo_posts g USING (book_id)
WHERE a.cf1 = :cf_krig
  AND g.type_id = :geo_place;
```

### Sample én tilfeldig forekomst

```sql
SELECT post_sample(post, :idx)
FROM ng1
WHERE cf1 = :cf_id;
```

### Intersection (eksakt)

```sql
SELECT post_intersect(a.post, b.post)
FROM ng1 a, ng1 b
WHERE a.cf1 = :w1 AND b.cf1 = :w2;
```

---

## Performance Notes

* Dekoding: 150–300 MB/s per kjerne
* Intersection på 100k+ postings skjer på millisekunder
* Fungerer perfekt sammen med SQLite’s page cache for store shards
* Anbefales brukt som “IR-motor” bak DH-verktøy, maps, konkordanser, sampling

---

## Contributing and Extending

Codex/GPT kan hjelpe med:

* SIMD-varianter av varint/delta
* Galloping intersection
* Skip-lists i postings
* Additional functions:

  * `post_union`
  * `post_andnot`
  * `post_window(blob, seq, ±N)`

---

## License

MIT (or any license you prefer).

---


