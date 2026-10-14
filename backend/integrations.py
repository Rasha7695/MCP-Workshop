import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

STATE_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "integrations_state.json")

def _get_default_seed_data() -> Dict[str, Any]:
    now = datetime.now()
    
    # Format realistic dates relative to current local date
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after_str = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    
    return {
        "gmail": {
            "connected": True,
            "mode": "sandbox",  # "none", "sandbox", "oauth"
            "email": "alex.morgan@gmail.com",
            "account_name": "Alex Morgan"
        },
        "calendar": {
            "connected": True,
            "mode": "sandbox",  # "none", "sandbox", "oauth"
            "email": "alex.morgan@gmail.com",
            "account_name": "Alex Morgan"
        },
        "oauth_config": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "access_token": "",
            "refresh_token": "",
            "expires_at": 0,
            "user_email": "",
            "user_name": ""
        },
        "sandbox_emails": [
            {
                "id": "msg_001",
                "folder": "inbox",
                "unread": True,
                "sender": "sarah.chen@techcorp.io",
                "to": "alex.morgan@gmail.com",
                "subject": "Q4 Roadmap Review & AI Initiatives",
                "snippet": "Hi team, please find attached the proposal for Q4 roadmap...",
                "body": (
                    "Hi Alex,\n\n"
                    "Please review the proposal for our Q4 product roadmap and AI tool calling integrations "
                    "before our review session tomorrow at 2:00 PM. Let me know if you have questions!\n\n"
                    "Best,\nSarah Chen\nVP of Product, TechCorp"
                ),
                "date": (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            },
            {
                "id": "msg_002",
                "folder": "inbox",
                "unread": True,
                "sender": "reservations@skyflyer.com",
                "to": "alex.morgan@gmail.com",
                "subject": "Flight Confirmation: SFO to JFK (Flight SF-802)",
                "snippet": "Your booking is confirmed! Flight SF802 departs on Oct 24...",
                "body": (
                    "Booking Reference: #SF-98241\n"
                    "Passenger: Alex Morgan\n"
                    "Flight: SF802 - Non-stop\n"
                    "Departing: San Francisco (SFO) - Oct 24 at 08:30 AM\n"
                    "Arriving: New York (JFK) - Oct 24 at 04:55 PM\n"
                    "Seat: 12A (Window, Economy Plus)\n\n"
                    "Thank you for flying SkyFlyer!"
                ),
                "date": (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M")
            },
            {
                "id": "msg_003",
                "folder": "inbox",
                "unread": True,
                "sender": "newsletter@womenintheloop.org",
                "to": "alex.morgan@gmail.com",
                "subject": "Women In The Loop: Workshop Kickoff & Resources",
                "snippet": "Welcome to today's Tool Calling Workshop! Here are the guides...",
                "body": (
                    "Hello Alex!\n\n"
                    "Welcome to the Women In The Loop Tool Calling Workshop! Today we are mastering "
                    "LLM tool use, structured parameters, and building real-world integrations like Gmail & Google Calendar.\n\n"
                    "Check the starter repository for tools and examples. Happy coding!\n\n"
                    "Warmly,\nThe Women In The Loop Team"
                ),
                "date": (now - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
            },
            {
                "id": "msg_004",
                "folder": "inbox",
                "unread": False,
                "sender": "no-reply@github.com",
                "to": "alex.morgan@gmail.com",
                "subject": "[GitHub] Pull Request #42 merged: Add function calling engine",
                "snippet": "Your pull request #42 was successfully merged into main...",
                "body": "PR #42 'Add function calling engine' was approved and merged by @marcus-lee.",
                "date": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
            },
            {
                "id": "msg_005",
                "folder": "sent",
                "unread": False,
                "sender": "alex.morgan@gmail.com",
                "to": "david.kim@designlab.co",
                "subject": "Design feedback on tool dashboard",
                "snippet": "Hi David, loved the dark mode palette and glassmorphic badges...",
                "body": "Hi David,\n\nLoved the dark mode palette and glassmorphic badges. Let's touch base soon.\n\nCheers,\nAlex",
                "date": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
            }
        ],
        "sandbox_events": [
            {
                "id": "evt_001",
                "summary": "Engineering & Product Standup",
                "description": "Daily team sync and sprint blocker review.",
                "location": "Google Meet: https://meet.google.com/abc-defg-hij",
                "start": f"{today_str}T09:30:00",
                "end": f"{today_str}T10:00:00",
                "attendees": ["alex.morgan@gmail.com", "sarah.chen@techcorp.io", "marcus.lee@techcorp.io"]
            },
            {
                "id": "evt_002",
                "summary": "Lunch with Maya",
                "description": "Discussing community mentorship programs.",
                "location": "Bistro Verde, Downtown",
                "start": f"{today_str}T12:30:00",
                "end": f"{today_str}T13:30:00",
                "attendees": ["alex.morgan@gmail.com", "maya.patel@community.org"]
            },
            {
                "id": "evt_003",
                "summary": "Q4 Roadmap Review",
                "description": "Review proposal slides and AI tool calling timeline with Sarah.",
                "location": "Conference Room B / Hybrid",
                "start": f"{tomorrow_str}T14:00:00",
                "end": f"{tomorrow_str}T15:00:00",
                "attendees": ["alex.morgan@gmail.com", "sarah.chen@techcorp.io"]
            },
            {
                "id": "evt_004",
                "summary": "Women In The Loop Project Demo",
                "description": "Demonstrating the integrated Gmail and Calendar tool calling assistant.",
                "location": "Virtual Auditorium",
                "start": f"{day_after_str}T15:00:00",
                "end": f"{day_after_str}T16:00:00",
                "attendees": ["alex.morgan@gmail.com", "workshop@womenintheloop.org"]
            }
        ]
    }

class IntegrationManager:
    def __init__(self):
        self.state = self._load_state()
        self._clear_mcp_disk_tokens()
        self._save_state()

    def _clear_mcp_disk_tokens(self):
        """Removes local MCP token caches so MCP stdio servers also require re-authorization."""
        cal_token_file = os.path.expanduser("~/.config/google-calendar-mcp/tokens.json")
        gmail_token_file = os.path.expanduser("~/.gmail-mcp/credentials.json")
        for fpath in [cal_token_file, gmail_token_file]:
            try:
                if os.path.exists(fpath):
                    os.remove(fpath)
            except Exception as e:
                print(f"[Integrations] Warning: Could not remove token file {fpath}: {e}")

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(STATE_FILE_PATH):
            try:
                with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Update client_id / client_secret from environment if set and missing in state
                    oauth_cfg = data.get("oauth_config", {})
                    if not oauth_cfg.get("client_id") and os.getenv("GOOGLE_CLIENT_ID"):
                        oauth_cfg["client_id"] = os.getenv("GOOGLE_CLIENT_ID")
                    if not oauth_cfg.get("client_secret") and os.getenv("GOOGLE_CLIENT_SECRET"):
                        oauth_cfg["client_secret"] = os.getenv("GOOGLE_CLIENT_SECRET")

                    # Always forget OAuth account tokens/session on restart (require re-authorization)
                    oauth_cfg["access_token"] = ""
                    oauth_cfg["refresh_token"] = ""
                    oauth_cfg["expires_at"] = 0
                    oauth_cfg["user_email"] = ""
                    oauth_cfg["user_name"] = ""
                    data["oauth_config"] = oauth_cfg

                    # If saved services were in OAuth mode or on restart, default to Sandbox
                    if data.get("gmail", {}).get("mode") in ["oauth", "none"]:
                        data["gmail"] = {
                            "connected": True,
                            "mode": "sandbox",
                            "email": "alex.morgan@gmail.com",
                            "account_name": "Alex Morgan"
                        }
                    if data.get("calendar", {}).get("mode") in ["oauth", "none"]:
                        data["calendar"] = {
                            "connected": True,
                            "mode": "sandbox",
                            "email": "alex.morgan@gmail.com",
                            "account_name": "Alex Morgan"
                        }
                    return data
            except Exception as e:
                print(f"Error loading state from {STATE_FILE_PATH}: {e}")
        return _get_default_seed_data()

    def _save_state(self):
        try:
            os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
            # Create a sanitized copy of state for disk persistence that never stores live account session/tokens
            disk_state = json.loads(json.dumps(self.state))
            oauth_cfg = disk_state.get("oauth_config", {})
            oauth_cfg["access_token"] = ""
            oauth_cfg["refresh_token"] = ""
            oauth_cfg["expires_at"] = 0
            oauth_cfg["user_email"] = ""
            oauth_cfg["user_name"] = ""
            if os.getenv("GOOGLE_CLIENT_ID"):
                oauth_cfg["client_id"] = ""
            if os.getenv("GOOGLE_CLIENT_SECRET"):
                oauth_cfg["client_secret"] = ""
            if disk_state.get("gmail", {}).get("mode") == "oauth":
                disk_state["gmail"] = {
                    "connected": True,
                    "mode": "sandbox",
                    "email": "alex.morgan@gmail.com",
                    "account_name": "Alex Morgan"
                }
            if disk_state.get("calendar", {}).get("mode") == "oauth":
                disk_state["calendar"] = {
                    "connected": True,
                    "mode": "sandbox",
                    "email": "alex.morgan@gmail.com",
                    "account_name": "Alex Morgan"
                }
            with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(disk_state, f, indent=2)
        except Exception as e:
            print(f"Error saving state to {STATE_FILE_PATH}: {e}")

    def reload_state(self):
        # Preserve active in-memory OAuth session during runtime
        oauth_session = self.state.get("oauth_config", {})
        gmail_session = self.state.get("gmail", {})
        calendar_session = self.state.get("calendar", {})
        
        loaded = self._load_state()
        if oauth_session.get("access_token") and oauth_session.get("user_email"):
            loaded["oauth_config"]["access_token"] = oauth_session.get("access_token", "")
            loaded["oauth_config"]["refresh_token"] = oauth_session.get("refresh_token", "")
            loaded["oauth_config"]["expires_at"] = oauth_session.get("expires_at", 0)
            loaded["oauth_config"]["user_email"] = oauth_session.get("user_email", "")
            loaded["oauth_config"]["user_name"] = oauth_session.get("user_name", "")
            if gmail_session.get("mode") == "oauth":
                loaded["gmail"] = gmail_session
            if calendar_session.get("mode") == "oauth":
                loaded["calendar"] = calendar_session
        self.state = loaded

    # -------------------------------------------------------------
    # Status & Management
    # -------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        self.reload_state()
        oauth_cfg = self.state.get("oauth_config", {})
        has_oauth_creds = bool(oauth_cfg.get("client_id") and oauth_cfg.get("client_secret"))
        has_oauth_tokens = bool(oauth_cfg.get("access_token") and oauth_cfg.get("user_email"))

        # When live isn't available, automatically ensure Sandbox is active
        if not has_oauth_tokens:
            if self.state.get("gmail", {}).get("mode") != "sandbox":
                self.state["gmail"] = {
                    "connected": True,
                    "mode": "sandbox",
                    "email": "alex.morgan@gmail.com",
                    "account_name": "Alex Morgan"
                }
            if self.state.get("calendar", {}).get("mode") != "sandbox":
                self.state["calendar"] = {
                    "connected": True,
                    "mode": "sandbox",
                    "email": "alex.morgan@gmail.com",
                    "account_name": "Alex Morgan"
                }
        
        return {
            "gmail": self.state.get("gmail", {
                "connected": True,
                "mode": "sandbox",
                "email": "alex.morgan@gmail.com",
                "account_name": "Alex Morgan"
            }),
            "calendar": self.state.get("calendar", {
                "connected": True,
                "mode": "sandbox",
                "email": "alex.morgan@gmail.com",
                "account_name": "Alex Morgan"
            }),
            "oauth": {
                "configured": has_oauth_creds,
                "authenticated": has_oauth_tokens,
                "client_id": oauth_cfg.get("client_id", ""),
                "has_secret": bool(oauth_cfg.get("client_secret")),
                "user_email": oauth_cfg.get("user_email", ""),
                "user_name": oauth_cfg.get("user_name", "")
            }
        }

    def connect_sandbox(self, service: str, email: str = "alex.morgan@gmail.com", account_name: str = "Alex Morgan"):
        """Connect gmail, calendar, or both in Sandbox mode."""
        if service in ["gmail", "both"]:
            self.state["gmail"] = {
                "connected": True,
                "mode": "sandbox",
                "email": email,
                "account_name": account_name
            }
        if service in ["calendar", "both"]:
            self.state["calendar"] = {
                "connected": True,
                "mode": "sandbox",
                "email": email,
                "account_name": account_name
            }
        self._save_state()
        return self.get_status()

    def switch_mode(self, mode: str) -> Dict[str, Any]:
        """
        Quickly toggle both Gmail and Calendar between 'sandbox' and 'oauth'.
        """
        if mode == "sandbox":
            email = self.state.get("sandbox_account_email") or "alex.morgan@gmail.com"
            account_name = self.state.get("sandbox_account_name") or "Alex Morgan"
            self.state["gmail"] = {
                "connected": True,
                "mode": "sandbox",
                "email": email,
                "account_name": account_name
            }
            self.state["calendar"] = {
                "connected": True,
                "mode": "sandbox",
                "email": email,
                "account_name": account_name
            }
        elif mode == "oauth":
            oauth_cfg = self.state.get("oauth_config", {})
            user_email = oauth_cfg.get("user_email")
            access_token = oauth_cfg.get("access_token")
            # If live is not available, automatically fall back to sandbox
            if not access_token or not user_email:
                return self.switch_mode("sandbox")
            user_name = oauth_cfg.get("user_name") or "User"
            self.state["gmail"] = {
                "connected": True,
                "mode": "oauth",
                "email": user_email,
                "account_name": user_name
            }
            self.state["calendar"] = {
                "connected": True,
                "mode": "oauth",
                "email": user_email,
                "account_name": user_name
            }
        self._save_state()
        return self.get_status()

    def disconnect_service(self, service: str):
        """Disconnect gmail, calendar, or both. Disconnecting OAuth falls back to sandbox."""
        if service in ["gmail"]:
            self.state["gmail"] = {
                "connected": False,
                "mode": "none",
                "email": "",
                "account_name": ""
            }
        if service in ["calendar"]:
            self.state["calendar"] = {
                "connected": False,
                "mode": "none",
                "email": "",
                "account_name": ""
            }
        if service in ["oauth", "both"]:
            # Fall back to sandbox when live is disconnected / unavailable
            self.state["gmail"] = {
                "connected": True,
                "mode": "sandbox",
                "email": "alex.morgan@gmail.com",
                "account_name": "Alex Morgan"
            }
            self.state["calendar"] = {
                "connected": True,
                "mode": "sandbox",
                "email": "alex.morgan@gmail.com",
                "account_name": "Alex Morgan"
            }
            self.state["oauth_config"]["access_token"] = ""
            self.state["oauth_config"]["refresh_token"] = ""
            self.state["oauth_config"]["expires_at"] = 0
            self.state["oauth_config"]["user_email"] = ""
            self.state["oauth_config"]["user_name"] = ""
            self._clear_mcp_disk_tokens()

        self._save_state()
        return self.get_status()

    def get_sandbox_data(self) -> Dict[str, Any]:
        return {
            "emails": self.state.get("sandbox_emails", []),
            "calendar_events": self.state.get("sandbox_events", [])
        }

    def reset_sandbox_data(self):
        seed = _get_default_seed_data()
        self.state["sandbox_emails"] = seed["sandbox_emails"]
        self.state["sandbox_events"] = seed["sandbox_events"]
        self._save_state()
        return self.get_sandbox_data()

    # -------------------------------------------------------------
    # OAuth Configuration & Flow
    # -------------------------------------------------------------
    def save_oauth_credentials(self, client_id: str, client_secret: str):
        self.state["oauth_config"]["client_id"] = client_id.strip()
        self.state["oauth_config"]["client_secret"] = client_secret.strip()
        self._save_state()
        return {"status": "saved", "configured": bool(client_id and client_secret)}

    def get_google_auth_url(self, redirect_uri: str) -> str:
        client_id = self.state["oauth_config"].get("client_id")
        if not client_id:
            raise ValueError("Google Client ID is not configured. Please enter your credentials first.")
        
        scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.settings.basic",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/calendar.readonly"
        ]
        scope_str = "%20".join(scopes)
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope_str}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        return auth_url

    async def exchange_google_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        client_id = self.state["oauth_config"].get("client_id")
        client_secret = self.state["oauth_config"].get("client_secret")
        if not client_id or not client_secret:
            raise ValueError("Missing Google Client ID or Client Secret.")

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(token_url, data=data)
            if resp.status_code != 200:
                raise ValueError(f"Failed to exchange OAuth code: {resp.text}")
            token_data = resp.json()

            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token", self.state["oauth_config"].get("refresh_token"))
            expires_in = token_data.get("expires_in", 3600)

            # Fetch user info
            user_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_email = "connected-user@gmail.com"
            user_name = "Google User"
            if user_resp.status_code == 200:
                user_info = user_resp.json()
                user_email = user_info.get("email", user_email)
                user_name = user_info.get("name", user_name)

            self.state["oauth_config"]["access_token"] = access_token
            if refresh_token:
                self.state["oauth_config"]["refresh_token"] = refresh_token
            self.state["oauth_config"]["expires_at"] = time.time() + expires_in
            self.state["oauth_config"]["user_email"] = user_email
            self.state["oauth_config"]["user_name"] = user_name

            # Mark both Gmail and Calendar as connected in OAuth mode
            self.state["gmail"] = {
                "connected": True,
                "mode": "oauth",
                "email": user_email,
                "account_name": user_name
            }
            self.state["calendar"] = {
                "connected": True,
                "mode": "oauth",
                "email": user_email,
                "account_name": user_name
            }

            self._save_state()
            return {"email": user_email, "name": user_name}

    def _get_valid_access_token(self) -> str:
        """Get active access token, refreshing synchronously if necessary."""
        token = self.state["oauth_config"].get("access_token")
        expires_at = self.state["oauth_config"].get("expires_at", 0)
        refresh_token = self.state["oauth_config"].get("refresh_token")
        client_id = self.state["oauth_config"].get("client_id")
        client_secret = self.state["oauth_config"].get("client_secret")

        # If expired or expiring within 60s, refresh
        if (time.time() > expires_at - 60) and refresh_token and client_id and client_secret:
            try:
                with httpx.Client() as client:
                    resp = client.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "refresh_token": refresh_token,
                            "grant_type": "refresh_token"
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        token = data.get("access_token")
                        self.state["oauth_config"]["access_token"] = token
                        self.state["oauth_config"]["expires_at"] = time.time() + data.get("expires_in", 3600)
                        self._save_state()
            except Exception as e:
                print(f"Error refreshing access token: {e}")
        return token

    # -------------------------------------------------------------
    # Gmail Tools Implementation (Sandbox / Local)
    # -------------------------------------------------------------
    def is_gmail_connected(self) -> bool:
        return self.state.get("gmail", {}).get("connected", False)

    def get_unread_emails(self, max_results: int = 5) -> Dict[str, Any]:
        if not self.is_gmail_connected():
            return {
                "error": "Gmail is NOT connected. Please connect your Gmail account in the app header or modal to access your emails."
            }

        unread = [
            e for e in self.state.get("sandbox_emails", [])
            if e.get("folder") == "inbox" and e.get("unread")
        ][:max_results]
        return {
            "account": self.state.get("gmail", {}).get("email", "alex.morgan@gmail.com"),
            "mode": "Sandbox Mode",
            "count": len(unread),
            "emails": [
                {
                    "id": e["id"],
                    "from": e["sender"],
                    "subject": e["subject"],
                    "snippet": e["snippet"],
                    "date": e["date"],
                    "body": e["body"]
                } for e in unread
            ]
        }

    def search_emails(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        if not self.is_gmail_connected():
            return {
                "error": "Gmail is NOT connected. Please connect your Gmail account in the app header or modal to access your emails."
            }

        q_lower = query.lower()
        results = []
        for e in self.state.get("sandbox_emails", []):
            text_to_search = f"{e.get('subject', '')} {e.get('sender', '')} {e.get('body', '')} {e.get('snippet', '')}".lower()
            if q_lower in text_to_search:
                results.append({
                    "id": e["id"],
                    "folder": e.get("folder", "inbox"),
                    "from": e["sender"],
                    "to": e.get("to", ""),
                    "subject": e["subject"],
                    "snippet": e["snippet"],
                    "date": e["date"],
                    "body": e["body"]
                })
            if len(results) >= max_results:
                break
        return {
            "query": query,
            "account": self.state.get("gmail", {}).get("email", "alex.morgan@gmail.com"),
            "mode": "Sandbox Mode",
            "count": len(results),
            "emails": results
        }

    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        if not self.is_gmail_connected():
            return {
                "error": "Gmail is NOT connected. Please connect your Gmail account in the app header or modal before sending emails."
            }

        sender_email = self.state.get("gmail", {}).get("email", "alex.morgan@gmail.com")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_id = f"sent_{int(time.time())}"
        new_email = {
            "id": new_id,
            "folder": "sent",
            "unread": False,
            "sender": sender_email,
            "to": to,
            "subject": subject,
            "snippet": body[:80] + ("..." if len(body) > 80 else ""),
            "body": body,
            "date": now_str
        }
        self.state.setdefault("sandbox_emails", []).insert(0, new_email)
        self._save_state()
        return {
            "status": "success",
            "message": f"Email successfully sent to {to}",
            "mode": "Sandbox Mode",
            "id": new_id,
            "sender": sender_email,
            "to": to,
            "subject": subject,
            "timestamp": now_str
        }

    def create_email_draft(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        if not self.is_gmail_connected():
            return {
                "error": "Gmail is NOT connected. Please connect your Gmail account in the app header or modal to create drafts."
            }

        sender_email = self.state.get("gmail", {}).get("email", "alex.morgan@gmail.com")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_id = f"draft_{int(time.time())}"
        new_draft = {
            "id": new_id,
            "folder": "drafts",
            "unread": False,
            "sender": sender_email,
            "to": to,
            "subject": subject,
            "snippet": body[:80] + ("..." if len(body) > 80 else ""),
            "body": body,
            "date": now_str
        }
        self.state.setdefault("sandbox_emails", []).insert(0, new_draft)
        self._save_state()
        return {
            "status": "success",
            "message": f"Draft saved successfully for {to}",
            "mode": "Sandbox Mode",
            "draft_id": new_id,
            "to": to,
            "subject": subject,
            "timestamp": now_str
        }

    # -------------------------------------------------------------
    # Google Calendar Tools Implementation (Sandbox / Local)
    # -------------------------------------------------------------
    def is_calendar_connected(self) -> bool:
        return self.state.get("calendar", {}).get("connected", False)

    def list_calendar_events(self, time_min: Optional[str] = None, time_max: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
        if not self.is_calendar_connected():
            return {
                "error": "Google Calendar is NOT connected. Please connect your Google Calendar in the app header or modal to view your schedule."
            }

        events = self.state.get("sandbox_events", [])
        filtered = []
        for ev in events:
            ev_start = ev.get("start", "")
            if time_min and ev_start < time_min:
                continue
            if time_max and ev_start > time_max:
                continue
            filtered.append(ev)
        
        # Sort by start time
        filtered.sort(key=lambda x: x.get("start", ""))
        return {
            "account": self.state.get("calendar", {}).get("email", "alex.morgan@gmail.com"),
            "mode": "Sandbox Mode",
            "count": len(filtered[:max_results]),
            "events": filtered[:max_results]
        }

    def check_calendar_availability(self, start_time: str, end_time: str) -> Dict[str, Any]:
        if not self.is_calendar_connected():
            return {
                "error": "Google Calendar is NOT connected. Please connect your Google Calendar in the app header or modal to check availability."
            }

        # Normalize start_time and end_time strings for comparison
        clean_start = start_time.replace("Z", "").replace("+00:00", "")
        clean_end = end_time.replace("Z", "").replace("+00:00", "")

        events = self.state.get("sandbox_events", [])
        conflicts = []
        for ev in events:
            ev_s = ev.get("start", "").replace("Z", "").replace("+00:00", "")
            ev_e = ev.get("end", "").replace("Z", "").replace("+00:00", "")
            
            # Overlap condition: start < ev_end and end > ev_start
            if clean_start < ev_e and clean_end > ev_s:
                conflicts.append({
                    "summary": ev.get("summary"),
                    "start": ev.get("start"),
                    "end": ev.get("end")
                })
        
        is_available = len(conflicts) == 0
        return {
            "available": is_available,
            "requested_slot": {"start": start_time, "end": end_time},
            "status": "Available" if is_available else "Busy (Conflict found)",
            "conflicts": conflicts,
            "mode": "Sandbox Mode"
        }

    def create_calendar_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if not self.is_calendar_connected():
            return {
                "error": "Google Calendar is NOT connected. Please connect your Google Calendar in the app header or modal before scheduling events."
            }

        new_id = f"evt_{int(time.time())}"
        new_event = {
            "id": new_id,
            "summary": summary,
            "description": description,
            "location": location,
            "start": start_time,
            "end": end_time,
            "attendees": attendees or [self.state.get("calendar", {}).get("email", "alex.morgan@gmail.com")]
        }
        self.state.setdefault("sandbox_events", []).append(new_event)
        self._save_state()
        return {
            "status": "success",
            "message": f"Calendar event '{summary}' scheduled successfully!",
            "event": new_event,
            "mode": "Sandbox Mode"
        }

# Global singleton
integrations_mgr = IntegrationManager()
