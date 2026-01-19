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
        # URL from your screenshot
        "url": "https://jobright.ai/swan/recommend/list/jobs?refresh=true&sortCondition=1&position=0&count=20",
        
        "headers": {
            # PASTE YOUR COOKIE HERE AGAIN (The one you used last time)
            'Cookie': '_ga=GA1.1.1185743235.1753715893; _tt_enable_cookie=1; _ttp=01K18SST7WQYXK8QWXJ06B6WPA_.tt.1; _clck=1kcuafb%5E2%5Efyz%5E0%5E2035; _uetvid=13eca1e06bc611f0b03a6f669781a09a; ttcsid_CM0IJ53C77U0797CAP10=1756847259998::zILEIuOOJh22OQB1vBWl.13.1756847316123; ttcsid=1756847259998::Asx0Ifw7QWE_r57eP2Rt.13.1756847316123; _ga_ETKKWETCJD=GS2.1.s1756847259$o19$g1$t1756847323$j60$l0$h1369803158; SESSION_ID=36ca7972e736482b96d8d1e7181d5d47; g_state={"i_l":0,"i_ll":1766900985700,"i_b":"lI5/EvGL/oPmqi5JEzK+l+P+ZB8445SKbYlciuYxw2w","i_e":{"enable_itp_optimization":0}}',
            
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://jobright.ai/jobs/recommend"
        },
        "state_file": "state_jobright.txt"
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
                # If monitoring a specific file, skip others
                if target['path'] and target['path'] not in f['filename']:
                    continue
                
                # Get the 'patch' (the diff string)
                patch = f.get('patch', '')
                if not patch: continue
                
                # Filter for lines that start with '+' (Added lines)
                added_lines = []
                for line in patch.split('\n'):
                    # We look for lines starting with + but ignore the header +++
                    if line.startswith('+') and not line.startswith('+++'):
                        # Clean up the line for the email
                        clean_line = line[1:].strip() 
                        # Skip empty lines or trivial changes
                        if len(clean_line) > 5: 
                            added_lines.append(clean_line)
                
                if added_lines:
                    diff_text += f"\n📂 In {f['filename']}:\n"
                    for line in added_lines:
                        diff_text += f"🟢 {line}\n"
            
            return diff_text if diff_text else "No content additions detected (maybe just deletions?)."
    except Exception as e:
        return f"Could not fetch diff details: {e}"
    return "No details available."

def get_github_update(target):
    headers = {"Authorization": f"token {GH_TOKEN}"}
    url = f"https://api.github.com/repos/{target['owner']}/{target['repo']}/commits"
    params = {"sha": target['branch'], "path": target['path'], "per_page": 1}
    
    try:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200 and r.json():
            commit = r.json()[0]
            sha = commit['sha']
            msg = commit['commit']['message']
            
            # Return basic info, we will fetch the diff later if it's new
            return {
                "id": sha,
                "msg": msg,
                "link": f"https://github.com/{target['owner']}/{target['repo']}/commit/{sha}",
                "timestamp": commit['commit']['author']['date']
            }
    except Exception as e:
        print(f"GitHub Error {target['name']}: {e}")
    return None

def get_api_update(target):
    """Fetches private API and hashes the result."""
    try:
        r = requests.get(target['url'], headers=target['headers'])
        if r.status_code == 200:
            data_hash = hashlib.md5(r.text.encode('utf-8')).hexdigest()
            return {"id": data_hash, "msg": "JobRight Feed Updated", "link": "https://jobright.ai/jobs/recommend", "details": "New recommendations available in your feed."}
        else:
            print(f"API Error {target['name']}: {r.status_code}")
    except Exception as e:
        print(f"API Network Error: {e}")
    return None

def send_email(target, data, diff_details=""):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 NEW JOBS: {target['name']}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = SEND_TO
    
    # Construct the body
    body = f"Update detected in {target['name']}!\n\n"
    body += f"Commit Message: {data['msg']}\n"
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
    except Exception as e:
        print(f"❌ Email failed: {e}")

def main():
    print("--- Advanced Cloud Monitor ---")
    changes_detected = False

    for target in TARGETS:
        print(f"Checking {target['name']}...")
        
        # 1. Fetch Current Data
        if target['type'] == 'github':
            current_data = get_github_update(target)
        else:
            current_data = get_api_update(target)

        if not current_data:
            continue

        # 2. Read Last State
        last_id = ""
        if os.path.exists(target['state_file']):
            with open(target['state_file'], 'r') as f:
                last_id = f.read().strip()

        # 3. Compare
        if last_id != current_data['id']:
            print(f"--> Update found for {target['name']}!")
            
            # EXTRA STEP: If it's GitHub, fetch the Diff details
            diff_text = ""
            if target['type'] == 'github':
                print("   Fetching specific file changes...")
                diff_text = get_github_diff(target, current_data['id'])
            
            send_email(target, current_data, diff_text)
            
            # Save new state
            with open(target['state_file'], 'w') as f:
                f.write(current_data['id'])
            changes_detected = True
        else:
            print("--> No changes.")
            
    if not changes_detected:
        print("Done. No updates.")

if __name__ == "__main__":
    main()
