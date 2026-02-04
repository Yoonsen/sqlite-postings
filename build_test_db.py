#!/usr/bin/env python3
import argparse
import random
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


def delta_varint_encode(positions):
    out = bytearray()
    last = 0
    for pos in positions:
        delta = pos - last
        if delta < 0:
            raise ValueError("positions must be sorted ascending")
        out.extend(varint_encode(delta))
        last = pos
    return bytes(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="test.db", help="Output sqlite db path")
    parser.add_argument("--tokens", type=int, default=20000, help="Total token count")
    parser.add_argument("--bok-id", type=int, default=1, help="Book id")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    db_path = args.db
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(
        """
        DROP TABLE IF EXISTS tokens;
        DROP TABLE IF EXISTS postings;

        CREATE TABLE tokens (
            bok_id INTEGER NOT NULL,
            seq INTEGER NOT NULL,
            word TEXT NOT NULL,
            PRIMARY KEY (bok_id, seq)
        );

        CREATE TABLE postings (
            bok_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            blob BLOB NOT NULL,
            PRIMARY KEY (bok_id, word)
        );
        """
    )

    bok_id = args.bok_id
    random.seed(args.seed)

    # Small fixed vocab + a few high-frequency targets
    vocab = [
        "demokrati",
        "diktatur",
        "frihet",
        "ansvar",
        "makt",
        "stat",
        "folk",
        "rett",
        "lov",
        "krig",
        "fred",
        "by",
        "land",
        "hav",
        "tid",
        "rom",
    ]
    common = ["og", "i", "det", "er", "som", "til", "på", "for", "med", "ikke"]
    weighted = vocab + (common * 8) + (["demokrati"] * 6) + (["diktatur"] * 3)

    words = [random.choice(weighted) for _ in range(args.tokens)]

    for i, w in enumerate(words, start=1):
        cur.execute(
            "INSERT INTO tokens (bok_id, seq, word) VALUES (?, ?, ?)",
            (bok_id, i, w),
        )

    positions_by_word = {}
    for i, w in enumerate(words, start=1):
        positions_by_word.setdefault(w, []).append(i)

    for w, positions in positions_by_word.items():
        blob = delta_varint_encode(positions)
        cur.execute(
            "INSERT INTO postings (bok_id, word, blob) VALUES (?, ?, ?)",
            (bok_id, w, blob),
        )

    conn.commit()
    conn.close()
    print(f"Created {db_path} with {len(words)} tokens and {len(positions_by_word)} postings.")


if __name__ == "__main__":
    main()
