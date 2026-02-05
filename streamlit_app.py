#!/usr/bin/env python3
import json
import sqlite3
import time

import streamlit as st


def open_postings_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    conn.load_extension("build/linux/postings.so")
    return conn


def ensure_random_bok_ids(db_path: str, count: int) -> list[int]:
    if st.session_state.get("bok_ids"):
        return st.session_state["bok_ids"]
    conn = open_postings_db(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT bok_id FROM urns ORDER BY random() LIMIT ?", (count,))
    except sqlite3.Error:
        cur.execute(
            "SELECT DISTINCT bok_id FROM tokens ORDER BY random() LIMIT ?",
            (count,),
        )
    st.session_state["bok_ids"] = [row[0] for row in cur.fetchall()]
    conn.close()
    return st.session_state["bok_ids"]


st.set_page_config(page_title="SQLite Postings Demo", layout="wide")
st.title("SQLite Postings Demo")
st.markdown(
    """
Dette er en praktisk sammenligning mellom **postings‑basert nærhetssøk**
og **FTS5 NEAR** på samme korpus.

- Resten av backend‑designet er fra 2016.
- FTS5 ble lagt til i 2019/20 for fulltekst.
- Treffer kan avvike mellom metodene pga. ulik tokenisering/normalisering.
"""
)

st.sidebar.header("Databaser")
postings_db = st.sidebar.text_input(
    "Postings DB", value="/mnt/disk1/alto_postings/alto_100000000_100019999_postings.db"
)
fts_db = st.sidebar.text_input(
    "FTS5 DB", value="/mnt/disk1/alto_100000000_100019999.db"
)

st.sidebar.header("Parametre")
corpus_size = 1000
word_a = st.sidebar.text_input("Word A", value="A")
word_b = st.sidebar.text_input("Word B", value="D")
off_min = st.sidebar.number_input("off_min", value=-5)
off_max = st.sidebar.number_input("off_max", value=5)
sample_n = 10
window = 20

if "bok_ids" not in st.session_state:
    st.session_state["bok_ids"] = []
if "bok_ids_size" not in st.session_state:
    st.session_state["bok_ids_size"] = None
if "near_positions" not in st.session_state:
    st.session_state["near_positions"] = []
if "near_bok_id" not in st.session_state:
    st.session_state["near_bok_id"] = None

if st.session_state.get("bok_ids_size") != corpus_size:
    st.session_state["bok_ids"] = []
    st.session_state["bok_ids_size"] = corpus_size

if st.sidebar.button("Lag korpus (tilfeldig bok_id‑liste)"):
    try:
        st.session_state["bok_ids"] = []
        ids = ensure_random_bok_ids(postings_db, corpus_size)
        st.sidebar.caption(f"Aktivt utvalg: {len(ids)} bok_id")
    except Exception as exc:
        st.sidebar.error(f"Feil: {exc}")
elif st.session_state["bok_ids"]:
    st.sidebar.caption(f"Aktivt utvalg: {len(st.session_state['bok_ids'])} bok_id")
else:
    st.sidebar.caption("Aktivt utvalg: 0 bok_id")

run_compare = st.button("Kjør sammenligning")
bok_ids = st.session_state["bok_ids"]
if run_compare and not bok_ids:
    bok_ids = ensure_random_bok_ids(postings_db, corpus_size)
    st.session_state["bok_ids"] = bok_ids

left, right = st.columns(2)

with left:
    st.subheader("Postings: nærhetssøk")
    if run_compare:
        try:
            conn = open_postings_db(postings_db)
            cur = conn.cursor()
            bok_ids = st.session_state["bok_ids"] or None
            if not bok_ids:
                bok_ids = ensure_random_bok_ids(postings_db, corpus_size)

            placeholders = ",".join("?" for _ in bok_ids)
            t0 = time.perf_counter()
            sql_hits = f"""
                SELECT bok_id, hits
                FROM (
                  SELECT a.bok_id,
                         post_intersect_offset_sym(a.blob, b.blob, ?, ?) AS hits
                  FROM postings a
                  JOIN postings b USING (bok_id)
                  WHERE a.word = ? AND b.word = ?
                    AND a.bok_id IN ({placeholders})
                )
                WHERE hits > 0
                ORDER BY hits DESC
            """
            params = [off_min, off_max, word_a, word_b] + bok_ids
            sql_len = f"""
                SELECT
                  AVG(length(a.blob)) AS avg_a,
                  AVG(length(b.blob)) AS avg_b
                FROM postings a
                JOIN postings b USING (bok_id)
                WHERE a.word = ? AND b.word = ?
                  AND a.bok_id IN ({placeholders})
            """
            cur.execute(sql_len, [word_a, word_b] + bok_ids)
            row_len = cur.fetchone()
            cur.execute(sql_hits, params)
            hits_rows = cur.fetchall()
            elapsed = time.perf_counter() - t0
            if row_len and row_len[0] is not None and row_len[1] is not None:
                st.write(f"Snitt blob‑lengde: a={row_len[0]:.1f}, b={row_len[1]:.1f}")
            st.write(f"Bøker i korpus: {len(bok_ids)}")
            st.write(f"Treff (bøker): {len(hits_rows)}")
            st.write(f"Tid (total): {elapsed:.3f} s")
            if hits_rows:
                st.dataframe(hits_rows, use_container_width=True)
                top_bok = hits_rows[0][0]
                cur.execute(
                    """
                    SELECT je.value
                    FROM postings a
                    JOIN postings b USING (bok_id),
                         json_each(post_near_positions(a.blob, b.blob, ?, ?)) AS je
                    WHERE a.word = ? AND b.word = ? AND a.bok_id = ?
                    LIMIT 10
                    """,
                    (off_min, off_max, word_a, word_b, top_bok),
                )
                st.session_state["near_positions"] = [r[0] for r in cur.fetchall()]
                st.session_state["near_bok_id"] = top_bok
            else:
                st.write("Ingen treff.")
            conn.close()
        except Exception as exc:
            st.error(f"Feil: {exc}")

st.subheader("Postings: konkordans")
if st.button("Kjør konkordans"):
    try:
        conn = open_postings_db(postings_db)
        cur = conn.cursor()
        target_bok = st.session_state.get("near_bok_id")
        positions = st.session_state.get("near_positions", [])
        if target_bok is None or not positions:
            st.write("Kjør først nærhetssøk for å hente 10 treff.")
            conn.close()
            target_bok = None
        if target_bok is not None:
            if positions and st.session_state.get("near_bok_id") == target_bok:
                positions_json = json.dumps(positions)
                cur.execute(
                    f"""
                    SELECT s.seq AS hit_seq, t.seq, t.word
                    FROM (
                      SELECT value AS seq
                      FROM json_each(?)
                      LIMIT {int(sample_n)}
                    ) AS s
                    JOIN tokens t
                      ON t.bok_id = ?
                     AND t.seq BETWEEN s.seq - ? AND s.seq + ?
                    ORDER BY s.seq, t.seq
                    """,
                    (positions_json, target_bok, window, window),
                )
            rows = cur.fetchall()
            if rows:
                st.dataframe(rows, use_container_width=True)
            else:
                st.write("Ingen rader.")
        conn.close()
    except Exception as exc:
        st.error(f"Feil: {exc}")

with right:
    st.subheader("FTS5: NEAR‑søk")
    if run_compare:
        if not fts_db:
            st.warning("Oppgi en FTS5‑DB.")
        else:
            try:
                conn = sqlite3.connect(fts_db)
                cur = conn.cursor()
                distance = abs(off_max)
                query = f'NEAR("{word_a}" "{word_b}", {distance})'
                placeholders = ",".join("?" for _ in bok_ids)
                t0 = time.perf_counter()
                sql_hits = (
                    f"SELECT urn, COUNT(*) AS hits FROM ft_para "
                    f"WHERE ft_para MATCH ? AND urn IN ({placeholders}) "
                    f"GROUP BY urn ORDER BY hits DESC"
                )
                params = [query] + bok_ids
                cur.execute(sql_hits, params)
                hits_rows = cur.fetchall()
                elapsed = time.perf_counter() - t0
                st.write(f"Bøker i korpus: {len(bok_ids)}")
                st.write(f"Treff (bøker): {len(hits_rows)}")
                st.write(f"Tid (total): {elapsed:.3f} s")
                if hits_rows:
                    st.dataframe(hits_rows, use_container_width=True)
                else:
                    st.write("Ingen treff.")
                conn.close()
            except Exception as exc:
                st.error(f"Feil: {exc}")
