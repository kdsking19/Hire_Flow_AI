from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import uuid

from services.parser_service import extract_text
from services.ai_service import extract_details
from services.scoring_service import match_resume_with_jd

app = Flask(__name__)

# Configure uploads directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # Max 32MB upload size limit

# Ensure directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory session store for candidate screenings
ANALYSIS_CACHE = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    # 1. Extract Job Description Text
    jd_text = ""
    if "jd_file" in request.files and request.files["jd_file"].filename != "":
        jd_file = request.files["jd_file"]
        jd_path = os.path.join(app.config["UPLOAD_FOLDER"], jd_file.filename)
        jd_file.save(jd_path)
        jd_text = extract_text(jd_path)
        try:
            os.remove(jd_path)
        except:
            pass
    else:
        jd_text = request.form.get("job_description", "")
        
    if not jd_text.strip():
        return render_template("index.html", error="Please provide a Job Description (paste text or upload a document).")

    # 2. Extract Resume Files (check single vs multiple files)
    resumes = request.files.getlist("resumes")
    if not resumes or resumes[0].filename == "":
        single_resume = request.files.get("resume")
        if single_resume and single_resume.filename != "":
            resumes = [single_resume]
        else:
            return render_template("index.html", error="Please upload at least one Resume file.")

    results_list = []

    for resume_file in resumes:
        if resume_file.filename == "":
            continue
            
        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
        resume_file.save(resume_path)
        
        resume_text = extract_text(resume_path)
        
        # Clean up temporary file
        try:
            if os.path.exists(resume_path):
                os.remove(resume_path)
        except Exception as e:
            print(f"Error removing temporary file: {e}")
            
        if not resume_text.strip():
            continue
            
        # Analyze Candidate
        details = extract_details(resume_text)
        result = match_resume_with_jd(resume_text, jd_text, details)
        
        candidate_id = str(uuid.uuid4())
        record = {
            "id": candidate_id,
            "details": details,
            "result": result,
            "filename": resume_file.filename,
            "resume_text": resume_text
        }
        
        # Cache for page switching
        ANALYSIS_CACHE[candidate_id] = record
        results_list.append(record)

    if not results_list:
        return render_template("index.html", error="Could not parse or extract text from the uploaded Resume(s).")

    # Direct redirect if only 1 resume is screened
    if len(results_list) == 1:
        return redirect(url_for("candidate_detail", candidate_id=results_list[0]["id"]))

    # Sort batch results by score (descending)
    results_list.sort(key=lambda x: x["result"]["score"], reverse=True)
    return render_template("ranking.html", candidates=results_list)

@app.route("/candidate/<candidate_id>")
def candidate_detail(candidate_id):
    record = ANALYSIS_CACHE.get(candidate_id)
    if not record:
        return redirect(url_for("index"))
        
    return render_template(
        "result.html",
        details=record["details"],
        result=record["result"],
        filename=record["filename"],
        candidate_id=candidate_id,
        resume_text=record.get("resume_text", "")
    )

# --- Resume Upload History Management ---
@app.route("/history")
def history():
    entries = []
    for cid, record in ANALYSIS_CACHE.items():
        entries.append({
            "id": cid,
            "filename": record.get("filename", "Unknown"),
            "name": record.get("details", {}).get("name", "Not Found"),
            "score": record.get("result", {}).get("score", 0),
            "recommendation": record.get("result", {}).get("recommendation", "N/A"),
            "recommendation_badge": record.get("result", {}).get("recommendation_badge", "primary"),
            "decision": record.get("result", {}).get("recruiter_decision", None),
            "matched_skills": record.get("result", {}).get("matched_skills", []),
            "missing_skills": record.get("result", {}).get("missing_skills", []),
        })
    entries.sort(key=lambda x: x["score"], reverse=True)
    return render_template("history.html", entries=entries)

@app.route("/history/<candidate_id>/delete", methods=["POST"])
def delete_history(candidate_id):
    if candidate_id in ANALYSIS_CACHE:
        del ANALYSIS_CACHE[candidate_id]
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Entry not found"}), 404

# --- Recruiter Action States (SaaS Interactivity Simulation) ---
@app.route("/candidate/<candidate_id>/action", methods=["POST"])
def candidate_action(candidate_id):
    status = request.json.get("status")
    if candidate_id in ANALYSIS_CACHE and status in ["Shortlisted", "Rejected", "Hold"]:
        ANALYSIS_CACHE[candidate_id]["result"]["recruiter_decision"] = status
        return jsonify({"success": True, "status": status})
    return jsonify({"success": False}), 400

# --- Enterprise-Grade Programmatic API Integration ---
@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Programmatic JSON API to programmatically screen candidates."""
    if "resume" not in request.files:
        return jsonify({"error": "Missing file field 'resume'"}), 400
        
    jd_text = request.form.get("job_description", "")
    if not jd_text:
        return jsonify({"error": "Missing parameter 'job_description'"}), 400
        
    resume_file = request.files["resume"]
    resume_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(resume_path)
    
    resume_text = extract_text(resume_path)
    try:
        os.remove(resume_path)
    except:
        pass
        
    if not resume_text.strip():
        return jsonify({"error": "Unparseable resume file"}), 400
        
    details = extract_details(resume_text)
    result = match_resume_with_jd(resume_text, jd_text, details)
    
    return jsonify({
        "status": "success",
        "filename": resume_file.filename,
        "candidate_details": {
            "name": details["name"],
            "email": details["email"],
            "phone": details["phone"],
            "skills": details["skills"],
            "experience_years": details["experience"]["years"],
            "roles": details["experience"]["roles"],
            "companies": details["experience"]["companies"],
            "education": details["education"]
        },
        "match_analysis": {
            "overall_score": result["score"],
            "skill_match_score": result["skill_match"],
            "experience_match_score": result["experience_match"],
            "education_match_score": result["education_match"],
            "keyword_match_score": result["keyword_match"],
            "ats_compatibility_score": result["ats_score"],
            "ai_confidence_score": result["confidence"],
            "recommendation": result["recommendation"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
            "ai_summary": result["summary"]
        }
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
