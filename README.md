# Quantum Paper Summarizer

A web application that automatically retrieves, processes, and summarizes quantum physics research papers from arXiv's quant-ph category.

## Features

- **Automated Paper Retrieval**: Daily retrieval of the latest quantum physics papers from arXiv
- **Full-Text Processing**: Extracts and processes the complete text from PDF papers
- **AI-Powered Summarization**: Generates both brief and extended summaries using natural language processing
- **Web Interface**: Clean, responsive interface to browse and read paper summaries
- **Statistics Dashboard**: Visual analytics of paper categories, publication trends, and system status

## Screenshots

(Add screenshots of the application here)

## Technology Stack

- **Backend**: Python, Flask
- **Database**: SQLite
- **NLP**: NLTK, NetworkX
- **PDF Processing**: PyPDF2
- **Scheduling**: APScheduler
- **Frontend**: HTML, Bootstrap, Chart.js
- **Deployment**: Gunicorn

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/quantum-paper-summarizer.git
   cd quantum-paper-summarizer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download NLTK resources:
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
   ```

4. Initialize the database:
   ```bash
   python arxiv_retrieval.py
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Access the web interface at http://localhost:5000

## Production Deployment

For production deployment, you can use the included setup script:

```bash
chmod +x setup.sh
sudo ./setup.sh
```

This will:
- Install all required dependencies
- Set up systemd service for automatic startup
- Configure cron jobs for scheduled paper retrieval and processing

## Project Structure

```
quantum-paper-summarizer/
├── app.py                  # Main Flask application
├── arxiv_retrieval.py      # arXiv API integration and paper retrieval
├── paper_processor.py      # Paper processing and summarization
├── pdf_extractor.py        # PDF text extraction
├── requirements.txt        # Python dependencies
├── setup.sh                # Setup script for production deployment
├── templates/              # HTML templates
│   ├── index.html          # Homepage with paper list
│   ├── paper_detail.html   # Detailed paper view with summary
│   ├── stats.html          # Statistics dashboard
│   ├── 404.html            # Not found error page
│   └── 500.html            # Server error page
└── logs/                   # Application logs (created at runtime)
```

## Database Schema

The application uses SQLite with the following schema:

- **papers**: Core paper information (ID, title, publication date, URLs)
- **authors**: Author information
- **paper_authors**: Junction table for papers and authors
- **categories**: arXiv categories
- **paper_categories**: Junction table for papers and categories
- **abstracts**: Paper abstracts
- **full_texts**: Extracted full text content from PDFs
- **summaries**: Generated brief and extended summaries
- **retrieval_log**: Log of paper retrieval operations

For detailed schema information, see [database_design.md](database_design.md).

## Important Notes

- The application is set to retrieve papers from the quant-ph (Quantum Physics) category on arXiv
- Full PDF text extraction is used rather than just abstracts to generate more comprehensive summaries
- Paper retrieval is scheduled to run daily at 2 AM, and processing at 3 AM by default
- The summarization algorithm uses extractive summarization based on sentence similarity and PageRank

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [arXiv](https://arxiv.org/) for providing access to research papers
- [NLTK](https://www.nltk.org/) for natural language processing tools
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Bootstrap](https://getbootstrap.com/) for the frontend design
