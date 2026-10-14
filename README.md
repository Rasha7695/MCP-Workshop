# MCP Workshop

Welcome to the **Women In The Loop** MCP workshop! 
This repository contains a simple Python backend and a chat frontend. It provides a complete environment where you can build an AI assistant that uses tools and connect to real services.

## Prerequisites
- **Python 3.9+**
- **Node.js 18+ & npm** (required if using live Model Context Protocol / MCP servers)

## Setup Instructions

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment variables**:
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Add your OpenAI API key and (optional) workshop Google OAuth credentials:
   ```env
   OPENAI_API_KEY=your_api_key_here
   GOOGLE_CLIENT_ID=your_google_client_id_here
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here
   ```

## Running the App

Start the backend server:
```bash
uvicorn backend.main:app --reload
```
Then, open your browser at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Connecting Gmail & Google Calendar

The chatbot works immediately out of the box in **Sandbox Mode**:
- **⚡ Sandbox Mode (Default):** Pre-seeded mock emails and calendar events for Alex Morgan. Try asking: *"What unread emails do I have?"* or *"What's on my calendar today?"*.
- **🌐 Google OAuth 2.0 (Live Mode):** Click **"Connect Services"** in the top navigation bar to sign in with your real Google account via OAuth 2.0 and MCP.
- **Inspect Mock Data:** Click **"Sandbox Data"** in the top header to inspect all mock emails, folders, and calendar events.

### Available Tools:
- `get_unread_emails`: Fetch recent unread emails.
- `search_emails`: Search messages by query, sender, or subject.
- `send_email`: Send an email to any recipient.
- `create_email_draft`: Save a new draft.
- `list_calendar_events`: List upcoming events in a date/time window.
- `check_calendar_availability`: Check whether a time slot is free or busy.
- `create_calendar_event`: Schedule and create a new meeting or event.
- `calculate_total`: Original workshop math tool.

## How to Add Your Own Tools

1. Open `backend/tools.py`.
2. Write a standard Python function.
3. Add the JSON schema for your tool to the `TOOL_DEFINITIONS` list.
4. Add your Python function to the `TOOL_FUNCTIONS` dictionary to map the tool name to your code.

The core tool execution loop runs in `backend/agent.py`.
