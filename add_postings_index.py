#!/usr/bin/env python3
import argparse
import glob
import sqlite3


def add_index(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE INDEX IF NOT EXISTS postings_word_bok_id ON postings(word, bok_id)")
    conn.commit()
    conn.close()
    print(f"Indexed: {db_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add postings(word, bok_id) index to postings DBs."
    )
    parser.add_argument("--glob", required=True, help="Glob for postings DBs")
    args = parser.parse_args()

    for path in sorted(glob.glob(args.glob)):
        add_index(path)


if __name__ == "__main__":
    main()
