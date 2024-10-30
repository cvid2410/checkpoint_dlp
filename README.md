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

1. **Setup Ngrok**
   To download and install Ngrok, go to the [Ngrok website](https://ngrok.com/download) and follow the instructions for your OS.

To start Ngrok, run the following command:

```bash
ngrok http 8000
```

Copy the **Forwarding** url and set it as your `SLACK_WEBHOOK_BASE_URL/` + `/slack/events`, you will also need to add this URL under `ALLOWED_HOSTS` (do not include `http://`) within your Django Settings.

2. **Clone the repository:**

```bash
git clone https://github.com/cvid2410/checkpoint_dlp
cd dlp-scanner
```

3. **Set up environment variables:**
   Create a .env file in the project root and define the necessary variables (refer to the [Environment Variables](#environment-variables) section).

4. **Build docker containers:**

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

4. **Within Django Admin create some Patterns**

Credit Card Pattern

```regex
(?:\d[ -]*?){13,16}
```

SSN Pattern

```regex
\b\d{3}-?\d{2}-?\d{4}\b
```

5. **Access the application:**

- Django app: http://localhost:8000
- RabbitMQ UI: http://localhost:15672

6. **Create a public slack channel**

On your Slack App create a public slack channel. Your Slack App will be automatically joined to the newly created channel.

7. **Attach a file with a Credit Card Number or SSN**
   Either attach a PDF file with a credit card number or simply type on the public channel (You will notice the message gets immediately removed):

```
My credit card number is 1111-2222-3333-4444
My SSN in 123-45-6789
```

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

You will need to set up 5 environmental variables in here.

1. **SLACK_WEBHOOK_BASE_URL** refer to [Setup Ngrok](#installation) step
2. **SLACK_SIGNING_SECRET** go to [Slack API](https://api.slack.com/) and [setup an app](https://api.slack.com/quickstart) you will be given this key once you are done
3. **SLACK_BOT_TOKEN** go to OAuth & Permissions within your app and retrieve your **Bot User OAuth Token**
4. **SLACK_BOT_USER** go to OAuth & Permissions within your app and retrieve your **User OAuth Token**
5. **WEBSERVER_API_KEY** create webserver API Key via Django Shell

```bash
docker-compose exec webserver python manage.py shell
```

```python
from rest_framework_api_key.models import APIKey

_, key = APIKey.objects.create_key(name="Manager Key")
print(f"API key: {key}")
```

Save the key as your **WEBSERVER_API_KEY**

## Slack Webhook Events & OAuth Scopes

### 1. Setup Event Subscriptions

Under **Request URL** set your **SLACK_WEBHOOK_BASE_URL** as well as under **Subscribe to bot events** choose `Subscribe to bot events` and under **Subscribe to events on behalf of users** choose `message.channels`.

Click Save.

### 2. Setup Auth Scopes

Under **OAuth & Permissions** look for **Bot Token Scopes** and enable the following `channels:join`,`channels:read`, and `files:read`. Also look for **User Token Scopes** and enable the following `chat:write`.

Click Save.

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

## Demo

https://drive.google.com/file/d/1gN_LudYfZptNJHpYhWVqyLObbZuzsuBU/view?usp=sharing
