# Made by Mehul Ambastha
from flask import Flask, request, jsonify
import os
from github import Github
from github import GithubIntegration
from dotenv import load_dotenv
from groq import Groq
from functools import wraps
import threading
import time
from database import has_already_commented, insert_comment_record

load_dotenv()

app = Flask(__name__)

pr_locks = {}


def get_pr_lock(repo_name, pr_number):
    lock_key = f"{repo_name}:{pr_number}"
    return pr_locks.setdefault(lock_key, threading.Lock())


# Github configuration
GITHUB_APP_ID = os.getenv('GITHUB_APP_ID')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')

# OPENAI configuration
groq_client = Groq(api_key=os.getenv('GROQ_KEY'))

# Setting up the app


@app.route('/webhook', methods=['POST'])
def webhook():
    # Will verify github signature now
    event = request.headers.get('X-Github-Event')
    if event == 'pull_request':
        payload = request.json

        if payload['action'] == 'opened':
            pr_number = payload['number']
            repo_name = payload['repository']['full_name']

            pr_lock = get_pr_lock(repo_name, pr_number)

            def process_with_lock():
                with pr_lock:
                    print('Processing payload.')
                    if not has_already_commented(repo_name, pr_number):
                        process_payload(payload)
                    else:
                        print(f'Already commented on PR #{
                              pr_number} in {repo_name}. Skipping...')

            # Start a new thread to process the payload
            threading.Thread(target=process_with_lock).start()

    return jsonify({'status': 'success'}), 200


def generate_github_bot_instance():

    with open(os.getenv('PATH_TO_PEM'), 'r') as key:
        GITHUB_APP_PRIVATE_KEY = key.read()

    payload = {
        "iat": int(time.time() + 60),
        "exp": int(time.time()) + (30*24*60*60),
        "iss": GITHUB_APP_ID
    }

    gb_integration = GithubIntegration(
        GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, base_url="https://api.github.com/")

    installations = gb_integration.get_installations()
    try:
        install_token = gb_integration.get_access_token(installations[0].id)
    except Exception as e:
        print('EXCEPTION', e)
    return Github(install_token.token)


instance = generate_github_bot_instance()


def process_payload(payload):
    pr_number = payload['number']
    repo_name = payload['repository']['full_name']

    pr_content = get_pr_content(repo_name, pr_number)
    # Generating the Analysis

    print('Generating Analyis...')
    analysis = generate_pr_analysis(pr_content)
    print('AI says: \n', analysis)
    # Posting it as comment

    print('Posting comment...')
    post_pr_comment(repo_name, pr_number, analysis)

    insert_comment_record(repo_name, pr_number)
    print('Commented.')


def get_pr_content(repo_name, pr_number):
    # USing Github API to fetch PR Content
    github_instance = Github(os.getenv('GITHUB_ACCESS_TOKEN'))
    repo = github_instance.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    files_changed = pr.get_files()

    pr_content = f"""
        Pull Requst #{pr_number} in {repo_name}
        Title: {pr.title}
        Description: {pr.body or '(No description provided'}

        Files Changed:
        """

    for file in files_changed:
        pr_content += f"\nFile {file.filename} (Status: {file.status}, Changes: +{
            file.additions} -{file.deletions})"
        pr_content += f"\nPatch:\n{file.patch}\n"

    return pr_content


def generate_pr_analysis(pr_content):
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a senior software engineer acting as a code reviewer. Your task is to review the contents of the given pull request carefully. Analyze the code for potential improvements, including code quality, readability, performance, security, and adherence to best practices. Identify any bugs or potential issues, suggest alternative implementations if needed, and provide constructive feedback. Explain your suggestions clearly so the author understands the rationale behind them. Do not mention in your analysis that you are a seniors software engineer. Answer in Markdown."},
            {"role": "user", "content": pr_content}
        ]
    )
    return response.choices[0].message.content


def post_pr_comment(repo_name, pr_number, comment):
    github_instance = generate_github_bot_instance()
    repo = github_instance.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(comment)


if __name__ == '__main__':
    app.run(debug=True)
