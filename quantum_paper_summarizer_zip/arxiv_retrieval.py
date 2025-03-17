import os
import sqlite3
import arxiv
import time
from datetime import datetime, timedelta

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quantum_papers.db')

def create_database():
    """Create the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
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
    
    CREATE INDEX IF NOT EXISTS idx_papers_published_date ON papers(published_date DESC);
    CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id);
    CREATE INDEX IF NOT EXISTS idx_paper_authors_paper_id ON paper_authors(paper_id);
    CREATE INDEX IF NOT EXISTS idx_paper_authors_author_id ON paper_authors(author_id);
    CREATE INDEX IF NOT EXISTS idx_paper_categories_paper_id ON paper_categories(paper_id);
    CREATE INDEX IF NOT EXISTS idx_paper_categories_category_id ON paper_categories(category_id);
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database created at {DB_PATH}")

def get_or_create_category(conn, category_code):
    """Get a category ID or create it if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE category_code = ?", (category_code,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    cursor.execute("INSERT INTO categories (category_code) VALUES (?)", (category_code,))
    return cursor.lastrowid

def get_or_create_author(conn, author_name):
    """Get an author ID or create it if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM authors WHERE name = ?", (author_name,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    cursor.execute("INSERT INTO authors (name) VALUES (?)", (author_name,))
    return cursor.lastrowid

def paper_exists(conn, arxiv_id):
    """Check if a paper already exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM papers WHERE arxiv_id = ?", (arxiv_id,))
    return cursor.fetchone() is not None

def store_paper(conn, paper):
    """Store a paper and its related data in the database."""
    if paper_exists(conn, paper.entry_id):
        print(f"Paper {paper.entry_id} already exists in the database. Skipping.")
        return None
    
    cursor = conn.cursor()
    
    # Insert paper
    cursor.execute("""
    INSERT INTO papers (arxiv_id, title, published_date, entry_url, pdf_url)
    VALUES (?, ?, ?, ?, ?)
    """, (
        paper.entry_id,
        paper.title,
        paper.published.isoformat(),
        paper.entry_id,
        paper.pdf_url
    ))
    paper_id = cursor.lastrowid
    
    # Insert abstract
    cursor.execute("INSERT INTO abstracts (paper_id, abstract_text) VALUES (?, ?)",
                  (paper_id, paper.summary))
    
    # Insert categories
    for category in paper.categories:
        category_id = get_or_create_category(conn, category)
        cursor.execute("INSERT INTO paper_categories (paper_id, category_id) VALUES (?, ?)",
                      (paper_id, category_id))
    
    # Insert authors
    for i, author in enumerate(paper.authors):
        author_id = get_or_create_author(conn, author.name)
        cursor.execute("INSERT INTO paper_authors (paper_id, author_id, author_position) VALUES (?, ?, ?)",
                      (paper_id, author_id, i))
    
    return paper_id

def retrieve_recent_papers(max_results=10):
    """
    Retrieve recent papers from arXiv's quant-ph category and store them in the database.
    
    Args:
        max_results (int): Maximum number of papers to retrieve
        
    Returns:
        int: Number of new papers stored
    """
    # Create database if it doesn't exist
    if not os.path.exists(DB_PATH):
        create_database()
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Search for papers in quant-ph category
        print(f"Searching for papers in the quant-ph category...")
        
        client = arxiv.Client()
        search = arxiv.Search(
            query='cat:quant-ph',
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        papers = []
        for result in client.results(search):
            papers.append(result)
            # Be nice to the API with a small delay
            time.sleep(0.1)
        
        if not papers:
            print("No papers found.")
            log_retrieval(conn, 0, "success", "No papers found")
            return 0
        
        print(f"Found {len(papers)} papers. Processing...")
        
        # Process each paper
        new_papers_count = 0
        for paper in papers:
            paper_id = store_paper(conn, paper)
            if paper_id:
                new_papers_count += 1
                print(f"Stored paper: {paper.title}")
        
        conn.commit()
        
        # Log the retrieval
        log_retrieval(conn, new_papers_count, "success", f"Retrieved {new_papers_count} new papers")
        
        print(f"Stored {new_papers_count} new papers in the database.")
        return new_papers_count
        
    except Exception as e:
        conn.rollback()
        error_message = f"Error retrieving papers: {str(e)}"
        print(error_message)
        log_retrieval(conn, 0, "error", error_message)
        return 0
    
    finally:
        conn.close()

def log_retrieval(conn, papers_retrieved, status, message):
    """Log the retrieval run in the database."""
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO retrieval_log (papers_retrieved, status, message)
    VALUES (?, ?, ?)
    """, (papers_retrieved, status, message))
    conn.commit()

def get_last_retrieval_date():
    """Get the date of the last successful retrieval."""
    if not os.path.exists(DB_PATH):
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT run_date FROM retrieval_log 
    WHERE status = 'success' AND papers_retrieved > 0
    ORDER BY run_date DESC LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return datetime.fromisoformat(result[0])
    return None

def should_run_retrieval(hours_between_runs=24):
    """Determine if we should run the retrieval based on the last run time."""
    last_run = get_last_retrieval_date()
    
    if not last_run:
        return True
    
    time_since_last_run = datetime.now() - last_run
    return time_since_last_run > timedelta(hours=hours_between_runs)

if __name__ == "__main__":
    if should_run_retrieval():
        print("Starting scheduled paper retrieval...")
        retrieve_recent_papers(max_results=20)
    else:
        last_run = get_last_retrieval_date()
        print(f"Skipping retrieval. Last successful run was at {last_run}.")
