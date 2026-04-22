CREATE TABLE articles (
    article_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR,
    date TIMESTAMP,
    link VARCHAR UNIQUE,
    description TEXT
);

CREATE TABLE authors (
    author_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR UNIQUE
);

CREATE TABLE written_by (
    article_id INT REFERENCES articles(article_id),
    author_id INT REFERENCES authors(author_id),

    PRIMARY KEY (article_id, author_id)
)