#!/usr/bin/env python3
"""
Database initialization script for Quantum Paper Summarizer.
This script creates the SQLite database and all required tables.
"""

import os
import sqlite3
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("db_init.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quantum_papers.db')

def create_database():
    """Create the database and tables if they don't exist."""
    logger.info(f"Creating database at {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    logger.info("Creating database tables...")
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        arxiv_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        published_date TIMESTAMP NOT NULL,
        entry_url TEXT NOT NULL,
        pdf_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        UNIQUE(name)
    );
    
    CREATE TABLE IF NOT EXISTS paper_authors (
        paper_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        author_position INTEGER NOT NULL,
        PRIMARY KEY (paper_id, author_id),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_code TEXT UNIQUE NOT NULL,
        category_name TEXT
    );
    
    CREATE TABLE IF NOT EXISTS paper_categories (
        paper_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        PRIMARY KEY (paper_id, category_id),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS abstracts (
        paper_id INTEGER PRIMARY KEY,
        abstract_text TEXT NOT NULL,
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS full_texts (
        paper_id INTEGER PRIMARY KEY,
        full_text TEXT NOT NULL,
        extraction_status TEXT NOT NULL,
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS summaries (
        paper_id INTEGER PRIMARY KEY,
        brief_summary TEXT NOT NULL,
        extended_summary TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS retrieval_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        papers_retrieved INTEGER,
        status TEXT,
        message TEXT
    );
    ''')
    
    # Create indexes
    logger.info("Creating database indexes...")
    cursor.executescript('''
    CREATE INDEX IF NOT EXISTS idx_papers_published_date ON papers(published_date DESC);
    CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id);
    CREATE INDEX IF NOT EXISTS idx_paper_authors_paper_id ON paper_authors(paper_id);
    CREATE INDEX IF NOT EXISTS idx_paper_authors_author_id ON paper_authors(author_id);
    CREATE INDEX IF NOT EXISTS idx_paper_categories_paper_id ON paper_categories(paper_id);
    CREATE INDEX IF NOT EXISTS idx_paper_categories_category_id ON paper_categories(category_id);
    ''')
    
    conn.commit()
    conn.close()
    
    logger.info(f"Database created successfully at {DB_PATH}")
    return True

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        logger.warning(f"Database already exists at {DB_PATH}")
        user_input = input("Database already exists. Do you want to recreate it? (y/N): ")
        if user_input.lower() == 'y':
            os.remove(DB_PATH)
            logger.info(f"Removed existing database at {DB_PATH}")
            create_database()
        else:
            logger.info("Database initialization cancelled by user")
    else:
        create_database()
