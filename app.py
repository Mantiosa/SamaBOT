from flask import Flask, redirect, request, session, url_for
import requests
import os
from dotenv import load_dotenv
import mysql.connector

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Discord OAuth2 credentials
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

# Database connection
db = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

# Discord OAuth2 URLs
DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_URL = "https://discord.com/api/v9/users/@me"

def get_discord_oauth_url():
    return f"{DISCORD_AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"

@app.route("/")
def home():
    return 'Welcome to the Discord OAuth2 example. <a href="/login">Login</a>'

@app.route("/login")
def login():
    return redirect(get_discord_oauth_url())

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
    response_data = response.json()
    
    # Log the entire response for debugging
    print("Token response data:", response_data)

    if 'access_token' not in response_data:
        return f"Error: {response_data.get('error', 'Unknown error')} - {response_data.get('error_description', 'No description provided')}"

    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]

    # Fetch the user's Discord ID
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    user_response = requests.get(DISCORD_API_URL, headers=headers)
    user_data = user_response.json()

    # Store the user's Discord ID and tokens in the database
    cursor = db.cursor()
    cursor.execute("REPLACE INTO users (discord_id, access_token, refresh_token) VALUES (%s, %s, %s)",
                   (user_data["id"], access_token, refresh_token))
    db.commit()

    return f"Logged in as {user_data['username']}#{user_data['discriminator']}"

@app.route("/refresh")
def refresh_token():
    discord_id = session.get("discord_id")
    if not discord_id:
        return redirect(url_for("login"))
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT refresh_token FROM users WHERE discord_id = %s", (discord_id,))
    user = cursor.fetchone()
    
    if not user:
        return redirect(url_for("login"))

    refresh_token = user["refresh_token"]

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
    response_data = response.json()
    
    # Log the entire response for debugging
    print("Refresh token response data:", response_data)

    if 'access_token' not in response_data:
        return f"Error: {response_data.get('error', 'Unknown error')} - {response_data.get('error_description', 'No description provided')}"

    access_token = response_data["access_token"]
    new_refresh_token = response_data["refresh_token"]

    # Update the database with new tokens
    cursor.execute("UPDATE users SET access_token = %s, refresh_token = %s WHERE discord_id = %s",
                   (access_token, new_refresh_token, discord_id))
    db.commit()

    return "Token refreshed!"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
