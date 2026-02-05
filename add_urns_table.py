#!/usr/bin/env python3
import argparse
import glob
import sqlite3


def add_urns(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS urns (
            bok_id INTEGER NOT NULL PRIMARY KEY
        ) WITHOUT ROWID
        """
    )
    cur.execute("INSERT OR IGNORE INTO urns (bok_id) SELECT DISTINCT bok_id FROM postings")
    conn.commit()
    conn.close()
    print(f"URNs added: {db_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add urns table to postings DBs."
    )
    parser.add_argument("--glob", required=True, help="Glob for postings DBs")
    args = parser.parse_args()

    for path in sorted(glob.glob(args.glob)):
        add_urns(path)


if __name__ == "__main__":
    main()
