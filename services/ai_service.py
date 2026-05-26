import re
import spacy

# Load spaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    import en_core_web_sm
    nlp = en_core_web_sm.load()

# Predefined skill ontology
COMMON_SKILLS = [
    # Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "ruby", "php", "go", "golang", "rust", "swift", "kotlin", "scala", "r", "sql", "html", "css", "sass", "bash",
    # Web Frameworks & Libraries
    "react", "react.js", "angular", "vue", "vue.js", "django", "flask", "fastapi", "spring", "spring boot", "laravel", "express", "node.js", "next.js", "nuxt", "svelte", "jquery", "bootstrap", "tailwind",
    # Data Science, AI & Machine Learning
    "machine learning", "deep learning", "nlp", "natural language processing", "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn", "scipy", "llm", "openai", "transformers", "langchain", "data science", "data analysis", "tableau", "power bi", "analytics",
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible", "git", "github", "gitlab", "bitbucket", "linux", "nginx", "apache",
    # Databases & Caching
    "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch", "sqlite", "mariadb", "cassandra", "dynamodb", "oracle", "sql server",
    # Methodologies & Tools
    "agile", "scrum", "jira", "confluence", "trello", "sdlc", "rest api", "graphql", "grpc", "microservices", "system design", "oop", "mvc"
]

def extract_name(text):
    """Extract candidate name using spaCy NER and structural heuristics."""
    doc = nlp(text[:500])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip().replace('\n', ' ')
            words = name.split()
            if 2 <= len(words) <= 3 and not any(char.isdigit() for char in name):
                if not any(w.lower() in ["resume", "curriculum", "vitae", "summary", "experience", "education"] for w in words):
                    return name
    
    # Fallback to looking at first few lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines[:5]:
        words = line.split()
        if 2 <= len(words) <= 3 and all(w[0].isupper() for w in words if w.isalpha()):
            if not any(w.lower() in ["resume", "curriculum", "vitae", "summary", "experience", "education", "profile", "contact", "email", "phone"] for w in words):
                return line
                
    return "Not Found"

def extract_email(text):
    """Extract email address."""
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0) if match else ""

def extract_phone(text):
    """Extract phone number."""
    match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    return match.group(0).strip() if match else ""

def extract_skills(text):
    """Extract and format skills matching our taxonomy."""
    found = []
    text_lower = text.lower()
    
    for skill in COMMON_SKILLS:
        skill_escaped = re.escape(skill)
        if '+' in skill or '.' in skill or '-' in skill:
            pattern = rf'(?:^|[\s,;:.()/])({skill_escaped})(?:$|[\s,;:.()/])'
        else:
            pattern = rf'\b{skill_escaped}\b'
            
        if re.search(pattern, text_lower):
            formatted_skill = skill
            if skill == "react.js":
                formatted_skill = "React"
            elif skill == "vue.js":
                formatted_skill = "Vue"
            elif skill == "spring boot":
                formatted_skill = "Spring Boot"
            else:
                if len(skill) <= 3 or skill in ["numpy", "scipy", "nginx", "html", "css", "sql", "aws", "gcp", "api", "rest", "mvc", "oop", "jira", "sdlc"]:
                    formatted_skill = skill.upper()
                else:
                    formatted_skill = skill.title()
            
            if formatted_skill not in found:
                found.append(formatted_skill)
                
    return sorted(found)

def extract_experience_years(text):
    """Extract total years of experience using regex patterns."""
    patterns = [
        r'(\d+(?:\.\d+)?|\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\b)\+?\s*(?:yr|year)s?\s*(?:of\s*)?experience',
        r'experience\s*:\s*(\d+(?:\.\d+)?)\+?\s*(?:yr|year)s?',
        r'total\s*(?:of\s*)?(\d+(?:\.\d+)?)\+?\s*(?:yr|year)s?'
    ]
    
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            years = []
            for m in matches:
                m_clean = m.strip().lower()
                if m_clean in word_to_num:
                    years.append(word_to_num[m_clean])
                else:
                    try:
                        years.append(float(m_clean))
                    except ValueError:
                        pass
            if years:
                max_years = max(years)
                if max_years.is_integer():
                    return int(max_years)
                return max_years
                
    match = re.search(r'\b(\d{1,2})\+?\s*(?:yr|year)s?\b', text, re.IGNORECASE)
    if match:
        val = int(match.group(1))
        if val < 40:
            return val
            
    return 0

def extract_experience_details(text):
    """Extract companies and roles from the resume text using structural headers."""
    sections = re.split(r'\n(?=[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s*\n)', text)
    exp_text = ""
    for sec in sections:
        lines = sec.strip().split('\n')
        if not lines:
            continue
        sec_header = lines[0].lower()
        if any(kw in sec_header for kw in ["experience", "work history", "employment", "professional background", "career history"]):
            exp_text = sec
            break
            
    if not exp_text:
        exp_text = text
        
    doc = nlp(exp_text[:2000])
    companies = []
    for ent in doc.ents:
        if ent.label_ == "ORG":
            org_name = ent.text.strip().replace('\n', ' ')
            org_lower = org_name.lower()
            if len(org_name) > 3 and not any(s in org_lower for s in ["university", "college", "school", "institute", "git", "python", "aws"]):
                org_cleaned = re.sub(r'\s+', ' ', org_name).strip()
                if org_cleaned not in companies:
                    companies.append(org_cleaned)
            elif any(s in org_lower for s in ["pvt", "ltd", "corporation", "corp", "inc", "llc"]):
                org_cleaned = re.sub(r'\s+', ' ', org_name).strip()
                if org_cleaned not in companies:
                    companies.append(org_cleaned)
                    
    companies = companies[:3]
    
    role_titles = [
        "Software Engineer", "Software Developer", "Frontend Developer", "Backend Developer", "Full Stack Developer",
        "Data Scientist", "Data Analyst", "Machine Learning Engineer", "DevOps Engineer", "Cloud Engineer",
        "Project Manager", "Product Manager", "Business Analyst", "System Administrator", "Quality Assurance Engineer",
        "QA Engineer", "UI/UX Designer", "Technical Architect", "Solutions Architect", "Consultant", "Intern"
    ]
    roles_found = []
    
    for line in exp_text.split('\n'):
        line_clean = line.strip()
        for role in role_titles:
            if role.lower() in line_clean.lower():
                if role not in roles_found:
                    roles_found.append(role)
                    
    if not roles_found:
        dynamic_matches = re.findall(r'\b(Senior|Junior|Lead|Principal|Associate)?\s*([A-Za-z]+)\s*(Engineer|Developer|Analyst|Manager|Designer|Consultant|Architect)\b', exp_text)
        for m in dynamic_matches:
            title = " ".join(m).strip()
            if len(title) > 5 and not any(w.lower() in ["company", "system", "technical"] for w in title.split()):
                if title not in roles_found:
                    roles_found.append(title)
                    
    roles_found = roles_found[:3]
    
    return {
        "years": extract_experience_years(text),
        "companies": companies if companies else ["Not specified"],
        "roles": roles_found if roles_found else ["Not specified"]
    }

def extract_education(text):
    """Extract education details including degree types and institutions."""
    sections = re.split(r'\n(?=[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s*\n)', text)
    edu_text = ""
    for sec in sections:
        lines = sec.strip().split('\n')
        if not lines:
            continue
        sec_header = lines[0].lower()
        if any(kw in sec_header for kw in ["education", "academic", "qualification", "university", "school", "degrees"]):
            edu_text = sec
            break
            
    if not edu_text:
        edu_text = text
        
    degrees = []
    degree_patterns = [
        (r'\bB\.?\s*S\.?\s*C\.?\b', "B.Sc"),
        (r'\bB\.?\s*E\.?\b', "B.E"),
        (r'\bB\.?\s*Tech\b', "B.Tech"),
        (r'\bM\.?\s*Tech\b', "M.Tech"),
        (r'\bM\.?\s*S\.?\b', "M.S"),
        (r'\bPh\.?\s*D\.?\b', "Ph.D"),
        (r'\bB\.?\s*A\.?\b', "B.A"),
        (r'\bM\.?\s*A\.?\b', "M.A"),
        (r'\bM\.?\s*B\.?\s*A\.?\b', "MBA"),
        (r'\bB\.?\s*C\.?\s*A\.?\b', "BCA"),
        (r'\bM\.?\s*C\.?\s*A\.?\b', "MCA"),
        (r'\bBachelor\s*of\s*[A-Za-z\s]+', None),
        (r'\bMaster\s*of\s*[A-Za-z\s]+', None)
    ]
    
    for pattern, name in degree_patterns:
        matches = re.findall(pattern, edu_text, re.IGNORECASE)
        for m in matches:
            val = name if name else m.strip().title()
            val = re.sub(r'\s+', ' ', val)
            if len(val) < 40 and val not in degrees:
                degrees.append(val)
                
    universities = []
    doc = nlp(edu_text[:2000])
    for ent in doc.ents:
        if ent.label_ == "ORG":
            text_clean = ent.text.strip().replace('\n', ' ')
            text_lower = text_clean.lower()
            if any(kw in text_lower for kw in ["university", "college", "institute", "school", "academy", "iit", "nit", "bits", "mit"]):
                text_cleaned = re.sub(r'\s+', ' ', text_clean).strip()
                if text_cleaned not in universities and len(text_cleaned) < 80:
                    universities.append(text_cleaned)
                    
    if not universities:
        for line in edu_text.split('\n'):
            line_clean = line.strip()
            if any(kw in line_clean.lower() for kw in ["university", "college", "institute", "school"]) and len(line_clean) < 80:
                if line_clean not in universities:
                    universities.append(line_clean)
                    
    return {
        "degrees": degrees if degrees else ["Not specified"],
        "institutions": universities if universities else ["Not specified"]
    }

def extract_projects_and_certs(text):
    """Count and extract lists of projects and certifications from the resume text."""
    sections = re.split(r'\n(?=[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s*\n)', text)
    
    project_list = []
    cert_list = []
    
    for sec in sections:
        lines = sec.strip().split('\n')
        if not lines:
            continue
        sec_header = lines[0].lower()
        
        # Parse Projects
        if any(kw in sec_header for kw in ["project", "portfolio", "key work"]):
            for line in lines[1:]:
                line_clean = line.strip()
                if line_clean.startswith(('•', '-', '*', 'o', '1.', '2.', '3.')):
                    # Extract list items
                    proj_name = re.sub(r'^[\s•\-*o0-9.\(\)]+', '', line_clean).strip()
                    if len(proj_name) > 10 and len(proj_name) < 120:
                        project_list.append(proj_name.split(':')[0]) # Get title
                elif 5 < len(line_clean) < 80 and line_clean.isupper():
                    project_list.append(line_clean)
                    
        # Parse Certifications
        if any(kw in sec_header for kw in ["certif", "award", "licens", "course"]):
            for line in lines[1:]:
                line_clean = line.strip()
                if line_clean.startswith(('•', '-', '*', 'o', '1.', '2.', '3.')):
                    cert_name = re.sub(r'^[\s•\-*o0-9.\(\)]+', '', line_clean).strip()
                    if len(cert_name) > 8 and len(cert_name) < 100:
                        cert_list.append(cert_name)
                elif 8 < len(line_clean) < 80:
                    cert_list.append(line_clean)
                    
    # Fallback to generic regex extraction if sections are missing
    if not project_list:
        # Match sentences like "worked on [Project]" or "developed [Project]"
        proj_matches = re.findall(rf'\b(?:built|developed|designed|implemented)\s+([A-Za-z0-9\s]+?)(?:\s+using|\s+with|\.|\,)', text, re.IGNORECASE)
        project_list = [m.strip().title() for m in proj_matches if len(m.strip()) > 5 and len(m.strip()) < 50][:3]
        
    if not cert_list:
        # Look for words like AWS Certified, Google Certified, Oracle, etc.
        cert_matches = re.findall(rf'\b([A-Za-z0-9\s]+?(?:Certified|Certification|Credential|License))\b', text, re.IGNORECASE)
        cert_list = [m.strip().title() for m in cert_matches if len(m.strip()) > 5][:3]
        
    # Clean duplicates
    project_list = list(set(project_list))[:4]
    cert_list = list(set(cert_list))[:4]
    
    return {
        "projects": project_list,
        "project_count": max(len(project_list), 1 if len(project_list) > 0 else 0),
        "certifications": cert_list,
        "cert_count": max(len(cert_list), 1 if len(cert_list) > 0 else 0)
    }

def extract_details(text):
    """Aggregate all candidate details from the text."""
    exp = extract_experience_details(text)
    edu = extract_education(text)
    extra = extract_projects_and_certs(text)
    
    # Parse formatting cues
    has_email = extract_email(text) != ""
    has_phone = extract_phone(text) != ""
    has_skills = len(extract_skills(text)) > 0
    has_edu = edu["degrees"][0] != "Not specified"
    has_exp = exp["roles"][0] != "Not specified"
    
    # Basic layout checker
    layout_score = 70
    if len(text) > 800:
        layout_score += 10
    if text.count('\n') > 15:
        layout_score += 10
    if len(text.split()) > 150:
        layout_score += 10
    layout_score = min(100, layout_score)
    
    ats_score = 0
    if has_email: ats_score += 15
    if has_phone: ats_score += 15
    if has_skills: ats_score += 15
    if has_edu: ats_score += 15
    if has_exp: ats_score += 15
    ats_score += int(layout_score * 0.25)
    
    return {
        "name": extract_name(text),
        "email": extract_email(text) or "Not Found",
        "phone": extract_phone(text) or "Not Found",
        "skills": extract_skills(text),
        "experience": exp,
        "education": edu,
        "projects": extra["projects"],
        "project_count": extra["project_count"],
        "certifications": extra["certifications"],
        "cert_count": extra["cert_count"],
        "ats_checklist": {
            "email_present": has_email,
            "phone_present": has_phone,
            "skills_present": has_skills,
            "education_present": has_edu,
            "experience_present": has_exp,
            "proper_formatting": layout_score >= 80
        },
        "ats_score": ats_score
    }
