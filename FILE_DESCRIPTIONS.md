# File Descriptions

This repository has been reorganized under `oxeign/swagger`.
Below is an overview of each file and a short note on what it contains.

## bots
- **bots_Dockerfile** – Docker instructions for containerizing the bot.
- **bots_handlers/** – Telegram bot handlers.
  - **bots_handlers_init.py** – package initializer for handlers.
  - **bots_admin.py** – admin command handlers.
  - **bots_callbacks.py** – callback query handlers.
  - **bots_commands.py** – bot command handlers.
  - **bots_filters.py** – custom message filters.
  - **bots_general.py** – general utility handlers.
  - **bots_logging.py** – logging setup for handlers.
  - **bots_ping.py** – ping and health checks.
  - **bots_settings.py** – settings handlers.

## yard
- **yard_README.md** – original project README.
- **yard_utils/** – helper utilities used by the bot.
  - **yard_utils_init.py** – package initializer for utilities.
  - **yard_db.py** – MongoDB access functions.
  - **yard_errors.py** – error handling helpers.
  - **yard_messages.py** – message templates and texts.
  - **yard_perms.py** – permission helpers.
  - **yard_webhook.py** – webhook utilities.

## harami
- **harami_config.py** – loads environment variables and configuration.
- **harami_env.example** – example environment file.
- **harami_render.yaml** – Render.com service description.
- **harami_requirements.txt** – Python dependencies list.
- **harami_runtime.txt** – runtime version pin for hosting.
- **harami_start.sh** – startup script used on Render or Heroku.

## swagger
- **swagger_init.py** – package initializer.
- **swagger_web.py** – HTTP server for webhook mode.

## oxy
- **oxy_Procfile** – process declaration for Heroku style platforms.
- **oxy_main.py** – main entry point when running locally.
- **oxy_oxygenbot.py** – asynchronous launcher for the bot.

