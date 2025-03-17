from flask import Flask, render_template, request, jsonify, abort
import sqlite3
import os
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import arxiv_retrieval
import paper_processor
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webapp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quantum_papers.db')

# Initialize Flask app
app = Flask(__name__)

# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

# Helper function to format date
def format_date(date_str):
    try:
        date_obj = datetime.fromisoformat(date_str)
        return date_obj.strftime('%B %d, %Y')
    except:
        return date_str

# Schedule background tasks
def schedule_tasks():
    scheduler = BackgroundScheduler()
    
    # Schedule paper retrieval to run daily
    scheduler.add_job(
        func=arxiv_retrieval.retrieve_recent_papers,
        trigger='interval',
        days=1,
        id='retrieve_papers',
        kwargs={'max_results': 20},
        replace_existing=True
    )
    
    # Schedule paper processing to run 30 minutes after retrieval
    scheduler.add_job(
        func=paper_processor.process_unprocessed_papers,
        trigger='interval',
        days=1,
        id='process_papers',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduled tasks have been set up")

# Routes
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    
    # Get total number of papers
    total_papers = conn.execute('SELECT COUNT(*) FROM papers').fetchone()[0]
    
    # Get papers for current page
    papers_query = '''
    SELECT p.id, p.arxiv_id, p.title, p.published_date, p.entry_url, p.pdf_url, s.brief_summary
    FROM papers p
    LEFT JOIN summaries s ON p.id = s.paper_id
    ORDER BY p.published_date DESC
    LIMIT ? OFFSET ?
    '''
    papers_data = conn.execute(papers_query, (per_page, offset)).fetchall()
    
    papers = []
    for paper in papers_data:
        # Get authors for this paper
        authors_query = '''
        SELECT a.name
        FROM authors a
        JOIN paper_authors pa ON a.id = pa.author_id
        WHERE pa.paper_id = ?
        ORDER BY pa.author_position
        '''
        authors = [row[0] for row in conn.execute(authors_query, (paper['id'],)).fetchall()]
        
        # Get categories for this paper
        categories_query = '''
        SELECT c.category_code
        FROM categories c
        JOIN paper_categories pc ON c.id = pc.category_id
        WHERE pc.paper_id = ?
        '''
        categories = [row[0] for row in conn.execute(categories_query, (paper['id'],)).fetchall()]
        
        papers.append({
            'id': paper['id'],
            'arxiv_id': paper['arxiv_id'],
            'title': paper['title'],
            'authors': authors,
            'published_date': format_date(paper['published_date']),
            'entry_url': paper['entry_url'],
            'pdf_url': paper['pdf_url'],
            'categories': categories,
            'brief_summary': paper['brief_summary'] if paper['brief_summary'] else "Summary not available yet."
        })
    
    # Calculate pagination info
    total_pages = (total_papers + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    conn.close()
    
    return render_template(
        'index.html',
        papers=papers,
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next
    )

@app.route('/paper/<int:paper_id>')
def paper_detail(paper_id):
    conn = get_db_connection()
    
    # Get paper details
    paper_query = '''
    SELECT p.id, p.arxiv_id, p.title, p.published_date, p.entry_url, p.pdf_url, 
           a.abstract_text, s.extended_summary
    FROM papers p
    LEFT JOIN abstracts a ON p.id = a.paper_id
    LEFT JOIN summaries s ON p.id = s.paper_id
    WHERE p.id = ?
    '''
    paper_data = conn.execute(paper_query, (paper_id,)).fetchone()
    
    if paper_data is None:
        conn.close()
        abort(404)
    
    # Get authors for this paper
    authors_query = '''
    SELECT a.name
    FROM authors a
    JOIN paper_authors pa ON a.id = pa.author_id
    WHERE pa.paper_id = ?
    ORDER BY pa.author_position
    '''
    authors = [row[0] for row in conn.execute(authors_query, (paper_id,)).fetchall()]
    
    # Get categories for this paper
    categories_query = '''
    SELECT c.category_code
    FROM categories c
    JOIN paper_categories pc ON c.id = pc.category_id
    WHERE pc.paper_id = ?
    '''
    categories = [row[0] for row in conn.execute(categories_query, (paper_id,)).fetchall()]
    
    paper = {
        'id': paper_data['id'],
        'arxiv_id': paper_data['arxiv_id'],
        'title': paper_data['title'],
        'authors': authors,
        'published_date': format_date(paper_data['published_date']),
        'entry_url': paper_data['entry_url'],
        'pdf_url': paper_data['pdf_url'],
        'categories': categories,
        'abstract': paper_data['abstract_text'],
        'extended_summary': paper_data['extended_summary'] if paper_data['extended_summary'] else "Extended summary not available yet."
    }
    
    conn.close()
    
    return render_template('paper_detail.html', paper=paper)

@app.route('/api/paper/<int:paper_id>')
def api_paper_detail(paper_id):
    conn = get_db_connection()
    
    # Get paper details
    paper_query = '''
    SELECT p.id, p.arxiv_id, p.title, p.published_date, p.entry_url, p.pdf_url, 
           a.abstract_text, s.extended_summary
    FROM papers p
    LEFT JOIN abstracts a ON p.id = a.paper_id
    LEFT JOIN summaries s ON p.id = s.paper_id
    WHERE p.id = ?
    '''
    paper_data = conn.execute(paper_query, (paper_id,)).fetchone()
    
    if paper_data is None:
        conn.close()
        return jsonify({'error': 'Paper not found'}), 404
    
    # Get authors for this paper
    authors_query = '''
    SELECT a.name
    FROM authors a
    JOIN paper_authors pa ON a.id = pa.author_id
    WHERE pa.paper_id = ?
    ORDER BY pa.author_position
    '''
    authors = [row[0] for row in conn.execute(authors_query, (paper_id,)).fetchall()]
    
    # Get categories for this paper
    categories_query = '''
    SELECT c.category_code
    FROM categories c
    JOIN paper_categories pc ON c.id = pc.category_id
    WHERE pc.paper_id = ?
    '''
    categories = [row[0] for row in conn.execute(categories_query, (paper_id,)).fetchall()]
    
    paper = {
        'id': paper_data['id'],
        'arxiv_id': paper_data['arxiv_id'],
        'title': paper_data['title'],
        'authors': authors,
        'published_date': paper_data['published_date'],
        'entry_url': paper_data['entry_url'],
        'pdf_url': paper_data['pdf_url'],
        'categories': categories,
        'abstract': paper_data['abstract_text'],
        'extended_summary': paper_data['extended_summary']
    }
    
    conn.close()
    
    return jsonify(paper)

@app.route('/stats')
def stats():
    conn = get_db_connection()
    
    # Get total number of papers
    total_papers = conn.execute('SELECT COUNT(*) FROM papers').fetchone()[0]
    
    # Get number of papers with summaries
    summarized_papers = conn.execute('SELECT COUNT(*) FROM summaries').fetchone()[0]
    
    # Get latest retrieval log
    latest_retrieval = conn.execute('''
    SELECT run_date, papers_retrieved, status, message 
    FROM retrieval_log 
    ORDER BY run_date DESC 
    LIMIT 5
    ''').fetchall()
    
    # Get papers by category
    category_stats = conn.execute('''
    SELECT c.category_code, COUNT(pc.paper_id) as paper_count
    FROM categories c
    JOIN paper_categories pc ON c.id = pc.category_id
    GROUP BY c.category_code
    ORDER BY paper_count DESC
    ''').fetchall()
    
    # Get papers by date
    date_stats = conn.execute('''
    SELECT strftime('%Y-%m', published_date) as month, COUNT(*) as paper_count
    FROM papers
    GROUP BY month
    ORDER BY month DESC
    LIMIT 12
    ''').fetchall()
    
    stats_data = {
        'total_papers': total_papers,
        'summarized_papers': summarized_papers,
        'latest_retrieval': [dict(row) for row in latest_retrieval],
        'category_stats': [dict(row) for row in category_stats],
        'date_stats': [dict(row) for row in date_stats]
    }
    
    conn.close()
    
    return render_template('stats.html', stats=stats_data)

@app.template_filter('json')
def json_filter(data):
    return json.dumps(data)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Initialize the database if it doesn't exist
def init_db():
    if not os.path.exists(DB_PATH):
        logger.info("Initializing database...")
        arxiv_retrieval.create_database()
        logger.info("Database initialized")

if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    # Schedule background tasks
    schedule_tasks()
    
    # Run initial retrieval if database is empty
    conn = get_db_connection()
    paper_count = conn.execute('SELECT COUNT(*) FROM papers').fetchone()[0]
    conn.close()
    
    if paper_count == 0:
        logger.info("No papers in database. Running initial retrieval...")
        arxiv_retrieval.retrieve_recent_papers(max_results=20)
        paper_processor.process_unprocessed_papers()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0')
