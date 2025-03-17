import requests
import PyPDF2
import io
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pdf_extractor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_pdf(url):
    """
    Download a PDF file from a URL.
    
    Args:
        url (str): URL of the PDF file
        
    Returns:
        bytes: The PDF file content as bytes, or None if download fails
    """
    try:
        logger.info(f"Downloading PDF from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.content
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        return None

def extract_text_from_pdf(pdf_content):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_content (bytes): PDF file content as bytes
        
    Returns:
        str: Extracted text from the PDF, or None if extraction fails
    """
    try:
        logger.info("Extracting text from PDF content")
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        if not text.strip():
            logger.warning("No text extracted from PDF")
            return None
        
        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def get_full_paper_text(pdf_url):
    """
    Download a PDF and extract its text content.
    
    Args:
        pdf_url (str): URL of the PDF file
        
    Returns:
        str: Extracted text from the PDF, or None if download or extraction fails
    """
    # Download the PDF
    pdf_content = download_pdf(pdf_url)
    if not pdf_content:
        return None
    
    # Extract text from the PDF
    text = extract_text_from_pdf(pdf_content)
    return text

if __name__ == "__main__":
    # Test with a sample arXiv PDF
    test_url = "https://arxiv.org/pdf/2101.00123.pdf"
    text = get_full_paper_text(test_url)
    if text:
        print(f"Successfully extracted {len(text)} characters from the PDF")
        print(text[:500] + "...")  # Print the first 500 characters
    else:
        print("Failed to extract text from the PDF")
