# Database Design for Quantum Paper Summarizer

## Overview
This document outlines the database structure for storing quantum physics research papers and their summaries. The database will support automatic updates while retaining all historical data.

## Database Choice: SQLite
SQLite is chosen for this application because:
- It's lightweight and file-based (no separate server required)
- Easy to set up and maintain
- Good performance for our expected data volume
- Simple integration with Python and Flask
- Portable (the entire database is stored in a single file)

## Schema Design

### Tables

#### 1. Papers
Stores the core information about each paper.

```sql
CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    published_date TIMESTAMP NOT NULL,
    entry_url TEXT NOT NULL,
    pdf_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. Authors
Stores information about paper authors.

```sql
CREATE TABLE authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    UNIQUE(name)
);
```

#### 3. PaperAuthors
Junction table for the many-to-many relationship between papers and authors.

```sql
CREATE TABLE paper_authors (
    paper_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    author_position INTEGER NOT NULL,
    PRIMARY KEY (paper_id, author_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
);
```

#### 4. Categories
Stores arXiv categories.

```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_code TEXT UNIQUE NOT NULL,
    category_name TEXT
);
```

#### 5. PaperCategories
Junction table for the many-to-many relationship between papers and categories.

```sql
CREATE TABLE paper_categories (
    paper_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (paper_id, category_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);
```

#### 6. Abstracts
Stores the original abstracts of papers.

```sql
CREATE TABLE abstracts (
    paper_id INTEGER PRIMARY KEY,
    abstract_text TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);
```

#### 7. FullTexts
Stores the extracted full text content of papers.

```sql
CREATE TABLE full_texts (
    paper_id INTEGER PRIMARY KEY,
    full_text TEXT NOT NULL,
    extraction_status TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);
```

#### 8. Summaries
Stores both brief and extended summaries of papers.

```sql
CREATE TABLE summaries (
    paper_id INTEGER PRIMARY KEY,
    brief_summary TEXT NOT NULL,
    extended_summary TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);
```

## Indexes
To optimize query performance:

```sql
CREATE INDEX idx_papers_published_date ON papers(published_date DESC);
CREATE INDEX idx_papers_arxiv_id ON papers(arxiv_id);
CREATE INDEX idx_paper_authors_paper_id ON paper_authors(paper_id);
CREATE INDEX idx_paper_authors_author_id ON paper_authors(author_id);
CREATE INDEX idx_paper_categories_paper_id ON paper_categories(paper_id);
CREATE INDEX idx_paper_categories_category_id ON paper_categories(category_id);
```

## Sample Queries

### Get the 10 most recent papers with their summaries
```sql
SELECT p.id, p.arxiv_id, p.title, p.published_date, s.brief_summary
FROM papers p
JOIN summaries s ON p.id = s.paper_id
ORDER BY p.published_date DESC
LIMIT 10;
```

### Get a specific paper with all its details
```sql
SELECT p.id, p.arxiv_id, p.title, p.published_date, p.entry_url, p.pdf_url,
       a.abstract_text, s.brief_summary, s.extended_summary
FROM papers p
JOIN abstracts a ON p.id = a.paper_id
JOIN summaries s ON p.id = s.paper_id
WHERE p.arxiv_id = ?;
```

### Get all authors for a paper
```sql
SELECT a.name
FROM authors a
JOIN paper_authors pa ON a.id = pa.author_id
WHERE pa.paper_id = ?
ORDER BY pa.author_position;
```

### Get all categories for a paper
```sql
SELECT c.category_code, c.category_name
FROM categories c
JOIN paper_categories pc ON c.id = pc.category_id
WHERE pc.paper_id = ?;
```

### Check if a paper already exists in the database
```sql
SELECT id FROM papers WHERE arxiv_id = ?;
```

## Data Migration Strategy
To migrate from the current static implementation to this database:
1. Create the database schema
2. Parse the existing JSON files containing paper data
3. Insert the data into the appropriate tables
4. Verify data integrity after migration

This database design will support the automatic updating functionality while maintaining all historical paper data as required.
