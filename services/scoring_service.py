from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from services.ai_service import extract_skills
import numpy as np
import re

print("Loading SentenceTransformer model 'all-MiniLM-L6-v2' in scoring service...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully in scoring service.")

def extract_requested_experience(jd_text):
    """Detect how many years of experience the Job Description requests."""
    patterns = [
        r'(\d+)\+?\s*(?:yr|year)s?\s*(?:of\s*)?experience',
        r'experience\s*(?:required|preferred)?\s*:\s*(\d+)',
        r'minimum\s*(?:of\s*)?(\d+)\s*(?:yr|year)s?'
    ]
    for pattern in patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 3  # default standard assumptions

def calculate_education_match(candidate_edu, jd_text):
    """Determine education overlap score based on degree level requirements."""
    degrees = [d.lower() for d in candidate_edu.get("degrees", [])]
    jd_lower = jd_text.lower()
    
    # Check if JD mentions degree levels
    requires_phd = any(w in jd_lower for w in ["phd", "ph.d", "doctorate"])
    requires_master = any(w in jd_lower for w in ["master", "ms", "mtech", "m.tech", "mba", "m.s"])
    requires_bachelor = any(w in jd_lower for w in ["bachelor", "bs", "btech", "b.tech", "be", "b.e", "degree"])
    
    cand_has_phd = any("ph.d" in d or "phd" in d for d in degrees)
    cand_has_master = any("master" in d or "ms" in d or "m.s" in d or "mba" in d or "m.tech" in d or "mtech" in d or "mca" in d for d in degrees)
    cand_has_bachelor = any("bachelor" in d or "bs" in d or "b.s" in d or "b.tech" in d or "btech" in d or "b.e" in d or "be" in d or "bca" in d or "bsc" in d or "b.sc" in d for d in degrees)
    
    if candidate_edu.get("degrees", ["Not specified"])[0] == "Not specified":
        return 40.0
        
    if requires_phd:
        if cand_has_phd: return 100.0
        if cand_has_master: return 75.0
        return 50.0
        
    if requires_master:
        if cand_has_phd or cand_has_master: return 100.0
        if cand_has_bachelor: return 80.0
        return 60.0
        
    if requires_bachelor:
        if cand_has_phd or cand_has_master or cand_has_bachelor: return 100.0
        return 70.0
        
    # If no specific degree is requested in JD
    if cand_has_master or cand_has_phd:
        return 95.0
    if cand_has_bachelor:
        return 90.0
        
    return 80.0

def calculate_keyword_match(resume_text, jd_text):
    """Calculate direct overlapping vocabulary percentage between resume and JD."""
    res_words = set(re.findall(r'\b[a-zA-Z]{3,15}\b', resume_text.lower()))
    jd_words = set(re.findall(r'\b[a-zA-Z]{3,15}\b', jd_text.lower()))
    
    stopwords = {
        'the', 'and', 'for', 'with', 'you', 'that', 'this', 'from', 'our', 'are', 'your', 'will', 'have', 'web', 'role',
        'work', 'team', 'experience', 'skills', 'about', 'services', 'systems', 'tools', 'development', 'management',
        'design', 'software', 'project', 'candidate', 'position', 'requirements', 'applications', 'solutions'
    }
    
    res_words_filtered = res_words - stopwords
    jd_words_filtered = jd_words - stopwords
    
    if not jd_words_filtered:
        return 50.0
        
    overlap = res_words_filtered.intersection(jd_words_filtered)
    score = (len(overlap) / len(jd_words_filtered)) * 100
    
    # Scale keyword match to visual expectations
    score = 30 + (score / 100) * 70
    return min(100.0, round(score, 1))

def generate_ai_summary(details, matched_skills, missing_skills, score):
    """Generate a clean candidate description summary based on the matched details."""
    years = details["experience"]["years"]
    roles = details["experience"]["roles"]
    
    role_str = roles[0] if roles and roles[0] != "Not specified" else "Professional"
    
    summary_parts = []
    
    if years > 0:
        summary_parts.append(f"Candidate is a {role_str} with {years}+ years of experience.")
    else:
        summary_parts.append(f"Candidate is a {role_str} with entry-level or unspecified years of experience.")
        
    if matched_skills:
        summary_parts.append(f"Demonstrates core competency in key technologies including {', '.join(matched_skills[:4])}.")
    else:
        summary_parts.append("Has technical background but minimal direct match to the requested skill stack.")
        
    if details["experience"]["companies"] and details["experience"]["companies"][0] != "Not specified":
        summary_parts.append(f"Has history working with organizations like {', '.join(details['experience']['companies'][:2])}.")
        
    if missing_skills:
        summary_parts.append(f"Lacks professional experience in {', '.join(missing_skills[:3])} as requested by the job description.")
        
    return " ".join(summary_parts)

# --- ADVANCED ENTERPRISE-GRADE AI MATCH SERVICES ---

def generate_skill_gap_analysis(missing_skills):
    """Compile skill gap list and specific learning recommendations for upskilling."""
    gap_recommendations = []
    
    course_map = {
        "aws": "AWS Certified Cloud Practitioner (Coursera / Udemy)",
        "amazon web services": "AWS Cloud Practitioner Essentials (Amazon Web Services)",
        "docker": "Docker Fundamentals (Docker Hub / Udemy)",
        "kubernetes": "Certified Kubernetes Administrator - CKA (Linux Foundation)",
        "flask": "REST APIs with Flask and Python (Udemy)",
        "django": "Django 4 Class-Based Views Masterclass (Udemy)",
        "fastapi": "FastAPI Complete Developer Course (Udemy)",
        "react": "React - The Complete Guide (Udemy)",
        "typescript": "TypeScript Masterclass (Udemy)",
        "machine learning": "Machine Learning Specialization by Andrew Ng (Coursera)",
        "deep learning": "Deep Learning Specialization by Andrew Ng (Coursera)",
        "nlp": "Natural Language Processing Specialization (Coursera)",
        "postgresql": "PostgreSQL Boot Camp (Udemy)",
        "mysql": "SQL Boot Camp (Udemy)",
        "redis": "Redis University (Redis Labs)"
    }
    
    for skill in missing_skills:
        skill_lower = skill.lower()
        if skill_lower in course_map:
            gap_recommendations.append(f"Learn {skill}: {course_map[skill_lower]}")
        else:
            gap_recommendations.append(f"Upskill in {skill}: {skill} Complete Course (Coursera / Udemy)")
            
    return gap_recommendations[:4]

def generate_improvement_suggestions(details, skill_score, ats_score):
    """Provide specific suggestions to optimize the candidate's resume."""
    suggestions = []
    
    if ats_score < 80:
        suggestions.append("Address structural layout. Ensure clearly separated contact info, work history, and skills headers.")
    if details["ats_checklist"]["email_present"] is False:
        suggestions.append("Add a professional email address in the contact details section.")
    if details["ats_checklist"]["phone_present"] is False:
        suggestions.append("Add a valid phone number with country code for recruiter outreach.")
        
    if len(details["skills"]) < 5:
        suggestions.append("Expand the skills section by listing technical core tools, libraries, and frameworks.")
        
    if details["project_count"] < 3:
        suggestions.append("Add at least 3 detailed projects containing a summary, technical stack used, and bulleted accomplishments.")
        
    if details["cert_count"] == 0:
        suggestions.append("Incorporate professional certifications (e.g. cloud practitioner, software engineering certs) to build credibility.")
        
    # General recommendations
    suggestions.append("Quantify career impacts (e.g., 'boosted system efficiency by 20%', 'reduced server latency by 15%') in bullet points.")
    suggestions.append("Incorporate a link to your public GitHub profile and LinkedIn profile near the top header.")
    
    return suggestions[:4]

def generate_interview_questions(matched_skills, missing_skills):
    """Generate interview questions tailored to the candidate's matched and missing capabilities."""
    questions = []
    matched_lower = [m.lower() for m in matched_skills]
    
    if "python" in matched_lower:
        questions.append("Explain the difference between Python decorators and generator functions, and name a real-world use case for each.")
    elif "javascript" in matched_lower:
        questions.append("Explain prototypal inheritance and how closures work in JavaScript.")
        
    if "flask" in matched_lower:
        questions.append("How do you handle database sessions and migrations inside a modular Flask application using Blueprints?")
    elif "react" in matched_lower:
        questions.append("Describe React context API vs Redux, and how you optimize functional components to prevent unnecessary re-renders.")
    elif "django" in matched_lower:
        questions.append("How does Django Middleware work, and how would you optimize database queries using select_related or prefetch_related?")
        
    # Missing Skills questions (Testing adaptability)
    if missing_skills:
        first_missing = missing_skills[0]
        questions.append(f"The job description requests experience with '{first_missing}'. Since you do not directly list this, how would you approach picking it up on the job?")
        
    # Core architectural question
    questions.append("Describe a challenging technical bug or performance bottleneck you encountered in a previous project, and the steps you took to diagnose and resolve it.")
    
    return questions[:3]

def generate_explainable_decision(score, matched_skills, missing_skills, cand_years, req_years):
    """Return an Explainable AI Hiring Decision detail outlining why recommended or rejected."""
    reasons = []
    if score >= 82:
        reasons.append(f"Strong overall alignment ({score}% match score) with requested technical profile.")
        if matched_skills:
            reasons.append(f"Demonstrates expertise in requested technologies: {', '.join(matched_skills[:3])}.")
        if cand_years >= req_years:
            reasons.append(f"Meets or exceeds minimum required experience length ({cand_years} years vs {req_years} required).")
    elif score >= 65:
        reasons.append(f"Moderately aligned candidate ({score}% match score) with good core skills.")
        if missing_skills:
            reasons.append(f"Has minor technical skill gaps. Lacks immediate experience in: {', '.join(missing_skills[:3])}.")
        if cand_years > 0:
            reasons.append(f"Possesses relevant industry exposure but may require upskilling on specific framework modules.")
    else:
        reasons.append(f"Low match evaluation score ({score}% match score) below target screening thresholds.")
        if missing_skills:
            reasons.append(f"Significant skill gaps identified: Candidate is missing {', '.join(missing_skills[:4])}.")
        if cand_years < req_years:
            reasons.append(f"Total experience length of {cand_years} years falls short of the target {req_years} years required.")
            
    return reasons

def predict_roles(skills):
    """Predict suitable job roles based on skills list."""
    roles = []
    skills_lower = [s.lower() for s in skills]
    
    has_python = "python" in skills_lower
    has_backend = any(x in skills_lower for x in ["flask", "django", "fastapi", "spring", "node.js", "express", "go", "golang", "java", "ruby"])
    has_frontend = any(x in skills_lower for x in ["react", "angular", "vue", "javascript", "typescript", "html", "css", "tailwind", "bootstrap"])
    has_cloud = any(x in skills_lower for x in ["aws", "azure", "gcp", "docker", "kubernetes", "devops", "jenkins", "ci/cd"])
    has_data = any(x in skills_lower for x in ["machine learning", "deep learning", "nlp", "pandas", "numpy", "tensorflow", "pytorch", "data science", "data analysis"])
    
    if has_backend and has_frontend:
        roles.append("Full Stack Developer")
    elif has_backend:
        roles.append("Backend Software Engineer")
    elif has_frontend:
        roles.append("Frontend Developer")
        
    if has_python:
        roles.append("Python Developer")
        
    if has_cloud:
        roles.append("Cloud & DevOps Engineer")
        
    if has_data:
        roles.append("Machine Learning Engineer / Data Scientist")
        
    if not roles:
        roles.append("Software Developer")
        
    return roles[:3]

def generate_tags(skills, exp_years, ats_score):
    """Generate modern SaaS style candidate tags."""
    tags = []
    skills_lower = [s.lower() for s in skills]
    
    if "python" in skills_lower: tags.append("#Python")
    if "react" in skills_lower: tags.append("#React")
    if "aws" in skills_lower or "docker" in skills_lower or "kubernetes" in skills_lower:
        tags.append("#CloudReady")
    else:
        tags.append("#CloudBeginner")
        
    if exp_years >= 5:
        tags.append("#SeniorEngineer")
    elif exp_years >= 2:
        tags.append("#MidLevel")
    else:
        tags.append("#Associate")
        
    if ats_score >= 90:
        tags.append("#ATS_Optimized")
        
    if len(skills) > 8:
        tags.append("#MultiSkilled")
        
    return tags[:5]


def match_resume_with_jd(resume_text, jd_text, details):
    """
    Compare resume with job description, compute various sub-scores, checklist items,
    and output a comprehensive metrics dictionary including all advanced AI indicators.
    """
    resume_skills = details["skills"]
    
    # 1. Semantic Match (SentenceTransformers Cosine Similarity)
    resume_emb = model.encode([resume_text])
    jd_emb = model.encode([jd_text])
    
    similarity = cosine_similarity(resume_emb, jd_emb)
    raw_similarity = float(similarity[0][0]) * 100
    
    # Map raw similarity to a realistic visual range [0.15, 0.75] -> [20%, 98%]
    if raw_similarity < 15:
        overall_score = max(10.0, raw_similarity * 1.3)
    else:
        overall_score = 20 + ((raw_similarity - 15) / (75 - 15)) * (98 - 20)
        overall_score = min(100.0, max(10.0, overall_score))
    
    overall_score = round(overall_score, 1)
    
    # 2. Skill Match Score
    jd_skills = extract_skills(jd_text)
    matched_skills = [s for s in jd_skills if s in resume_skills]
    missing_skills = [s for s in jd_skills if s not in resume_skills]
    
    if jd_skills:
        skill_score = (len(matched_skills) / len(jd_skills)) * 100
    else:
        skill_score = 65.0
        
    skill_score = round(skill_score, 1)
    
    # 3. Experience Match Score
    req_years = extract_requested_experience(jd_text)
    cand_years = details["experience"]["years"]
    
    if req_years == 0:
        exp_score = 100.0
    else:
        exp_score = (cand_years / req_years) * 100
        
    exp_score = min(100.0, round(exp_score, 1))
    
    # 4. Education Match Score
    edu_score = calculate_education_match(details["education"], jd_text)
    
    # 5. Keyword Match Score
    keyword_score = calculate_keyword_match(resume_text, jd_text)
    
    # 6. Confidence Score
    confidence = 50
    if details["name"] != "Not Found": confidence += 10
    if details["email"] != "Not Found": confidence += 10
    if details["phone"] != "Not Found": confidence += 10
    if cand_years > 0: confidence += 10
    if len(resume_skills) > 4: confidence += 10
    confidence = min(100, confidence)
    
    # AI Recommendation Badge
    if overall_score >= 82:
        recommendation = "Highly Recommended"
        recommendation_badge = "success"
        risk_level = "Low Risk"
        risk_badge = "success"
    elif overall_score >= 65:
        recommendation = "Recommended"
        recommendation_badge = "primary"
        risk_level = "Medium Risk"
        risk_badge = "warning"
    elif overall_score >= 45:
        recommendation = "Consider"
        recommendation_badge = "warning"
        risk_level = "Medium Risk"
        risk_badge = "warning"
    else:
        recommendation = "Rejected"
        recommendation_badge = "danger"
        risk_level = "High Risk"
        risk_badge = "danger"
        
    # Strengths and Weaknesses
    strengths = []
    weaknesses = []
    
    if skill_score >= 70:
        strengths.append("High alignment with requested technical skills.")
    elif len(matched_skills) > 0:
        strengths.append(f"Demonstrates proficiency in key core tools: {', '.join(matched_skills[:3])}.")
        
    if cand_years >= req_years:
        strengths.append(f"Meets or exceeds target experience requirements ({cand_years} years vs {req_years} required).")
    elif cand_years > 0:
        weaknesses.append(f"Experience is slightly below requested range ({cand_years} years vs {req_years} required).")
        
    if edu_score >= 90:
        strengths.append("Educational qualifications match role standards.")
        
    if missing_skills:
        weaknesses.append(f"Missing recommended technical stacks: {', '.join(missing_skills[:4])}.")
    else:
        if jd_skills:
            strengths.append("Fully covers all specific toolsets requested in the job description.")
            
    if not strengths:
        strengths.append("Possesses baseline formatting and standard details.")
    if not weaknesses:
        weaknesses.append("No critical missing skills or credentials detected.")
        
    # Suitability report
    if overall_score >= 82:
        suitability = f"Strong candidate showing {overall_score}% overlap. Their technical skills and years of experience are a solid match for this vacancy. Strongly recommend moving to technical interviews."
    elif overall_score >= 65:
        suitability = f"Promising candidate with {overall_score}% overlap. Covers most core components but has some skill or experience gaps. Recommend for initial phone screen."
    elif overall_score >= 45:
        suitability = f"Borderline candidate ({overall_score}% overlap). Lacks several critical skill categories. Consider only if alternative candidates are unavailable."
    else:
        suitability = f"Low match candidate ({overall_score}% overlap). Significant gaps in skills, experience, and domain knowledge. Not recommended for this role."
        
    # Advanced fields compilations
    gap_recommendations = generate_skill_gap_analysis(missing_skills)
    improvement_suggestions = generate_improvement_suggestions(details, skill_score, details["ats_score"])
    generated_questions = generate_interview_questions(matched_skills, missing_skills)
    explainable_decision = generate_explainable_decision(overall_score, matched_skills, missing_skills, cand_years, req_years)
    predicted_roles = predict_roles(resume_skills)
    smart_tags = generate_tags(resume_skills, cand_years, details["ats_score"])
    
    return {
        "score": overall_score,
        "skill_match": skill_score,
        "experience_match": exp_score,
        "education_match": edu_score,
        "keyword_match": keyword_score,
        "ats_score": details["ats_score"],
        "confidence": confidence,
        "recommendation": recommendation,
        "recommendation_badge": recommendation_badge,
        "risk_level": risk_level,
        "risk_badge": risk_badge,
        "jd_skills": jd_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suitability": suitability,
        "summary": generate_ai_summary(details, matched_skills, missing_skills, overall_score),
        
        # Advanced features
        "gap_recommendations": gap_recommendations,
        "improvement_suggestions": improvement_suggestions,
        "generated_questions": generated_questions,
        "explainable_decision": explainable_decision,
        "predicted_roles": predicted_roles,
        "smart_tags": smart_tags
    }
