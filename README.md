# AI Missing Information Detective

AI Missing Information Detective is a Flask-based document analysis application that uses AI to identify missing, unclear, and contradictory information in documents.

## Features

- Upload PDF, DOCX and TXT documents
- Upload JPG, JPEG and PNG images
- Analyze documents from a URL
- AI-powered document analysis
- Missing information detection
- Unclear information detection
- Contradiction detection
- Evidence extraction
- Smart question generation
- Critical / Important / Optional priority classification
- Document completeness score
- Analysis history
- View previous analysis reports
- Admin control panel
- Responsive detective-style interface

## How It Works

1. User uploads a document, image, text or URL.
2. The application extracts the available information.
3. Gemini AI analyzes the content.
4. The system identifies:
   - Missing information
   - Unclear information
   - Contradictions
   - Evidence
5. AI generates useful questions.
6. A completeness score is generated.
7. The analysis is saved in history.
8. Previous reports can be viewed later.

## Technology Stack

- Python
- Flask
- Google Gemini AI
- SQLite
- HTML
- CSS
- JavaScript

## Python Packages

- Flask
- google-genai
- python-dotenv
- pypdf
- python-docx
- requests
- beautifulsoup4

## Project Structure

```text
AI-Missing-Information-Detective/
│
├── app.py
├── requirements.txt
├── .env
├── README.md
│
├── ai/
│   └── analyzer.py
│
├── database/
│   ├── database.py
│   └── database.db
│
├── templates/
│   ├── index.html
│   ├── upload.html
│   ├── analysis.html
│   ├── results.html
│   ├── questions.html
│   ├── score.html
│   ├── history.html
│   └── admin.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
└── uploads/