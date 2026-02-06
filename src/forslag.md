Vi har en fungerende SQLite C-extension i src/postings.c (postings-baserte funksjoner).
Ikke endre eksisterende API eller wire-up, men utvid den med rene INT-varianter for nærhet
som ikke går via JSON, og samtidig gjør det litt mer effektivt for små BLOB-er.

Mål:

1. Behold alle eksisterende funksjoner uendret:
   - post_intersect
   - post_intersect_offset
   - post_intersect_offset_sym
   - post_sample
   - post_positions
   - post_near_positions

2. Legg til én ny funksjon:
   - post_near_count(blobA, blobB, off_min, off_max) -> INT
   Denne skal:
   - bruke samme semantikk som post_near_positions:
     * A og B er varint/delta-kodede postings-lister
     * off_min, off_max er heltall
     * teller antall posisjoner i A der det finnes minst én posisjon i B
       slik at (seq_b - seq_a) er i [off_min, off_max]
   - implementeres som en ren C-loop uten å bygge JSON
   - returnere samlet count som sqlite3_result_int

   Tenk på denne som en "count-only"-variant av post_near_positions.

3. Registrer UDF-en i sqlite3_postings_init:
   sqlite3_create_function(
       db, "post_near_count", 4,
       SQLITE_UTF8 | SQLITE_DETERMINISTIC,
       NULL, post_near_count_sqlite, NULL, NULL
   );

4. Optimalisering for små BLOB-er (valgfritt, men ønskelig):
   I både post_near_count og post_intersect_offset (og eventuelt _sym), legg inn en enkel
   "fast path" for veldig korte postings-lister, f.eks. hvis antall elementer er lite
   eller BLOB-lengden er under en terskel. Krav:
   - Ikke endre på varint/delta-formatet.
   - Bruk bare en enklere tight loop der du slipper ekstra branching.
   - Hold koden lesbar; ikke gjør micro-optimalisering som forverrer klarheten for mye.

5. Bevar hjelpefunksjonene:
   - read_varint
   - next_seq
   - json_append_* osv.
   Du kan legge til nye interne hjelpefunksjoner dersom det gjør koden ryddigere.

6. Kodekrav:
   - Ingen nye eksterne dependencies.
   - Ingen printf/logging.
   - Husk å håndtere NULL/0-lengde BLOB på samme måte som de andre funksjonene
     (returner 0 for post_near_count).
   - Følg samme stil og error-håndtering som resten av fila (sqlite3_result_error ved feil input).

Oppsummert:
- Ikke rør eksisterende funksjonssignaturer eller navn.
- Legg til post_near_count_sqlite (INT-returnerende) og registrer den.
- Gjerne legg inn en liten fast-path for korte BLOB-er der det er naturlig.
- Hold alt konsistent med dagens stil og hjelpefunksjoner i src/postings.c.
