#!/usr/bin/env python3
import argparse
import sqlite3


def varint_encode(n: int) -> bytes:
    if n < 0:
        raise ValueError("varint only supports non-negative integers")
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert ft(urn, word, seq, ...) to tokens/postings tables."
    )
    parser.add_argument("--src", required=True, help="Source SQLite path")
    parser.add_argument("--dst", required=True, help="Output SQLite path")
    parser.add_argument("--urn", type=int, help="Filter by urn/bok_id")
    parser.add_argument("--word", help="Filter by word")
    parser.add_argument("--limit", type=int, help="Limit number of rows")
    parser.add_argument("--batch", type=int, default=10000, help="Insert batch size")
    args = parser.parse_args()

    src = sqlite3.connect(args.src)
    dst = sqlite3.connect(args.dst)

    dst.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = OFF;
        PRAGMA temp_store = MEMORY;
        PRAGMA cache_size = 200000;

        DROP TABLE IF EXISTS tokens;
        DROP TABLE IF EXISTS postings;

        CREATE TABLE tokens (
            bok_id INTEGER NOT NULL,
            seq INTEGER NOT NULL,
            word TEXT NOT NULL,
            PRIMARY KEY (bok_id, seq)
        ) WITHOUT ROWID;

        CREATE TABLE postings (
            bok_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            blob BLOB NOT NULL,
            PRIMARY KEY (bok_id, word)
        ) WITHOUT ROWID;

        CREATE INDEX postings_word_bok_id ON postings(word, bok_id);

        CREATE TABLE urns (
            bok_id INTEGER NOT NULL PRIMARY KEY
        ) WITHOUT ROWID;
        """
    )

    where = []
    params = []
    if args.urn is not None:
        where.append("urn = ?")
        params.append(args.urn)
    if args.word is not None:
        where.append("word = ?")
        params.append(args.word)

    sql = "SELECT urn, word, seq FROM ft"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY urn, word, seq"
    if args.limit:
        sql += " LIMIT ?"
        params.append(args.limit)

    src_cur = src.cursor()
    dst_cur = dst.cursor()
    src_cur.execute(sql, params)

    tokens_batch = []
    current_urn = None
    current_word = None
    last_pos = 0
    blob = bytearray()
    postings_count = 0
    rows_count = 0
    urns_count = 0

    def flush_tokens() -> None:
        if not tokens_batch:
            return
        dst_cur.executemany(
            "INSERT INTO tokens (bok_id, seq, word) VALUES (?, ?, ?)",
            tokens_batch,
        )
        tokens_batch.clear()

    def flush_posting() -> None:
        nonlocal postings_count
        if current_urn is None:
            return
        dst_cur.execute(
            "INSERT INTO postings (bok_id, word, blob) VALUES (?, ?, ?)",
            (current_urn, current_word, bytes(blob)),
        )
        postings_count += 1

    def insert_urn(urn: int) -> None:
        nonlocal urns_count
        dst_cur.execute("INSERT OR IGNORE INTO urns (bok_id) VALUES (?)", (urn,))
        urns_count += 1

    for urn, word, seq in src_cur:
        rows_count += 1
        tokens_batch.append((urn, seq, word))
        if len(tokens_batch) >= args.batch:
            flush_tokens()

        if (urn != current_urn) or (word != current_word):
            flush_posting()
            current_urn = urn
            current_word = word
            last_pos = 0
            blob = bytearray()
            insert_urn(urn)

        delta = seq - last_pos
        if delta < 0:
            raise ValueError("seq must be non-decreasing within a word")
        blob.extend(varint_encode(delta))
        last_pos = seq

    flush_tokens()
    flush_posting()

    dst.commit()
    dst.close()
    src.close()

    print(
        f"Converted {rows_count} rows into tokens, {postings_count} postings, "
        f"and {urns_count} urns."
    )


if __name__ == "__main__":
    main()
