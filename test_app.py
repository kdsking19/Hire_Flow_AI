import requests

def test_screener():
    url = "http://127.0.0.1:5000/analyze"
    files = {"resume": ("sample_resume.docx", open("sample_resume.docx", "rb"))}
    data = {
        "job_description": (
            "Senior Full Stack Engineer\n"
            "Key Requirements:\n"
            "- 5+ years of experience as a software engineer.\n"
            "- Proficient in Python, Flask, React, and AWS cloud deployment.\n"
            "- Experience with Docker, PostgreSQL, and Git version control.\n"
            "- Experience with Kubernetes or FastAPI is a plus."
        )
    }

    try:
        print("Sending POST request to Flask app...")
        r = requests.post(url, files=files, data=data, timeout=10)
        print("Status Code:", r.status_code)
        if r.status_code == 200:
            print("Response successfully received!")
            html = r.text
            
            # Check for critical outputs in template rendering
            checks = [
                "Jane Doe",
                "jane.doe@example.com",
                "123-456-7890",
                "Match Score",
                "Tool Skill Alignment",
                "Evaluation Summary"
            ]
            
            all_passed = True
            for check in checks:
                if check in html:
                    print(f"[SUCCESS] Found: '{check}'")
                else:
                    print(f"[FAIL] Missing: '{check}'")
                    all_passed = False
                    
            if all_passed:
                print("\nAll integration checks passed perfectly!")
            else:
                print("\nSome checks failed. Review output HTML details.")
        else:
            print("Failed request, response HTML:")
            print(r.text[:1000])
    except Exception as e:
        print("Error during request:", e)

if __name__ == "__main__":
    test_screener()
