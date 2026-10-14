# starter-repo/backend/tools.py
from typing import Optional, List
from backend.integrations import integrations_mgr

# ==========================================
# 1. ORIGINAL WORKSHOP TOOL
# ==========================================

def calculate_total(subtotal: float, tax_rate: float) -> float:
    """Calculate an order total after tax."""
    return subtotal + (subtotal * tax_rate)

# ==========================================
# 2. GMAIL TOOLS
# ==========================================

def get_unread_emails(max_results: int = 5) -> str:
    """Fetch recent unread emails from the connected Gmail inbox."""
    result = integrations_mgr.get_unread_emails(max_results=max_results)
    return str(result)

def search_emails(query: str, max_results: int = 5) -> str:
    """Search for emails in the connected Gmail inbox matching a query or keyword."""
    result = integrations_mgr.search_emails(query=query, max_results=max_results)
    return str(result)

def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient using the connected Gmail account."""
    result = integrations_mgr.send_email(to=to, subject=subject, body=body)
    return str(result)

def create_email_draft(to: str, subject: str, body: str) -> str:
    """Create an email draft without sending it, saved in the connected Gmail account."""
    result = integrations_mgr.create_email_draft(to=to, subject=subject, body=body)
    return str(result)

# ==========================================
# 3. GOOGLE CALENDAR TOOLS
# ==========================================

def list_calendar_events(time_min: Optional[str] = None, time_max: Optional[str] = None, max_results: int = 10) -> str:
    """List events from the connected Google Calendar within an optional time range."""
    result = integrations_mgr.list_calendar_events(time_min=time_min, time_max=time_max, max_results=max_results)
    return str(result)

def check_calendar_availability(start_time: str, end_time: str) -> str:
    """Check if the user is available or busy during a specific time range."""
    result = integrations_mgr.check_calendar_availability(start_time=start_time, end_time=end_time)
    return str(result)

def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: Optional[List[str]] = None
) -> str:
    """Schedule and create a new event on the connected Google Calendar."""
    result = integrations_mgr.create_calendar_event(
        summary=summary,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
        attendees=attendees
    )
    return str(result)

# ==========================================
# TOOL DEFINITIONS (OpenAI Function Schemas)
# ==========================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_total",
            "description": "Calculate an order total after tax.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subtotal": {
                        "type": "number",
                        "description": "The pre-tax amount"
                    },
                    "tax_rate": {
                        "type": "number",
                        "description": "The tax rate as a decimal (e.g., 0.08 for 8%)"
                    }
                },
                "required": ["subtotal", "tax_rate"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_unread_emails",
            "description": "Retrieve recent unread emails from the connected Gmail inbox. Returns sender, subject, date, and preview snippet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of unread emails to retrieve (default is 5)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Search emails in the connected Gmail account by keyword, sender email, topic, or subject line.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword or sender to filter emails by (e.g., 'flight', 'roadmap', 'sarah')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of matching emails to retrieve (default is 5)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email message to a specified recipient using the connected Gmail account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "The email address of the recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject line of the email"
                    },
                    "body": {
                        "type": "string",
                        "description": "The full text message body of the email"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_email_draft",
            "description": "Create and save an email draft in the connected Gmail account without sending it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "The recipient's email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject line of the email draft"
                    },
                    "body": {
                        "type": "string",
                        "description": "The body text content of the draft"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_calendar_events",
            "description": "List events and meetings from the connected Google Calendar within an optional date/time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "description": "Lower bound (inclusive) for event start times formatted in ISO 8601 (e.g. '2026-10-13T00:00:00')"
                    },
                    "time_max": {
                        "type": "string",
                        "description": "Upper bound (inclusive) for event start times formatted in ISO 8601 (e.g. '2026-10-13T23:59:59')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return (default is 10)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_calendar_availability",
            "description": "Check whether the user is free or busy during a specific time interval on Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "The beginning of the time interval to check formatted in ISO 8601 (e.g. '2026-10-14T14:00:00')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "The end of the time interval to check formatted in ISO 8601 (e.g. '2026-10-14T15:00:00')"
                    }
                },
                "required": ["start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Schedule and create a new event or meeting on the user's connected Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "The title or summary of the meeting/event"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start date and time of the event formatted in ISO 8601 (e.g. '2026-10-14T14:00:00')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End date and time of the event formatted in ISO 8601 (e.g. '2026-10-14T15:00:00')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional notes or details for the event"
                    },
                    "location": {
                        "type": "string",
                        "description": "Optional physical location or meeting link (e.g. 'Google Meet')"
                    },
                    "attendees": {
                        "type": "array",
                        "items": { "type": "string" },
                        "description": "Optional list of attendee email addresses"
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        }
    }
]

# Map tool names to the executable Python functions
TOOL_FUNCTIONS = {
    "calculate_total": calculate_total,
    "get_unread_emails": get_unread_emails,
    "search_emails": search_emails,
    "send_email": send_email,
    "create_email_draft": create_email_draft,
    "list_calendar_events": list_calendar_events,
    "check_calendar_availability": check_calendar_availability,
    "create_calendar_event": create_calendar_event
}

# Tool category sets
LOCAL_GMAIL_TOOLS = {"get_unread_emails", "search_emails", "send_email", "create_email_draft"}
LOCAL_CALENDAR_TOOLS = {"list_calendar_events", "check_calendar_availability", "create_calendar_event"}
LOCAL_GENERAL_TOOLS = {"calculate_total"}

