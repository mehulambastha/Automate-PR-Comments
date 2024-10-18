# Automatic-PR-Comments

This project automates the process of reviewing code changes in pull requests on GitHub using a Flask web server, GitHub's API, Groq AI for analysis, and TinyDB as a local database. The bot listens for pull request events, generates feedback based on the PR's contents, and posts a comment on the pull request.

---
### [Link](https://github.com/mehulambastha/AutoPR-Reviewer-Bot-Install) to Frontend for installing the bot on your repos.
---

## Features
- Automatically comments on new pull requests with an AI-generated code review.
- Uses threading and locking mechanisms to prevent race conditions.
- Keeps track of processed pull requests to avoid duplicate comments.
- Lightweight, using TinyDB for local data storage.

## Table of Contents
1. [Setup](#setup)
2. [Environment Variables](#environment-variables)
3. [Handling Race Conditions](#handling-race-conditions)
4. [Database Explanation](#database-explanation)
5. [Project Structure](#project-structure)
6. [Usage](#usage)
7. [How It Works](#how-it-works)

## Setup

### Prerequisites
- Python 3.8+
- `pip` for Python package management
- A GitHub App with appropriate permissions

### Installing Dependencies
1. Clone the repository:
   ```bash
   git clone https://github.com/mehulambastha/Automate-PR-Comments
   cd Automatic-PR-Comments
   ```

2. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the GitHub App by following the [GitHub App creation guide](https://docs.github.com/en/developers/apps/building-github-apps/creating-a-github-app).

### Generating Necessary Files and Keys
1. **GitHub App Keys:**
   - Generate a private key for your GitHub App.
   - Save the private key file path for configuring environment variables.

2. **Setting Up TinyDB:**
   - The project uses TinyDB as a local database for tracking processed pull requests.
   - The database is stored in a JSON file named `comments.json`, which will be created automatically when the application runs.

## Environment Variables

Create a `.env` file in the root directory of the project and populate it with the following variables:

```env
GITHUB_APP_ID=<your-github-app-id>
GITHUB_WEBHOOK_SECRET=<your-github-webhook-secret>
GROQ_KEY=<your-groq-api-key>
PATH_TO_PEM=<path-to-your-github-app-private-key.pem>
GITHUB_ACCESS_TOKEN=<your-personal-access-token-for-fetching-pr-content>
```

- `GITHUB_APP_ID`: The App ID from your GitHub App settings.
- `GITHUB_WEBHOOK_SECRET`: The secret key used for verifying the webhook signature.
- `GROQ_KEY`: API key for accessing Groq services for generating code review analysis.
- `PATH_TO_PEM`: Path to the GitHub App's private key file.
- `GITHUB_ACCESS_TOKEN`: Personal access token for accessing repository details (not used for posting comments).

## Handling Race Conditions

### Explanation of the Race Condition
When multiple webhook events arrive simultaneously (e.g., multiple pull requests opened at the same time), the program may attempt to comment on the same pull request more than once. This can happen because separate threads are processing the events concurrently without coordinating.

### Locking Mechanism
To address this, we use a lock mechanism:
- Each pull request has a dedicated lock, created using a combination of `repo_name` and `pr_number` as the key.
- When processing a pull request, the corresponding lock ensures that only one thread can execute the code for a particular PR at any given time.
- The locking mechanism prevents race conditions by blocking simultaneous access to shared resources (TinyDB).

The locking mechanism in the code is implemented using Python's `threading.Lock()`.

## Database Explanation

### Using TinyDB
TinyDB is a lightweight, document-oriented database that stores data in a JSON file. It is ideal for small projects where a traditional database like SQLite or PostgreSQL may be overkill.

#### Database Structure
The database, stored in `comments.json`, tracks pull requests that have already been commented on to avoid duplicate comments.

#### Operations
- **`has_already_commented(repo_name, pr_number)`**: Checks if a comment has already been made on the given pull request.
- **`insert_comment_record(repo_name, pr_number)`**: Records that a comment has been made on the given pull request.

TinyDB automatically creates the `comments.json` file if it does not already exist, making the setup process easier.

## Project Structure
```plaintext
Automatic-PR-Comments/
├── app.py             # Main application file
├── database.py        # Database operations
├── requirements.txt   # Dependencies for the project
├── .env               # Environment variables
├── comments.json      # TinyDB database file (generated automatically)
└── README.md          # Documentation
```

## Usage
1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Configure the GitHub repository to send webhook events to the running server's `/webhook` endpoint (e.g., `http://your-server-address/webhook`).

3. Open a new pull request in the configured GitHub repository. The bot will automatically comment on it.

## How It Works
1. **Webhook Handling (`/webhook`):**
   - Listens for `pull_request` events from GitHub.
   - If the event action is `opened`, it checks whether the bot has already commented on the PR.
   - Uses a lock to prevent multiple threads from processing the same PR simultaneously.
   
2. **GitHub Bot Instance Generation:**
   - The bot authenticates using a private key to obtain an installation access token for the GitHub App.
   
3. **Pull Request Processing:**
   - Fetches the PR content (title, description, and changed files).
   - Uses Groq to analyze the content and suggest improvements.
   - Posts the analysis as a comment on the PR.
   - Records the PR in TinyDB to prevent duplicate comments.
  
## For Local Testing
You can use NGROK to generate a temporary domain mirroring your local app

## Conclusion

This project demonstrates an end-to-end automated workflow for code review using GitHub's API, AI analysis, and Flask web server. The implementation addresses potential concurrency issues by using a locking mechanism to avoid race conditions. TinyDB serves as a convenient, easy-to-use local storage for tracking processed pull requests.
