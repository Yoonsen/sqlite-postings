## Full Conversion (ft -> tokens/postings)

### Purpose
Convert `ft(urn, word, seq, ...)` from the `alto_*.db` shards into the demo
schema used by this repo:

- `tokens(bok_id, seq, word) WITHOUT ROWID`
- `postings(bok_id, word, blob) WITHOUT ROWID` (delta+varint positions)

### Scripts

- Single DB / filtered:
  - `convert_ft_to_postings.py`
- All shards:
  - `convert_all_ft.py`

### Output location

All converted shards are written to:

```
/mnt/disk1/alto_postings/
```

Naming convention:

```
alto_XXXXXXXX_YYYYYYYY_postings.db
```

### Run full conversion

```
python3 convert_all_ft.py
```

Optional parameters:

```
python3 convert_all_ft.py --glob "/mnt/disk1/alto_*.db" --out-dir "/mnt/disk1/alto_postings" --batch 10000
```

### Run single DB conversion

```
python3 convert_ft_to_postings.py \
  --src /mnt/disk1/alto_100000000_100019999.db \
  --dst demo_ft.db \
  --urn 100004670
```

### Quick sanity check

```
sqlite3 demo_ft.db ".load ./build/linux/postings.so" \
"SELECT post_intersect_offset(a.blob,b.blob,-5,5)
 FROM postings a JOIN postings b USING (bok_id)
 WHERE a.word='A' AND b.word='D';"
```

### Streamlit demo

```
streamlit run streamlit_app.py
```

The app lets you:
- run postings proximity (`post_intersect_offset`)
- run concordance sampling
- compare against FTS5 `NEAR` (optional; uses original `alto_*.db`)
