# Hire Flow AI Resume Screener

A lightweight Flask-based resume screening app that analyzes candidate resumes against a job description and produces an interactive match report.

![HTML](https://img.shields.io/badge/HTML-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/CSS-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![NLP](https://img.shields.io/badge/NLP-7B61FF?style=for-the-badge&logo=ai&logoColor=white)

## Project Description

This project combines document parsing, resume text extraction, NLP, and semantic matching to help recruiters screen candidates faster.

Key capabilities:
- Upload PDFs and DOCX resumes for automated text extraction
- Paste or upload a job description to compare against candidate experience
- Extract candidate details such as name, email, phone, skills, experience, and education
- Score resumes on keyword fit, skill alignment, education match, and ATS compatibility
- Display ranked screening results with an interactive candidate detail view
- View and manage resume upload history with delete capability
- Provide a JSON API endpoint for programmatic integration

## Features

- Flask web UI for recruiter-style screening
- Resume parsing via `PyMuPDF` and `python-docx`
- NLP extraction using `spaCy` and a custom skill ontology
- Semantic scoring using `sentence-transformers`
- ATS-friendly resume health indicators and recruiter decision tracking
- Resume upload history page with view and delete management

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

## Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Upload page (single & batch screening modes) |
| POST | `/analyze` | Upload and analyze resume(s) against a job description |
| GET | `/candidate/<id>` | View detailed candidate analysis report |
| POST | `/candidate/<id>/action` | Update recruiter decision (Shortlisted/Hold/Rejected) |
| GET | `/history` | View all analyzed resume upload history |
| POST | `/history/<id>/delete` | Delete a resume analysis entry |
| POST | `/api/analyze` | Programmatic JSON API for resume screening |

### API

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
- `templates/` - HTML pages for index, ranking, result, and history views
- `static/` - CSS and static assets
- `uploads/` - temporary upload storage

## Notes

- Make sure `python-docx` is installed instead of the obsolete `docx` package.
- If you encounter `sentence_transformers` import errors, reinstall the dependency and any required PyTorch wheel for your environment.
- The app uses local in-memory caching (`ANALYSIS_CACHE`) for candidate detail navigation during a single session. All data is lost when the server restarts.
- The history page displays all analyzed resumes sorted by match score, with options to view details or delete entries.

## License

This repository does not include a license file. Add a `LICENSE` if you want to publish this project publicly.