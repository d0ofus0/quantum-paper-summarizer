#!/bin/bash

# Create necessary directories
mkdir -p /home/ubuntu/quantum_paper_summarizer/templates
mkdir -p /home/ubuntu/quantum_paper_summarizer/logs
mkdir -p /home/ubuntu/quantum_paper_summarizer/data

# Install required Python packages
pip3 install flask apscheduler arxiv nltk PyPDF2 networkx numpy gunicorn

# Download NLTK resources
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create systemd service file for the Flask application
cat > /tmp/quantum-summarizer.service << 'EOF'
[Unit]
Description=Quantum Paper Summarizer Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/quantum_paper_summarizer
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always
StandardOutput=file:/home/ubuntu/quantum_paper_summarizer/logs/gunicorn_stdout.log
StandardError=file:/home/ubuntu/quantum_paper_summarizer/logs/gunicorn_stderr.log

[Install]
WantedBy=multi-user.target
EOF

# Create cron job for scheduled tasks
cat > /tmp/quantum-summarizer-cron << 'EOF'
# Run paper retrieval daily at 2 AM
0 2 * * * cd /home/ubuntu/quantum_paper_summarizer && /usr/bin/python3 arxiv_retrieval.py >> /home/ubuntu/quantum_paper_summarizer/logs/retrieval.log 2>&1

# Run paper processing daily at 3 AM
0 3 * * * cd /home/ubuntu/quantum_paper_summarizer && /usr/bin/python3 paper_processor.py >> /home/ubuntu/quantum_paper_summarizer/logs/processor.log 2>&1
EOF

echo "Setup script created successfully. Run with sudo privileges to install the service."
