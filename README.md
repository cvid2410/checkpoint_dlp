# DLP Scanner Project

## Overview

The DLP (Data Loss Prevention) Scanner is a Python-Django based project designed to scan Slack messages and files for sensitive information such as Social Security Numbers and Credit Card numbers. It identifies potential leaks and deletes messages if required, integrating with RabbitMQ for processing, and saving results in a MySQL database.

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Environment Variables](#environment-variables)
- [Key Features](#key-features)
- [Endpoints](#endpoints)
- [Testing](#testing)

## Getting Started

### Prerequisites

Ensure you have the following installed:

- Python 3.10
- Docker & Docker Compose
- Slack App
- Ngrok

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/cvid2410/checkpoint_dlp
cd dlp-scanner
```

2. **Set up environment variables:**
   Create a .env file in the project root and define the necessary variables (refer to the [Environment Variables](#environment-variables) section).

3. **Build docker containers:**

```bash
docker-compose build
```

### Running the application

1. **Start the containers:**

```bash
docker-compose up -d
```

This will spin up MySQL, RabbitMQ, the Django server, and the DLP processor.

2. **Apply migrations:**

```bash
docker-compose exec webserver python manage.py migrate
```

3. **Create a superuser to access the Django admin:**

```bash
docker-compose exec webserver python manage.py createsuperuser
```

3. **Access the application:**

- Django app: http://localhost:8000
- RabbitMQ UI: http://localhost:15672

## Environment Variables

```
# Django Settings
DJANGO_SECRET_KEY='django-insecure--q10*%!s@2c!w0nikrgy3n^$d#irtjtly&=e#f#kv#h1fn^cd5'

# Database Configuration
DB_NAME="mydatabase"
DB_USER="localuser"
DB_PASSWORD="localpassword"
DB_HOST="db"
DB_PORT=3306

# Slack Configuration
SLACK_WEBHOOK_BASE_URL="your_slack_webhook_base_url"
SLACK_SIGNING_SECRET="your_slack_signing_secret"
SLACK_BOT_TOKEN="your_slack_bot_token"
SLACK_BOT_USER="your_slack_bot_user_token"

# RabbitMQ Configuration
RABBITMQ_USER="localuser"
RABBITMQ_PASSWORD="localpassword"
RABBITMQ_PORT=5672

# Web Server API
WEBSERVER_API_KEY="your_webserver_api_key"
WEBSERVER_BASE_URL="http://host.docker.internal:8000"

```

## Key Features

- **Slack Integration**: Connects to Slack's Real Time Messaging (RTM) API to read messages.
- **Pattern Matching**: Uses regex patterns to detect sensitive information.
- **DLP Processor**: Consumes messages from RabbitMQ, processes the data, and saves results.
- **Caught Messages**: Saves matched patterns in a database and attempts to delete the offending Slack message.
- **REST API**: Provides endpoints to manage patterns and caught messages.
- **Admin Interface**: Manage data and view logs via Django Admin.

## Endpoints

### Pattern Management

- **GET /api/patterns/** - Retrieve all patterns.

### Caught Messages

- **POST /api/caught_messages/** - Save a caught message.

### Slack Events

- **POST /slack/events/** - Handle Slack events (URL verification, messages, channel creations).

## Testing

- **Run tests using the Django test runner:**

```bash
docker-compose exec webserver python manage.py test
```
