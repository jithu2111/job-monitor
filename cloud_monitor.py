import requests
import smtplib
import os
import hashlib
import json
from email.message import EmailMessage

# --- CONFIGURATION ---
TARGETS = [
    # 1. SpeedyApply (GitHub) - Monitoring README.md
    {
        "type": "github",
        "name": "SpeedyApply (2026 Jobs)",
        "owner": "speedyapply",
        "repo": "2026-SWE-College-Jobs",
        "branch": "main",
        "path": "README.md",
        "state_file": "state_speedy.txt"
    },
    # 2. SimplifyJobs (GitHub) - Monitoring README.md
    {
        "type": "github",
        "name": "SimplifyJobs (Summer 2026)",
        "owner": "SimplifyJobs",
        "repo": "Summer2026-Internships",
        "branch": "dev",
        "path": "README.md",
        "state_file": "state_simplify.txt"
    },
    # 3. JobRight (Private API) - Monitoring your personal feed
    {
        "type": "api",
        "name": "JobRight Recommendations",
        # The URL from your screenshot
        "url": "https://jobright.ai/swan/recommend/list/jobs?refresh=true&sortCondition=1&position=0&count=20",
        
        "headers": {
            # YOUR COOKIE (I used single quotes to handle the double quotes inside your cookie)
            'Cookie': '_ga=GA1.1.1185743235.1753715893; _tt_enable_cookie=1; _ttp=01K18SST7WQYXK8QWXJ06B6WPA_.tt.1; _clck=1kcuafb%5E2%5Efyz%5E0%5E2035; _uetvid=13eca1e06bc611f0b03a6f669781a09a; ttcsid_CM0IJ53C77U0797CAP10=1756847259998::zILEIuOOJh22OQB1vBWl.13.1756847316123; ttcsid=1756847259998::Asx0Ifw7QWE_r57eP2Rt.13.1756847316123; _ga_ETKKWETCJD=GS2.1.s1756847259$o19$g1$t1756847323$j60$l0$h1369803158; SESSION_ID=36ca7972e736482b96d8d1e7181d5d47; g_state={"i_l":0,"i_ll":1766900985700,"i_b":"lI5/EvGL/oPmqi5JEzK+l+P+ZB8445SKbYlciuYxw2w","i_e":{"enable_itp_optimization":0}}',
            
            # Pretending to be your Mac
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

def get_github_update(target):
    """Fetches latest commit SHA from GitHub."""
    headers = {"Authorization": f"token {GH_TOKEN}"}
    url = f"https://api.github.com/repos/{target['owner']}/{target['repo']}/commits"
    params = {"sha": target['branch'], "path": target['path'], "per_page": 1}
    
    try:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200 and r.json():
            return {"id": r.json()[0]['sha'], "msg": r.json()[0]['commit']['message'], "link": f"https://github.com/{target['owner']}/{target['repo']}/blob/{target['branch']}/{target['path']}"}
    except Exception as e:
        print(f"GitHub Error {target['name']}: {e}")
    return None

def get_api_update(target):
    """Fetches private API and hashes the result to detect changes."""
    try:
        r = requests.get(target['url'], headers=target['headers'])
        if r.status_code == 200:
            # Create a hash of the data so we can detect changes
            data_hash = hashlib.md5(r.text.encode('utf-8')).hexdigest()
            # Direct link to the UI for you to click
            web_link = "https://jobright.ai/jobs/recommend"
            return {"id": data_hash, "msg": "New Job List Detected", "link": web_link}
        else:
            print(f"API Error {target['name']}: {r.status_code} - Cookie might be expired.")
    except Exception as e:
        print(f"API Network Error: {e}")
    return None

def send_email(target, data):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 UPDATE: {target['name']}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = SEND_TO
    
    body = f"Change detected in {target['name']}!\n\nDetails: {data['msg']}\nID: {data['id']}\nLink: {data['link']}"
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent for {target['name']}.")
    except Exception:
        pass

def main():
    print("--- Universal Cloud Monitor ---")
    changes = False

    for target in TARGETS:
        print(f"Checking {target['name']}...")
        
        # 1. Fetch Data
        if target['type'] == 'github':
            current_data = get_github_update(target)
        else:
            current_data = get_api_update(target)

        if not current_data:
            continue

        # 2. Compare with local state
        last_id = ""
        if os.path.exists(target['state_file']):
            with open(target['state_file'], 'r') as f:
                last_id = f.read().strip()

        if last_id != current_data['id']:
            print(f"--> Update found for {target['name']}!")
            send_email(target, current_data)
            with open(target['state_file'], 'w') as f:
                f.write(current_data['id'])
            changes = True
        else:
            print("--> No changes.")
    
    if not changes:
        print("Done. No updates.")

if __name__ == "__main__":
    main()
