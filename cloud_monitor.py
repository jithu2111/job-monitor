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
        "path": "README.md",
        "state_file": "state_speedy.txt"
    },
    {
        "name": "SimplifyJobs (Summer 2026)",
        "owner": "SimplifyJobs",
        "repo": "Summer2026-Internships",
        "branch": "dev",
        "path": "README.md",
        "state_file": "state_simplify.txt"
    }
]

# SECRETS
EMAIL_ADDRESS = os.environ.get("EMAIL_USER")
APP_PASSWORD = os.environ.get("EMAIL_PASS")
SEND_TO = os.environ.get("EMAIL_USER")
GH_TOKEN = os.environ.get("GH_TOKEN")

def get_headers():
    return {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_latest_commit(target):
    """Fetches the latest commit summary."""
    owner = target["owner"]
    repo = target["repo"]
    branch = target["branch"]
    path = target["path"]
    
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"sha": branch, "path": path, "per_page": 1}
    
    try:
        response = requests.get(url, headers=get_headers(), params=params)
        if response.status_code == 200:
            commits = response.json()
            if commits:
                return commits[0]
            return None
        print(f"Error fetching {target['name']}: {response.status_code}")
        return None
    except Exception as e:
        print(f"Network error on {target['name']}: {e}")
        return None

def get_commit_diff(target, sha):
    """Fetches the specific code changes (patch) for the file."""
    owner = target["owner"]
    repo = target["repo"]
    path = target["path"]
    
    # We need the specific commit details to get the 'patch' text
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            # Loop through files to find the one we are watching (README.md)
            for file in data.get('files', []):
                if file['filename'] == path:
                    return file.get('patch', "No text changes found (binary file or rename?)")
            return "File modified, but specific diff not found in commit."
        else:
            return f"Could not fetch diff. Status: {response.status_code}"
    except Exception as e:
        return f"Error fetching diff: {str(e)}"

def send_email(target, commit_data, diff_text):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 JOBS CHANGED: {target['name']}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = SEND_TO

    sha = commit_data['sha']
    message = commit_data['commit']['message']
    author = commit_data['commit']['author']['name']
    link = f"https://github.com/{target['owner']}/{target['repo']}/blob/{target['branch']}/{target['path']}"

    # We truncate the diff if it's too huge (to prevent email errors)
    if len(diff_text) > 3000:
        diff_text = diff_text[:3000] + "\n...[Diff truncated, click link to see more]..."

    body = (
        f"The README has been updated!\n\n"
        f"Commit Msg: {message}\n"
        f"Author: {author}\n"
        f"Link: {link}\n\n"
        f"--- CHANGES BELOW ---\n\n"
        f"{diff_text}"
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
    print("--- Multi-Repo Deep Monitor Started ---")
    
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
            print(f"--> Update found! Fetching diff...")
            
            # 4. FETCH THE DIFF (New Step)
            diff_text = get_commit_diff(target, current_sha)
            
            send_email(target, current_data, diff_text)
            
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
