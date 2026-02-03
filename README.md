# Sirion Guard Bot
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/netizen-0/protection&app=myappname)
Sirion is a Telegram moderation bot built with [Pyrogram](https://docs.pyrogram.org/).
It offers a compact set of tools to keep groups clean while remaining easy to configure via inline buttons.

## Features
- **BioMode** – delete messages from users whose profile bio contains a link.
- **LinkFilter** – remove messages containing URLs from non‑admins.
- **EditMode** – delete edited messages from regular users.
- **AutoDelete** – automatically purge messages after a configurable delay.
- **Approval Mode** – allow only approved users to talk when enabled.
- **Broadcast** – send announcements to all groups with `/broadcast <text>`.
- Inline control panel available through `/start`, `/help` or `/menu`.

## Commands
`/ban`, `/kick`, `/mute`, `/warn`, `/resetwarn`, `/approve`, `/unapprove`, `/approved`, `/biolink`, `/linkfilter`, `/editfilter`, `/setautodelete`, `/broadcast` (owner only) and `/ping`.

## Requirements
- Python 3.10+
- A running MongoDB instance
- Telegram API credentials

## Setup
1. Clone the repository and install dependencies
   ```bash
   git clone https://github.com/youruser/guard-bot.git
   cd guard-bot
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in the variables.
   Required variables are:
   - `API_ID`, `API_HASH`, `BOT_TOKEN`
   - `MONGO_URI`, `MONGO_DB`
   Optional variables:
   - `OWNER_ID` – your Telegram user ID for owner commands
   - `LOG_GROUP_ID` – ID of a private channel for logs
   - `SUPPORT_CHAT_URL`, `DEVELOPER_URL`, `PANEL_IMAGE_URL`
3. Run the bot locally for testing
   ```bash
   python3 run.py
   ```
   Keep it running using `screen`, `tmux` or a `systemd` service.

4. To deploy on a server provide the same environment variables and execute
   `sh start.sh`. The script runs `python run.py` with logging enabled.

## Render Deployment
Create a new **Background Worker** on [Render](https://render.com) and use `render.yaml` for automatic configuration.
Set the environment variables from your `.env` file in the Render dashboard. The worker command runs `sh start.sh`.
Optionally deploy `web.py` as a small web service for health checks.

When running on your own VPS simply execute `sh start.sh` in a screen or
systemd service. On Render the worker type automatically keeps the bot
running in the background.

### VPS Deployment
1. Make sure you have Python 3.10+ and Git installed on the server.
2. Clone the repository and install dependencies as in the setup section.
3. Copy `.env.example` to `.env` and fill out **all** required variables:
   - `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org)
   - `BOT_TOKEN` from BotFather and ensure `/setprivacy` is **disabled**
   - `MONGO_URI` and `MONGO_DB` for your MongoDB instance
   - `OWNER_ID` – your Telegram user ID so `/broadcast` works
   - Optionally `LOG_GROUP_ID`, `SUPPORT_CHAT_URL`, etc.
4. Start the bot inside a persistent shell so it keeps running:
   ```bash
   screen -S oxygen
   python3 run.py
   ```
   Detach with `Ctrl+A` then `D`. Reattach with `screen -r oxygen`.

## Manual Broadcast
Only the owner can use `/broadcast <text>` (or reply to a message) to send an announcement.
Messages are delivered to all groups and private users that have interacted with the bot.
The Broadcast button in the control panel shows this instruction as well.

### Tips
- Give the bot administrator rights in your groups so it can delete messages and manage users.
- Use `/start` or `/menu` in a group as an admin to open the settings panel.

## Notes
The bot works entirely in polling mode and logs important events such as new users and group joins/leaves to the log group if provided.
