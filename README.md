# SamaBOT
System Automation &amp; Management Assistance BOT.

### Here are short explanations of the `.env` file:

- **FLASK_SECRET_KEY**: A secret key for Flask to secure your app. You can generate a new key by running `python -c 'import os; print(os.urandom(24))'` in your terminal.
- **DISCORD_CLIENT_ID**: Your Discord bot's client ID, which you can find in the [Discord Developer Portal](https://discord.com/developers/applications).
- **DISCORD_CLIENT_SECRET**: The secret key associated with your Discord application, also available in the [Discord Developer Portal](https://discord.com/developers/applications).
- **DISCORD_REDIRECT_URI**: The URL where users will be redirected after authorizing the bot. This is typically `http://localhost:5000/callback` for local development.
- **DISCORD_TOKEN**: The bot token you received when creating your Discord bot in the [Developer Portal](https://discord.com/developers/applications).


To launch: 'docker-compose up' in the terminal and you're good to go.