# Resume Screener

A lightweight Flask-based resume screening app that analyzes candidate resumes against a job description and produces an interactive match report.

## Project Description

This project combines document parsing, resume text extraction, NLP, and semantic matching to help recruiters screen candidates faster.

Key capabilities:
- Upload PDFs and DOCX resumes for automated text extraction
- Paste or upload a job description to compare against candidate experience
- Extract candidate details such as name, email, phone, skills, experience, and education
- Score resumes on keyword fit, skill alignment, education match, and ATS compatibility
- Display ranked screening results with an interactive candidate detail view
- Provide a JSON API endpoint for programmatic integration

## Features

- Flask web UI for recruiter-style screening
- Resume parsing via `PyMuPDF` and `python-docx`
- NLP extraction using `spaCy` and a custom skill ontology
- Semantic scoring using `sentence-transformers`
- ATS-friendly resume health indicators and recruiter decision tracking

## Getting Started

### Prerequisites

- Python 3.8+
- `virtualenv` or built-in `venv`

### Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Run the app

```powershell
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## API

A programmatic endpoint is available at `/api/analyze`.

Example request fields:
- `resume` file upload
- `job_description` form text

Example response includes candidate details, match scores, and summary fields.

## Project Structure

- `app.py` - main Flask application
- `services/parser_service.py` - PDF/DOCX text extraction
- `services/ai_service.py` - resume detail extraction and NLP heuristics
- `services/scoring_service.py` - semantic matching and score generation
- `templates/` - HTML pages for index, ranking, and result views
- `static/` - CSS and static assets
- `uploads/` - temporary upload storage

## Notes

- Make sure `python-docx` is installed instead of the obsolete `docx` package.
- If you encounter `sentence_transformers` import errors, reinstall the dependency and any required PyTorch wheel for your environment.
- The app uses local in-memory caching for candidate detail navigation during a single session.

## License

This repository does not include a license file. Add a `LICENSE` if you want to publish this project publicly.