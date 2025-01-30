CREATE DATABASE IF NOT EXISTS discord_bot;
USE discord_bot;

CREATE TABLE IF NOT EXISTS servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    server_name VARCHAR(255) NOT NULL,
    ip VARCHAR(255) NOT NULL,
    ssh_user VARCHAR(255) NOT NULL,
    ssh_password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    discord_id VARCHAR(255) PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL
);
