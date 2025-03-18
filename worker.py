import os
import time
import logging
from datetime import datetime, timedelta
import arxiv_retrieval
import paper_processor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def should_run_retrieval(hours_between_runs=24):
    """Determine if we should run the retrieval based on the last run time."""
    last_run = arxiv_retrieval.get_last_retrieval_date()
    
    if not last_run:
        return True
    
    time_since_last_run = datetime.now() - last_run
    return time_since_last_run > timedelta(hours=hours_between_runs)

def main():
    logger.info("Starting worker process")
    
    # Initialize the database if it doesn't exist
    if not os.path.exists(arxiv_retrieval.DB_PATH):
        logger.info("Initializing database...")
        arxiv_retrieval.create_database()
        logger.info("Database initialized")
    
    # Run initial retrieval if database is empty
    conn = arxiv_retrieval.sqlite3.connect(arxiv_retrieval.DB_PATH)
    try:
        paper_count = conn.execute('SELECT COUNT(*) FROM papers').fetchone()[0]
        if paper_count == 0:
            logger.info("No papers in database. Running initial retrieval...")
            arxiv_retrieval.retrieve_recent_papers(max_results=20)
            paper_processor.process_unprocessed_papers()
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
    finally:
        conn.close()
    
    # Main loop
    while True:
        try:
            # Check if we should run paper retrieval
            if should_run_retrieval():
                logger.info("Running scheduled paper retrieval...")
                new_papers = arxiv_retrieval.retrieve_recent_papers(max_results=20)
                logger.info(f"Retrieved {new_papers} new papers")
                
                # Process papers immediately after retrieval
                if new_papers > 0:
                    logger.info("Processing newly retrieved papers...")
                    processed = paper_processor.process_unprocessed_papers()
                    logger.info(f"Processed {processed} papers")
            else:
                logger.info("Skipping retrieval, not enough time has passed since last run")
            
            # Process any unprocessed papers that might have been missed
            unprocessed = paper_processor.process_unprocessed_papers()
            if unprocessed > 0:
                logger.info(f"Processed {unprocessed} previously missed papers")
                
        except Exception as e:
            logger.error(f"Error in worker loop: {str(e)}")
        
        # Sleep for 1 hour before checking again
        logger.info("Worker sleeping for 1 hour")
        time.sleep(3600)

if __name__ == "__main__":
    main()