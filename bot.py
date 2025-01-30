import discord
from discord.ext import commands
import mysql.connector
import paramiko
import spacy
import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI')

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# NLP setup
nlp = spacy.load("en_core_web_md")

# Database connection
db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

# In-memory storage for active SSH sessions
active_sessions = {}

# Example command suggestions
intents_responses = {
    "update system": "sudo apt-get update",
    "upgrade system": "sudo apt-get upgrade",
    "install package": "sudo apt-get install <package_name>",
    "remove package": "sudo apt-get remove <package_name>",
    "check disk space": "df -h",
    "check memory usage": "free -h",
    "list files": "ls -al <directory>",
    "restart service": "sudo systemctl restart <service_name>",
    "start service": "sudo systemctl start <service_name>",
    "stop service": "sudo systemctl stop <service_name>",
    "check service status": "sudo systemctl status <service_name>",
    "view running processes": "ps aux",
    "kill process": "kill <process_id>",
    "find files": "find /path/to/search -name <filename>",
    "check network configuration": "ifconfig",
    "check open ports": "netstat -tuln",
    "monitor network traffic": "iftop",
    "view system logs": "tail -f /var/log/syslog",
    "view dmesg output": "dmesg",
    "view CPU usage": "top",
    "create new user": "sudo adduser <username>",
    "delete user": "sudo deluser <username>",
    "change user password": "passwd <username>",
    "add user to group": "sudo usermod -aG <group> <username>",
    "change file permissions": "chmod <permissions> <file>",
    "change file ownership": "chown <owner>:<group> <file>",
    "mount filesystem": "sudo mount <device> <mount_point>",
    "unmount filesystem": "sudo umount <mount_point>",
    "create directory": "mkdir <directory>",
    "remove directory": "rmdir <directory>",
    "copy files": "cp <source> <destination>",
    "move files": "mv <source> <destination>",
    "delete files": "rm <file>",
    "check system uptime": "uptime",
    "show system information": "uname -a",
    "check disk usage by directory": "du -sh <directory>",
    "compress files": "tar -czvf <archive_name>.tar.gz <directory_or_file>",
    "extract compressed files": "tar -xzvf <archive_name>.tar.gz",
    "check IP address": "hostname -I",
    "set hostname": "sudo hostnamectl set-hostname <new_hostname>",
    "ping host": "ping <hostname_or_ip>",
    "traceroute to host": "traceroute <hostname_or_ip>",
    "configure network interface": "sudo nmtui",
    "manage cron jobs": "crontab -e",
    "view all cron jobs": "crontab -l",
    "check home directory": "echo $HOME",
    "display current directory": "pwd",
    "check environment variables": "printenv",
    "search text within files": "grep '<search_term>' <file>",
    "edit files": "nano <file>"
}

def recognize_intent(text):
    doc = nlp(text.lower())
    max_similarity = 0
    best_intent = None
    for intent in intents_responses.keys():
        intent_doc = nlp(intent)
        similarity = doc.similarity(intent_doc)
        if similarity > max_similarity:
            max_similarity = similarity
            best_intent = intent
    return best_intent if max_similarity > 0.6 else None

# Middleware to check for valid Discord session
async def ensure_authorized(ctx):
    user_id = str(ctx.author.id)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE discord_id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        await ctx.send("You are not logged in. Please log in through the web interface.")
        return False
    return True

# Adding a server
@bot.command(name='add')
@commands.check(ensure_authorized)
async def add_server(ctx, server_name=None, ip=None, ssh_user=None, ssh_password=None):
    if not all([server_name, ip, ssh_user, ssh_password]):
        await ctx.send("Usage: !add <server_name> <IP> <ssh_user> <ssh_password>")
        return
    
    user_id = str(ctx.author.id)
    cursor = db.cursor()
    cursor.execute("INSERT INTO servers (user_id, server_name, ip, ssh_user, ssh_password) VALUES (%s, %s, %s, %s, %s)",
                   (user_id, server_name, ip, ssh_user, ssh_password))
    db.commit()
    await ctx.send(f"Server {server_name} added.")

# Deleting a server
@bot.command(name='delete')
@commands.check(ensure_authorized)
async def delete_server(ctx, server_name=None):
    if not server_name:
        await ctx.send("Usage: !delete <server_name>")
        return
    
    user_id = str(ctx.author.id)
    cursor = db.cursor()
    cursor.execute("DELETE FROM servers WHERE user_id=%s AND server_name=%s", (user_id, server_name))
    db.commit()
    await ctx.send(f"Server {server_name} deleted.")

# Listing user servers
@bot.command(name='list')
@commands.check(ensure_authorized)
async def list_servers(ctx):
    user_id = str(ctx.author.id)
    cursor = db.cursor()
    cursor.execute("SELECT server_name, ip FROM servers WHERE user_id=%s", (user_id,))
    servers = cursor.fetchall()
    if servers:
        await ctx.send("\n".join([f"{server[0]}: {server[1]}" for server in servers]))
    else:
        await ctx.send("No servers found.")

# Execute bash command
@bot.command(name='bash')
@commands.check(ensure_authorized)
async def bash_command(ctx, server_name=None, *, command=None):
    user_id = str(ctx.author.id)

    if not server_name:
        await ctx.send("Usage: !bash <server_name> [command]")
        return

    cursor = db.cursor()
    cursor.execute("SELECT ip, ssh_user, ssh_password FROM servers WHERE user_id=%s AND server_name=%s", (user_id, server_name))
    server = cursor.fetchone()
    if not server:
        await ctx.send("Server not found.")
        return

    ip, ssh_user, ssh_password = server

    if command:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=ssh_user, password=ssh_password)
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
        ssh.close()
        await ctx.send(f"```\n{result}\n```")
    else:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=ssh_user, password=ssh_password)
        active_sessions[user_id] = ssh
        await ctx.send(f"SSH session opened for server {server_name}. You can now send commands directly.")

@bot.command(name='endbash')
@commands.check(ensure_authorized)
async def end_bash(ctx):
    user_id = str(ctx.author.id)
    if user_id in active_sessions:
        active_sessions[user_id].close()
        del active_sessions[user_id]
        await ctx.send("SSH session closed.")
    else:
        await ctx.send("No active SSH session.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = str(message.author.id)

    if user_id in active_sessions:
        ssh = active_sessions[user_id]
        stdin, stdout, stderr = ssh.exec_command(message.content)
        result = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
        await message.channel.send(f"```\n{result}\n```")
    else:
        await bot.process_commands(message)

@bot.command(name='ask')
@commands.check(ensure_authorized)
async def ask(ctx, *, query=None):
    if not query:
        await ctx.send("Usage: !ask <query>")
        return

    intent = recognize_intent(query)
    if intent:
        response = intents_responses[intent]
        await ctx.send(f"Suggested command: `{response}`")
    else:
        await ctx.send("Sorry, I didn't understand your query. Please try asking something else.")

# Commands command to list all available commands
@bot.command(name='commands')
@commands.check(ensure_authorized)
async def commands_list(ctx):
    command_list = [
        "!add <server_name> <IP> <ssh_user> <ssh_password> - Add a new server",
        "!delete <server_name> - Delete an existing server",
        "!list - List all added servers",
        "!bash <server_name> [command] - Open an SSH session or run a command",
        "!endbash - Close the active SSH session",
        "!ask <query> - Get a suggested command based on your query",
        "!commands - List all available commands"
    ]
    await ctx.send("\n".join(command_list))

bot.run(DISCORD_TOKEN)
