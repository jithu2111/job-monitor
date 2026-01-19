import requests
import smtplib
import os
import sys
from email.message import EmailMessage

# --- CONFIGURATION ---
TARGETS = [
    {
        "name": "SpeedyApply (2026 Jobs)",
        "owner": "speedyapply",
        "repo": "2026-SWE-College-Jobs",
        "branch": "main",
        "path": "README.md",          # STRICTLY monitor Readme
        "state_file": "state_speedy.txt"
    },
    {
        "name": "SimplifyJobs (Summer 2026)",
        "owner": "SimplifyJobs",
        "repo": "Summer2026-Internships",
        "branch": "dev",              # They usually update 'dev' first
        "path": "README.md",          # STRICTLY monitor Readme
        "state_file": "state_simplify.txt"
    }
]

# SECRETS
EMAIL_ADDRESS = os.environ.get("EMAIL_USER")
APP_PASSWORD = os.environ.get("EMAIL_PASS")
SEND_TO = os.environ.get("EMAIL_USER")
GH_TOKEN = os.environ.get("GH_TOKEN")

def get_latest_commit(target):
    """Fetches the latest commit for a SPECIFIC FILE."""
    owner = target["owner"]
    repo = target["repo"]
    branch = target["branch"]
    path = target["path"]
    
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # We use the 'commits' endpoint with a 'path' filter
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"sha": branch, "path": path, "per_page": 1}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            commits = response.json()
            if commits:
                return commits[0] # Return the latest commit object
            return None
        
        print(f"Error fetching {target['name']}: {response.status_code}")
        return None
    except Exception as e:
        print(f"Network error on {target['name']}: {e}")
        return None

def send_email(target, commit_data):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 NEW JOBS: {target['name']}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = SEND_TO

    sha = commit_data['sha']
    message = commit_data['commit']['message']
    author = commit_data['commit']['author']['name']
    
    # Direct link to the file so you can see the diff immediately
    link = f"https://github.com/{target['owner']}/{target['repo']}/blob/{target['branch']}/{target['path']}"

    body = (
        f"The README has changed in {target['name']}!\n\n"
        f"Commit: {message}\n"
        f"Author: {author}\n"
        f"Check the list here: {link}"
    )
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent for {target['name']}.")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def main():
    print("--- Multi-Repo Readme Check Started ---")
    
    changes_detected = False

    for target in TARGETS:
        print(f"Checking {target['name']}...")
        
        # 1. Read last state
        last_sha = ""
        if os.path.exists(target['state_file']):
            with open(target['state_file'], 'r') as f:
                last_sha = f.read().strip()

        # 2. Fetch current state
        current_data = get_latest_commit(target)
        if not current_data:
            continue
            
        current_sha = current_data['sha']
        
        # 3. Compare
        if last_sha != current_sha:
            print(f"--> Update found! {last_sha[:7]} -> {current_sha[:7]}")
            send_email(target, current_data)
            
            # Update state file
            with open(target['state_file'], 'w') as f:
                f.write(current_sha)
            changes_detected = True
        else:
            print("--> No changes.")
            
    if not changes_detected:
        print("No changes in any targets.")

if __name__ == "__main__":
    main()
