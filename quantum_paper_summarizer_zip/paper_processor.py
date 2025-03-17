import os
import sqlite3
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import networkx as nx
from pdf_extractor import get_full_paper_text
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("summarizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quantum_papers.db')

# Ensure NLTK resources are downloaded
def download_nltk_resources():
    """Download required NLTK resources if not already present."""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

# Text preprocessing functions
def preprocess_text(text):
    """Clean and preprocess text for summarization."""
    # Replace multiple newlines with a single one
    text = ' '.join(text.split())
    return text

def sentence_similarity(sent1, sent2, stopwords=None):
    """Calculate the cosine similarity between two sentences."""
    if stopwords is None:
        stopwords = []
    
    sent1 = [w.lower() for w in sent1]
    sent2 = [w.lower() for w in sent2]
    
    all_words = list(set(sent1 + sent2))
    
    vector1 = [0] * len(all_words)
    vector2 = [0] * len(all_words)
    
    # Build the vectors for the two sentences
    for w in sent1:
        if w in stopwords:
            continue
        vector1[all_words.index(w)] += 1
    
    for w in sent2:
        if w in stopwords:
            continue
        vector2[all_words.index(w)] += 1
    
    return 1 - cosine_distance(vector1, vector2)

def build_similarity_matrix(sentences, stop_words):
    """Create a similarity matrix for all sentences."""
    # Create an empty similarity matrix
    similarity_matrix = np.zeros((len(sentences), len(sentences)))
    
    for idx1 in range(len(sentences)):
        for idx2 in range(len(sentences)):
            if idx1 == idx2:  # Same sentences
                continue
            
            similarity_matrix[idx1][idx2] = sentence_similarity(
                sentences[idx1], sentences[idx2], stop_words)
    
    return similarity_matrix

def generate_summary(text, num_sentences=5):
    """
    Generate a summary of the given text using extractive summarization.
    
    Args:
        text (str): The text to summarize
        num_sentences (int): Number of sentences to include in the summary
        
    Returns:
        str: The generated summary
    """
    # Download NLTK resources if needed
    download_nltk_resources()
    
    # Preprocess the text
    preprocessed_text = preprocess_text(text)
    
    # Tokenize the text into sentences
    sentences = sent_tokenize(preprocessed_text)
    
    # If there are fewer sentences than requested, return the original text
    if len(sentences) <= num_sentences:
        return preprocessed_text
    
    # Get stop words
    stop_words = stopwords.words('english')
    
    # Tokenize each sentence into words
    sentence_tokens = [nltk.word_tokenize(sentence) for sentence in sentences]
    
    # Build the similarity matrix
    similarity_matrix = build_similarity_matrix(sentence_tokens, stop_words)
    
    # Rank sentences using PageRank algorithm
    nx_graph = nx.from_numpy_array(similarity_matrix)
    scores = nx.pagerank(nx_graph)
    
    # Sort sentences by score and select top ones
    ranked_sentences = sorted(((scores[i], i, s) for i, s in enumerate(sentences)), reverse=True)
    
    # Get the top N sentences based on their position in the original text
    top_sentence_indices = sorted([ranked_sentences[i][1] for i in range(min(num_sentences, len(ranked_sentences)))])
    summary = ' '.join([sentences[i] for i in top_sentence_indices])
    
    return summary

def extract_and_summarize_paper(paper_id):
    """
    Extract full text from a paper's PDF and generate summaries.
    
    Args:
        paper_id (int): The database ID of the paper
        
    Returns:
        bool: True if successful, False otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get paper details
        cursor.execute("""
        SELECT arxiv_id, pdf_url FROM papers WHERE id = ?
        """, (paper_id,))
        paper = cursor.fetchone()
        
        if not paper:
            logger.error(f"Paper with ID {paper_id} not found")
            return False
        
        arxiv_id, pdf_url = paper
        
        # Get abstract
        cursor.execute("SELECT abstract_text FROM abstracts WHERE paper_id = ?", (paper_id,))
        abstract = cursor.fetchone()[0]
        
        logger.info(f"Processing paper {arxiv_id}")
        
        # Extract full text from PDF
        logger.info(f"Extracting text from PDF: {pdf_url}")
        full_text = get_full_paper_text(pdf_url)
        
        # If PDF extraction fails, use abstract as fallback
        if not full_text or len(full_text.strip()) < len(abstract):
            logger.warning("PDF extraction failed or returned less text than the abstract. Using abstract as fallback.")
            full_text = abstract
            extraction_status = "failed"
        else:
            logger.info(f"Successfully extracted {len(full_text)} characters from the PDF")
            extraction_status = "success"
        
        # Store full text
        cursor.execute("""
        INSERT INTO full_texts (paper_id, full_text, extraction_status)
        VALUES (?, ?, ?)
        """, (paper_id, full_text, extraction_status))
        
        # Generate brief summary (3 sentences)
        logger.info("Generating brief summary...")
        brief_summary = generate_summary(full_text, num_sentences=3)
        
        # Generate extended summary (10 sentences)
        logger.info("Generating extended summary...")
        extended_summary = generate_summary(full_text, num_sentences=10)
        
        # Store summaries
        cursor.execute("""
        INSERT INTO summaries (paper_id, brief_summary, extended_summary)
        VALUES (?, ?, ?)
        """, (paper_id, brief_summary, extended_summary))
        
        conn.commit()
        logger.info(f"Successfully processed and summarized paper {arxiv_id}")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error processing paper {paper_id}: {str(e)}")
        return False
        
    finally:
        conn.close()

def process_unprocessed_papers():
    """
    Find papers that have been retrieved but not yet summarized and process them.
    
    Returns:
        int: Number of papers processed
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Find papers that have no summaries
        cursor.execute("""
        SELECT p.id FROM papers p
        LEFT JOIN summaries s ON p.id = s.paper_id
        WHERE s.paper_id IS NULL
        """)
        
        unprocessed_papers = cursor.fetchall()
        
        if not unprocessed_papers:
            logger.info("No unprocessed papers found")
            return 0
        
        logger.info(f"Found {len(unprocessed_papers)} unprocessed papers")
        
        # Process each paper
        processed_count = 0
        for paper in unprocessed_papers:
            paper_id = paper[0]
            success = extract_and_summarize_paper(paper_id)
            if success:
                processed_count += 1
        
        logger.info(f"Successfully processed {processed_count} papers")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error processing unprocessed papers: {str(e)}")
        return 0
        
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting paper processing and summarization")
    processed_count = process_unprocessed_papers()
    logger.info(f"Completed processing {processed_count} papers")
