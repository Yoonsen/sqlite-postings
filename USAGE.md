## SQLite Postings Extension – Quick Manual

This repo builds a small SQLite C extension for working with delta+varint
encoded postings stored as BLOBs. The extension only deals with positions
(sequence numbers), not tokens or text. Token/word lookup lives in a
separate table.

### Data Model Assumption

- `tokens` table: `(bok_id, seq, word)` with primary key `(bok_id, seq)`
- `postings` table: `(bok_id, word, blob)` where `blob` is delta+varint
  encoded sorted positions for that word/ngram

### Build

```
make
```

- macOS output: `build/macos/postings.dylib`
- Linux output: `build/linux/postings.so`

Override headers if needed:

```
make SQLITE_INCLUDE=/path/to/sqlite/headers
```

### Load Extension

In `sqlite3` shell:

```
.load ./build/macos/postings.dylib
```

Or as command line:

```
sqlite3 test.db ".load ./build/macos/postings.dylib"
```

### JSON1 Requirement (for in-SQL concordance)

If you want to expand JSON inside SQLite using `json_each`, your SQLite build
must have JSON1 enabled. Quick check:

```
SELECT json_array(1, 2, 3);
```

### API (UDFs)

#### `post_positions(blob) -> JSON`
Returns all positions as JSON array (e.g. `[1,9,15]`).

#### `post_near_positions(blobA, blobB, off_min, off_max) -> JSON`
Returns positions in A where B is within `[off_min, off_max]`.
Use `off_min > 0` to require B after A, and `off_max < 0` for before.

#### `post_intersect(blobA, blobB) -> INT`
Counts exact overlap positions.

#### `post_intersect_offset(blobA, blobB, off_min, off_max) -> INT`
Counts matches where `seq_b - seq_a` is within `[off_min, off_max]`.

#### `post_sample(blob, idx) -> INT`
Returns the position at index `idx` (0-based) or NULL if out of range.

### Example Queries

All positions for a word:

```
SELECT post_positions(p.blob)
FROM postings p
WHERE p.bok_id = 1 AND p.word = 'demokrati';
```

Near positions (±5):

```
SELECT post_near_positions(a.blob, b.blob, -5, 5)
FROM postings a
JOIN postings b USING (bok_id)
WHERE a.bok_id = 1 AND a.word = 'demokrati' AND b.word = 'diktatur';
```

Sampled concordance (5 random hits, ±3):

```
WITH sampled AS (
  SELECT je.value AS seq
  FROM postings p, json_each(post_positions(p.blob)) AS je
  WHERE p.bok_id = 1 AND p.word = 'demokrati'
  ORDER BY random()
  LIMIT 5
)
SELECT s.seq AS hit_seq, t.seq, t.word
FROM sampled s
JOIN tokens t
  ON t.bok_id = 1
 AND t.seq BETWEEN s.seq - 3 AND s.seq + 3
ORDER BY s.seq, t.seq;
```

### Test Data

Generate a larger test DB:

```
python3 build_test_db.py --db bigtest.db --tokens 200000
```

Then:

```
sqlite3 bigtest.db ".load ./build/macos/postings.dylib" ".read test_queries.sql"
```
