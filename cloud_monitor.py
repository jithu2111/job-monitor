import requests
import smtplib
import os
import sys
from email.message import EmailMessage

# --- CONFIGURATION ---
REPO_OWNER = "speedyapply"
REPO_NAME = "2026-SWE-College-Jobs"
BRANCH = "main"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits/{BRANCH}"

# SECRETS
EMAIL_ADDRESS = os.environ.get("EMAIL_USER")
APP_PASSWORD = os.environ.get("EMAIL_PASS")
SEND_TO = os.environ.get("EMAIL_USER")
# GRAB THE TOKEN
GH_TOKEN = os.environ.get("GH_TOKEN") 

STATE_FILE = "last_commit.txt"

def get_latest_commit():
    # If we don't have a token, the script will likely fail with 403
    if not GH_TOKEN:
        print("⚠️ Warning: No GH_TOKEN found. Request might be blocked.")
        headers = {}
    else:
        headers = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

    try:
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            return response.json()
        print(f"Error: {response.status_code} - {response.text}") # Print detail if it fails
        return None
    except Exception as e:
        print(f"Network error: {e}")
        return None

def send_email(commit_data):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 JOB REPO UPDATE!"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = SEND_TO

    sha = commit_data['sha']
    message = commit_data['commit']['message']
    link = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"

    body = f"New Update!\n\nCommit: {message}\nSHA: {sha}\n\nLink: {link}"
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ Email sent.")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def main():
    print("--- Cloud Check Started ---")
    
    # 1. Read the previous commit
    last_sha = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            last_sha = f.read().strip()

    # 2. Get current commit
    current_data = get_latest_commit()
    if not current_data:
        sys.exit(1) # Stop here if 403 happens
        
    current_sha = current_data['sha']
    
    # 3. Compare
    if last_sha != current_sha:
        print(f"Update detected! {last_sha} -> {current_sha}")
        send_email(current_data)
        
        with open(STATE_FILE, 'w') as f:
            f.write(current_sha)
    else:
        print("No changes detected.")

if __name__ == "__main__":
    main()
