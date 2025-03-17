#!/usr/bin/env python3
"""
Deployment script for Quantum Paper Summarizer.
This script prepares the application for deployment by checking dependencies,
initializing the database, and setting up required directories.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("deployment.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).resolve().parent

def check_python_version():
    """Check if Python version is compatible."""
    required_version = (3, 8)
    current_version = sys.version_info
    
    if current_version < required_version:
        logger.error(f"Python {required_version[0]}.{required_version[1]} or higher is required. You have {current_version[0]}.{current_version[1]}")
        return False
    
    logger.info(f"Python version check passed: {current_version[0]}.{current_version[1]}")
    return True

def check_dependencies():
    """Check if all required packages are installed."""
    try:
        import flask
        import apscheduler
        import arxiv
        import nltk
        import PyPDF2
        import networkx
        import numpy
        import requests
        
        logger.info("All required packages are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        logger.error("Please run: pip install -r requirements.txt")
        return False

def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        BASE_DIR / "logs",
        BASE_DIR / "data"
    ]
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")
    
    return True

def download_nltk_resources():
    """Download required NLTK resources."""
    try:
        import nltk
        
        # Check if resources are already downloaded
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            logger.info("NLTK resources are already downloaded")
        except LookupError:
            logger.info("Downloading NLTK resources...")
            nltk.download('punkt')
            nltk.download('stopwords')
            logger.info("NLTK resources downloaded successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error downloading NLTK resources: {str(e)}")
        return False

def initialize_database():
    """Initialize the database if it doesn't exist."""
    db_path = BASE_DIR / "quantum_papers.db"
    
    if db_path.exists():
        logger.info(f"Database already exists at {db_path}")
        return True
    
    try:
        logger.info("Initializing database...")
        subprocess.run([sys.executable, str(BASE_DIR / "init_db.py")], check=True)
        logger.info("Database initialized successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def main():
    """Main deployment function."""
    logger.info("Starting deployment process...")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Create directories
    if not create_directories():
        return False
    
    # Download NLTK resources
    if not download_nltk_resources():
        return False
    
    # Initialize database
    if not initialize_database():
        return False
    
    logger.info("Deployment completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
