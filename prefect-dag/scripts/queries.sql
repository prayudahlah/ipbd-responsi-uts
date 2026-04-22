-- PRAYUDA AFIFAN HANDOYO
-- L0224008
-- KELAS A - SAINS DATA '24

-- 1. Tampilkan judul artikel dan nama author yang sudah dibersihkan dari kata "By" di depannya.
SELECT
    a.article_id AS article_id,
    a.title AS article_titles,
    STRING_AGG(a2.name, ', ' ORDER BY a2.name) AS authors
FROM articles a
     JOIN written_by wb ON a.article_id = wb.article_id
     JOIN authors a2 ON a2.author_id = wb.author_id
GROUP BY a.article_id, a.title;

-- 2. Tampilkan 3 nama penulis yang paling sering muncul dalam database hasil scrape kalian.
WITH top_3_author_ids AS (
    SELECT
        wb.author_id,
        COUNT(wb.author_id) AS articles_amount
    FROM written_by wb
    GROUP BY wb.author_id
    ORDER BY articles_amount DESC
    LIMIT 3
)
SELECT
    a.name AS author,
    t3.articles_amount AS articles_amount
FROM top_3_author_ids t3
     JOIN authors a ON a.author_id = t3.author_id
ORDER BY t3.articles_amount DESC;


-- 3. Cari artikel yang mengandung kata kunci "AI", "Climate", atau "Security" pada judul atau deskripsi
SELECT *
FROM articles a
WHERE
    a.title ILIKE ANY(ARRAY['%ai%', '%climate%', '%security%'])
    OR a.description ILIKE ANY(ARRAY['%ai%', '%climate%', '%security%']);
