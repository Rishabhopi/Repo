import os
import re
import requests
import zipfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Function to download a single repository
def download_repo(repo_url, download_path):
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        return False, "Invalid GitHub repository link."

    username, repo_name = match.groups()
    zip_url = f"https://github.com/{username}/{repo_name}/archive/refs/heads/main.zip"

    response = requests.get(zip_url)
    if response.status_code != 200:
        return False, "Repository not found or main branch does not exist."

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    zip_path = os.path.join(download_path, f"{repo_name}.zip")
    with open(zip_path, "wb") as file:
        file.write(response.content)

    return True, zip_path

# Function to download all repositories of a user
def download_repos(username, download_path):
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)
    repos = response.json()

    if response.status_code != 200 or not repos:
        return False, "Invalid username or no repositories found."

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    for repo in repos:
        repo_name = repo['name']
        zip_url = repo['clone_url'].replace(".git", "/archive/refs/heads/main.zip")
        response = requests.get(zip_url)
        with open(f"{download_path}/{repo_name}.zip", "wb") as f:
            f.write(response.content)

    return True, "Repositories downloaded successfully."

# Start command handler
def start(update: Update, context: CallbackContext):
    buttons = [
        [InlineKeyboardButton("GitHub", url="https://github.com"), 
         InlineKeyboardButton("Developer", url="https://t.me/rishu1286")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    start_message = (
        "🤖 *Welcome to GitHub Repo Downloader Bot!*\n\n"
        "🔹 Send me:\n"
        "1️⃣ A GitHub username (e.g., `octocat`), and I'll fetch all their public repositories.\n"
        "2️⃣ A specific repository link (e.g., `https://github.com/octocat/Hello-World`).\n\n"
        "⚠️ Note: Ensure the repository or username exists and is public.\n"
    )
    update.message.reply_text(start_message, parse_mode="Markdown", reply_markup=reply_markup)

# Function to handle input
def fetch_repos(update: Update, context: CallbackContext):
    input_text = update.message.text.strip()
    download_path = f"downloads/{update.message.chat_id}"

    # Check if input is a GitHub repository link
    if re.match(r"https?://github\.com/([^/]+)/([^/]+)", input_text):
        update.message.reply_text("🔄 Fetching the repository...", parse_mode="Markdown")
        success, result = download_repo(input_text, download_path)

        if not success:
            update.message.reply_text(f"❌ {result}")
            return

        zip_path = result
        with open(zip_path, "rb") as file:
            update.message.reply_document(
                file,
                caption=f"✅ *Here is your repository:* `{input_text}`\n\n🔹 Powered by @rishu1286",
                parse_mode="Markdown",
            )

    else:  # Assume it's a GitHub username
        update.message.reply_text(f"🔄 Fetching repositories for GitHub username: *{input_text}*...", parse_mode="Markdown")
        success, message = download_repos(input_text, download_path)

        if not success:
            update.message.reply_text(f"❌ {message}")
            return

        zip_filename = f"{input_text}_repos.zip"
        zip_path = f"{download_path}/{zip_filename}"

        # Create a single zip file
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for root, dirs, files in os.walk(download_path):
                for file in files:
                    if file != zip_filename:
                        zipf.write(os.path.join(root, file), arcname=file)

        buttons = [
            [InlineKeyboardButton("🔗 GitHub Profile", url=f"https://github.com/{input_text}")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/rishu1286")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        with open(zip_path, "rb") as file:
            update.message.reply_document(
                file,
                caption=f"✅ *Here are the repositories for GitHub user:* `{input_text}`\n\n🔹 Powered by @rishu1286",
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )

    # Cleanup
    os.system(f"rm -rf {download_path}")

# Main function
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Use environment variable for token
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, fetch_repos))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
