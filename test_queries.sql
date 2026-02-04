-- Load extension (adjust path if needed)
-- .load ./build/macos/postings.dylib

-- Check JSON1 availability
SELECT json_array(1, 2, 3);

-- All positions for a word
SELECT post_positions(p.blob) AS positions_json
FROM postings p
WHERE p.bok_id = 1 AND p.word = 'demokrati';

-- Positions in A that are near B within window
SELECT post_near_positions(a.blob, b.blob, -5, 5) AS near_positions_json
FROM postings a
JOIN postings b USING (bok_id)
WHERE a.bok_id = 1 AND a.word = 'demokrati' AND b.word = 'diktatur';

-- Example concordance: tokens around each occurrence of "demokrati" (+/- 3)
WITH pos AS (
  SELECT je.value AS seq
  FROM postings p,
       json_each(post_positions(p.blob)) AS je
  WHERE p.bok_id = 1 AND p.word = 'demokrati'
)
SELECT t.seq, t.word
FROM pos
JOIN tokens t
  ON t.bok_id = 1
 AND t.seq BETWEEN pos.seq - 3 AND pos.seq + 3
ORDER BY t.seq;

-- Sampled concordance: pick 5 random occurrences of a word (+/- 3)
WITH sampled AS (
  SELECT je.value AS seq
  FROM postings p,
       json_each(post_positions(p.blob)) AS je
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
