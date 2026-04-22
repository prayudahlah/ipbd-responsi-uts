import os

os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"

import requests
import psycopg2
from psycopg2.extras import execute_values
from prefect import flow, task

DB_CONFIG = "postgresql://postgres:postgres@localhost:5432/wired_articles"
API_URL = "http://localhost:8000/articles"


@task(name="Extract articles", retries=3, retry_delay_seconds=5)
def extract_articles():
    response = requests.get(f"{API_URL}", timeout=30)
    response.raise_for_status()
    articles = response.json()

    print(f"Extracted {len(articles)} articles")
    return articles


@task(name="Transform articles")
def transform_articles(articles):
    articles_data = []
    author_relations = []

    for article in articles:
        articles_data.append(
            (
                article.get("title"),
                article.get("date"),
                article.get("link"),
                article.get("description"),
            )
        )

        authors = article.get("authors", [])

        for author in authors:
            author_relations.append(
                {"article_link": article.get("link"), "author_name": author}
            )
    return articles_data, author_relations


@task(name="Load articles to database", retries=3, retry_delay_seconds=10)
def load_articles(articles_data):
    if not articles_data:
        return []

    conn = None
    try:
        conn = psycopg2.connect(DB_CONFIG)
        cur = conn.cursor()

        execute_values(
            cur,
            """
            INSERT INTO articles (title, date, link, description)
            VALUES %s
            ON CONFLICT (link) DO UPDATE SET
                title = EXCLUDED.title,
                date = EXCLUDED.date,
                description = EXCLUDED.description
            RETURNING article_id, link
            """,
            articles_data,
            template="(%s, %s, %s, %s)",
        )

        inserted = cur.fetchall()
        conn.commit()

        # Return list dari tuple (article_id, link)
        result = [(row[0], row[1]) for row in inserted]
        print(f"Loaded/Updated {len(result)} articles")
        return result

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()


@task(name="Load authors and relations", retries=3, retry_delay_seconds=10)
def load_authors_and_relations(author_relations, article_map):
    if not author_relations:
        print("No authors to load")
        return 0

    conn = None
    try:
        conn = psycopg2.connect(DB_CONFIG)
        cur = conn.cursor()

        unique_authors = set()
        for rel in author_relations:
            unique_authors.add(rel["author_name"])

        # Insert authors
        author_data = [(name,) for name in unique_authors]
        execute_values(
            cur,
            """
            INSERT INTO authors (name)
            VALUES %s
            ON CONFLICT (name) DO NOTHING
            """,
            author_data,
            template="(%s)",
        )

        cur.execute("SELECT name, author_id FROM authors")
        author_ids = {name: author_id for name, author_id in cur.fetchall()}

        # Untuk junction table (written_by)
        relations_data = []
        for rel in author_relations:
            article_id = article_map.get(rel["article_link"])
            author_id = author_ids.get(rel["author_name"])
            if article_id and author_id:
                relations_data.append((article_id, author_id))

        if relations_data:
            execute_values(
                cur,
                """
                INSERT INTO written_by (article_id, author_id)
                VALUES %s
                ON CONFLICT (article_id, author_id) DO NOTHING
                """,
                relations_data,
                template="(%s, %s)",
            )

        conn.commit()
        print(
            f"Loaded {len(unique_authors)} authors and {len(relations_data)} relations"
        )
        return len(relations_data)

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()


@flow(name="WIRED ETL Flow", log_prints=True)
def etl_flow():
    print(f"API URL: {API_URL}")

    # 1. Extract
    raw_articles = extract_articles()

    # 2. Transform
    articles_data, author_relations = transform_articles(raw_articles)

    # 3. Load ke tabel articles
    inserted_articles = load_articles(articles_data)

    # Buat mapping link -> article_id
    article_map = {link: article_id for article_id, link in inserted_articles}

    # 4. Load authors dan relasi
    relations_count = load_authors_and_relations(author_relations, article_map)

    # 5. Summary
    print("[SUKSES] ETL berhasil dijalankan!")
    print(f"Extracted: {len(raw_articles)}")
    print(f"Articles loaded: {len(inserted_articles)}")
    print(f"Authors & relations: {relations_count}")

    return {
        "extracted": len(raw_articles),
        "articles_loaded": len(inserted_articles),
        "relations_created": relations_count,
    }


if __name__ == "__main__":
    etl_flow.serve(
        name="wired-etl",
        parameters={},
    )
