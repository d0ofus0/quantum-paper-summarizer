"""
Configuration settings for the Quantum Paper Summarizer application.
"""

import os

# Base directory of the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database settings
DB_PATH = os.path.join(BASE_DIR, 'quantum_papers.db')

# arXiv API settings
ARXIV_CATEGORY = 'quant-ph'  # Quantum Physics category
ARXIV_MAX_RESULTS = 20  # Maximum number of papers to retrieve per run
ARXIV_SORT_BY = 'submittedDate'  # Sort papers by submission date
ARXIV_DELAY = 0.1  # Delay between API requests in seconds

# Paper processing settings
BRIEF_SUMMARY_SENTENCES = 3  # Number of sentences in brief summary
EXTENDED_SUMMARY_SENTENCES = 10  # Number of sentences in extended summary

# Scheduler settings
RETRIEVAL_INTERVAL_HOURS = 24  # Run paper retrieval every 24 hours
PROCESSING_INTERVAL_HOURS = 24  # Run paper processing every 24 hours

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DIR = os.path.join(BASE_DIR, 'logs')
WEBAPP_LOG = os.path.join(LOG_DIR, 'webapp.log')
RETRIEVAL_LOG = os.path.join(LOG_DIR, 'retrieval.log')
PROCESSOR_LOG = os.path.join(LOG_DIR, 'processor.log')
PDF_EXTRACTOR_LOG = os.path.join(LOG_DIR, 'pdf_extractor.log')

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)
