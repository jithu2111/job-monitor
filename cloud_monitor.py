import requests
import smtplib
import os
import hashlib
from email.message import EmailMessage

# --- CONFIGURATION ---
TARGETS = [
    # 1. SpeedyApply (GitHub)
    {
        "type": "github",
        "name": "SpeedyApply (2026 Jobs)",
        "owner": "speedyapply",
        "repo": "2026-SWE-College-Jobs",
        "branch": "main",
        "path": "README.md",
        "state_file": "state_speedy.txt"
    },
    # 2. SimplifyJobs (GitHub)
    {
        "type": "github",
        "name": "SimplifyJobs (Summer 2026)",
        "owner": "SimplifyJobs",
        "repo": "Summer2026-Internships",
        "branch": "dev",
        "path": "README.md",
        "state_file": "state_simplify.txt"
    },
    # 3. JobRight (Private API)
    {
        "type": "api",
        "name": "JobRight Recommendations",
        "url": "https://jobright.ai/swan/recommend/list/jobs?refresh=true&sortCondition=1&position=0&count=20",
        "headers": {
            # PASTE YOUR JOBRIGHT COOKIE HERE
            'Cookie': '_ga=GA1.1.1185743235.1753715893; _tt_enable_cookie=1; _ttp=01K18SST7WQYXK8QWXJ06B6WPA_.tt.1; _clck=1kcuafb%5E2%5Efyz%5E0%5E2035; _uetvid=13eca1e06bc611f0b03a6f669781a09a; ttcsid_CM0IJ53C77U0797CAP10=1756847259998::zILEIuOOJh22OQB1vBWl.13.1756847316123; ttcsid=1756847259998::Asx0Ifw7QWE_r57eP2Rt.13.1756847316123; _ga_ETKKWETCJD=GS2.1.s1756847259$o19$g1$t1756847323$j60$l0$h1369803158; SESSION_ID=36ca7972e736482b96d8d1e7181d5d47; g_state={"i_l":0,"i_ll":1766900985700,"i_b":"lI5/EvGL/oPmqi5JEzK+l+P+ZB8445SKbYlciuYxw2w","i_e":{"enable_itp_optimization":0}}',
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Referer": "https://jobright.ai/jobs/recommend"
        },
        "state_file": "state_jobright.txt"
    },
    # 4. Levels.fyi (Private API)
    {
        "type": "api",
        "name": "Levels.fyi Internships",
        # I extracted this from your previous screenshot. It searches: US, Internship, Posted last 1 day.
        "url": "https://api.levels.fyi/v1/job/search?limitPerCompany=3&limit=50&offset=0&sortBy=relevance&postedAfterTimeType=days&postedAfterValue=1&locationSlugs%5B%5D=united-states&jobLevels%5B%5D=internship",
        "headers": {
            # ACTION REQUIRED: Paste the 'Authorization' value from your 'job-alert' screenshot here!
            # It must start with "Bearer eyJ..."
            "Authorization": "Bearer eyJraWQiOiJJaFplZEtLU3hDVkFDSmJaMTkra1wvQVJNWm5yVHZiMDZlYTZTMGFOeXo4UT0iLCJhbGciOiJSUzI1NiJ9.eyJhdF9oYXNoIjoiOWIwU2lKWEZGYU9XVHhqa1hidGVEUSIsInN1YiI6IjE3MzkzMWYxLTlhMmEtNDIzMS04MTY1LTE5Y2Y0OTNhMzg0OCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtd2VzdC0yLmFtYXpvbmF3cy5jb21cL3VzLXdlc3QtMl9mVWNmelNHZHYiLCJjb2duaXRvOnVzZXJuYW1lIjoiMTczOTMxZjEtOWEyYS00MjMxLTgxNjUtMTljZjQ5M2EzODQ4Iiwibm9uY2UiOiItM2JUWXpFQUxIeFFEX3BDQXhLNlFrZ1RJX2Z0RW9VdHdMZ0dLdmh3NG9zRWtJNTFUc2F2dy1meWlnNTNjXzhtUXk0bHNWZWhzam14RGF5ektxV2dadFM3MDI3Z1JkNXlheUtIVmpxbGhWdGhxMVlIZE1heVFac1RVSjVZY0NkSjMwT0hCOHl1b05uZGRjbW1wOXVzYVZsa1dqdHlOaE96N0JGYXpwNkc3Zk0iLCJhdWQiOiI3Nm9mMGljaDE4aGQ4dWVoanU3Zm5pdjJ1MSIsImlkZW50aXRpZXMiOlt7InVzZXJJZCI6IjExMTU5NzgwMTA5ODU5ODY0MzMwMCIsInByb3ZpZGVyTmFtZSI6Ikdvb2dsZSIsInByb3ZpZGVyVHlwZSI6Ikdvb2dsZSIsImlzc3VlciI6bnVsbCwicHJpbWFyeSI6ImZhbHNlIiwiZGF0ZUNyZWF0ZWQiOiIxNzU2Nzc3MTY3MTcyIn1dLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTc2ODg3MTUyMiwiZXhwIjoxNzY4OTU3OTIyLCJpYXQiOjE3Njg4NzE1MjIsImVtYWlsIjoicHJhamVldGguY2hhbm5hQGdtYWlsLmNvbSJ9.d3Y3IWe_q2JfQ-zZNavw0R2Cl5QNWAozQUqOF2M90tReHRCV3pPaYFFxUDfZE8Kcrx8jM6rE6tZb8QiolwhlRHxpLbAvpWqfaEe02p0AnEQtMT1U6ZI84zfNc8rKarVH7w4SKTG4zFI0fsBGNhRFmCWyEMFW61EOO-nnQC1OPPJXMIAtuy16ekMtAF1Ef0rec_LOXDb-jCOqGgtncMonVZq4ea2eQjYGNj9Rg6MkyCcCXAC1WpERNAsnG3GveW5QP5GZotrdseJ7eKyOG2mDtrlPV0hBpWO_oEQqN9LyPVn6ZJB3qU1AquwV_jmwcaNoSgYzFZIGgf7us1OppoDNTQ",
            
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.levels.fyi",
            "Referer": "https://www.levels.fyi/"
        },
        "state_file": "state_levels.txt"
    }
]

# SECRETS
EMAIL_ADDRESS = os.environ.get("EMAIL_USER")
APP_PASSWORD = os.environ.get("EMAIL_PASS")
SEND_TO = os.environ.get("EMAIL_USER")
GH_TOKEN = os.environ.get("GH_TOKEN")

def get_github_diff(target, commit_sha):
    """Fetches the specific lines that changed in a commit."""
    url = f"https://api.github.com/repos/{target['owner']}/{target['repo']}/commits/{commit_sha}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            files = r.json().get('files', [])
            diff_text = ""
            for f in files:
                if target['path'] and target['path'] not in f['filename']:
                    continue
                patch = f.get('patch', '')
                if not patch: continue
                added_lines = []
                for line in patch.split('\n'):
                    if line.startswith('+') and not line.startswith('+++'):
                        clean_line = line[1:].strip() 
                        if len(clean_line) > 5: 
                            added_lines.append(clean_line)
                if added_lines:
                    diff_text += f"\n📂 In {f['filename']}:\n"
                    for line in added_lines:
                        diff_text += f"🟢 {line}\n"
            return diff_text if diff_text else "No content additions detected."
    except Exception:
        return "No details available."
    return "No details available."

def get_github_update(target):
    headers = {"Authorization": f"token {GH_TOKEN}"}
    url = f"https://api.github.com/repos/{target['owner']}/{target['repo']}/commits"
    params = {"sha": target['branch'], "path": target['path'], "per_page": 1}
    try:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200 and r.json():
            commit = r.json()[0]
            return {
                "id": commit['sha'],
                "msg": commit['commit']['message'],
                "link": f"https://github.com/{target['owner']}/{target['repo']}/commit/{commit['sha']}"
            }
    except Exception as e:
        print(f"GitHub Error {target['name']}: {e}")
    return None

def get_api_update(target):
    """Fetches private API and hashes the result."""
    try:
        # Standard GET request for both JobRight and Levels
        r = requests.get(target['url'], headers=target['headers'])

        if r.status_code == 200:
            # Hash the response to detect changes
            data_hash = hashlib.md5(r.text.encode('utf-8')).hexdigest()
            
            # Determine which link to send in the email
            if "Levels" in target['name']:
                web_link = "https://www.levels.fyi/jobs/location/united-states/level/internship"
            else:
                web_link = "https://jobright.ai/jobs/recommend"
            
            return {"id": data_hash, "msg": "New Jobs Detected", "link": web_link}
        else:
            print(f"API Error {target['name']}: {r.status_code}")
    except Exception as e:
        print(f"API Network Error on {target['name']}: {e}")
    return None

def send_email(target, data, diff_details=""):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 NEW JOBS: {target['name']}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = SEND_TO
    
    body = f"Update detected in {target['name']}!\n\n"
    body += f"Link: {data['link']}\n\n"
    
    if diff_details:
        body += "-------- WHAT CHANGED --------\n"
        body += diff_details
        body += "\n------------------------------\n"
    
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent for {target['name']}.")
    except Exception:
        pass

def main():
    print("--- Universal Cloud Monitor v4 ---")
    changes = False

    for target in TARGETS:
        print(f"Checking {target['name']}...")
        
        if target['type'] == 'github':
            current_data = get_github_update(target)
        else:
            current_data = get_api_update(target)

        if not current_data:
            continue

        state_file = target['state_file']
        last_id = ""
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                last_id = f.read().strip()

        if last_id != current_data['id']:
            print(f"--> Update found for {target['name']}!")
            
            diff_text = ""
            if target['type'] == 'github':
                diff_text = get_github_diff(target, current_data['id'])
            
            send_email(target, current_data, diff_text)
            
            with open(state_file, 'w') as f:
                f.write(current_data['id'])
            changes = True
        else:
            print("--> No changes.")
            
    if not changes:
        print("Done. No updates.")

if __name__ == "__main__":
    main()
