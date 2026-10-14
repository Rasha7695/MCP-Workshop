import os
from dotenv import load_dotenv

# Load environment variables (like OPENAI_API_KEY, GOOGLE_CLIENT_ID, etc.)
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.agent import run_conversation
from backend.integrations import integrations_mgr
from backend.mcp_client import mcp_mgr

app = FastAPI(title="MCP Workshop - AI Assistant with Gmail & Calendar")

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]] = []

class SandboxConnectRequest(BaseModel):
    service: str = "both"  # "gmail", "calendar", or "both"
    email: Optional[str] = "alex.morgan@gmail.com"
    account_name: Optional[str] = "Alex Morgan"

class DisconnectRequest(BaseModel):
    service: str = "both"  # "gmail", "calendar", "both", or "oauth"

class OAuthConfigRequest(BaseModel):
    client_id: str
    client_secret: str

class SwitchModeRequest(BaseModel):
    mode: str  # "sandbox" or "oauth"

# -------------------------------------------------------------
# Chat Endpoint
# -------------------------------------------------------------
@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    try:
        reply, new_history = run_conversation(request.message, request.history)
        return {"reply": reply, "history": new_history}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# -------------------------------------------------------------
# Integrations Status & Management
# -------------------------------------------------------------
@app.get("/api/integrations/status")
async def get_integrations_status():
    return integrations_mgr.get_status()

@app.post("/api/integrations/switch-mode")
async def switch_mode_endpoint(req: SwitchModeRequest):
    status = integrations_mgr.switch_mode(req.mode)
    return {"status": "success", "integrations": status}

@app.post("/api/integrations/sandbox/connect")
async def connect_sandbox_endpoint(req: SandboxConnectRequest):
    email = req.email.strip() if req.email else "alex.morgan@gmail.com"
    account_name = req.account_name.strip() if req.account_name else "Alex Morgan"
    status = integrations_mgr.connect_sandbox(
        service=req.service,
        email=email,
        account_name=account_name
    )
    return {"status": "success", "integrations": status}

@app.post("/api/integrations/disconnect")
async def disconnect_endpoint(req: DisconnectRequest):
    status = integrations_mgr.disconnect_service(service=req.service)
    return {"status": "success", "integrations": status}

@app.get("/api/integrations/sandbox/data")
async def get_sandbox_data_endpoint():
    return integrations_mgr.get_sandbox_data()

@app.post("/api/integrations/sandbox/reset")
async def reset_sandbox_data_endpoint():
    data = integrations_mgr.reset_sandbox_data()
    return {"status": "success", "data": data}

# -------------------------------------------------------------
# Google OAuth Endpoints
# -------------------------------------------------------------
@app.get("/api/auth/google/config")
async def get_google_config():
    status = integrations_mgr.get_status()
    return status.get("oauth", {})

@app.post("/api/auth/google/config")
async def save_google_config(req: OAuthConfigRequest):
    res = integrations_mgr.save_oauth_credentials(req.client_id, req.client_secret)
    return res

@app.get("/api/auth/google/url")
async def get_google_auth_url(request: Request):
    # Automatically compute default redirect URI based on current request host or env override
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or f"{base_url}/api/auth/google/callback"
    try:
        url = integrations_mgr.get_google_auth_url(redirect_uri=redirect_uri)
        return {"url": url, "redirect_uri": redirect_uri}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@app.get("/api/auth/google/callback")
async def google_auth_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    if error:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Google Authentication Error</title></head>
        <body style="font-family: sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; background:#fff1f0;">
            <div style="background:white; padding:30px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); max-width:400px; text-align:center;">
                <h2 style="color:#cf1322;">Authentication Failed</h2>
                <p>{error}</p>
                <button onclick="window.close()" style="background:#cf1322; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;">Close Window</button>
            </div>
        </body>
        </html>
        """, status_code=400)

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or f"{base_url}/api/auth/google/callback"

    try:
        user_info = await integrations_mgr.exchange_google_code(code=code, redirect_uri=redirect_uri)
        email = user_info.get("email", "your Google account")
        name = user_info.get("name", "User")
        
        # Return friendly page that notifies parent window and self-closes
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Connected to Google</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background: #f0fdf4;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                }}
                .card {{
                    background: white;
                    padding: 32px;
                    border-radius: 16px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.08);
                    text-align: center;
                    max-width: 420px;
                }}
                .icon {{ font-size: 48px; margin-bottom: 16px; }}
                h2 {{ color: #166534; margin: 0 0 8px 0; font-size: 1.4rem; }}
                p {{ color: #4b5563; font-size: 0.95rem; margin-bottom: 20px; }}
                .badge {{ background: #dcfce7; color: #15803d; padding: 6px 14px; border-radius: 20px; font-weight: 600; display: inline-block; margin-bottom: 16px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="icon">✅</div>
                <div class="badge">Google Account Connected</div>
                <h2>Welcome, {name}!</h2>
                <p>Successfully linked <strong>{email}</strong> with Gmail & Google Calendar tools.</p>
                <p style="font-size: 0.85rem; color: #6b7280;">This window will close automatically...</p>
            </div>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{ type: 'GOOGLE_AUTH_SUCCESS', email: '{email}' }}, '*');
                    setTimeout(() => window.close(), 1200);
                }} else {{
                    setTimeout(() => window.location.href = '/', 1500);
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Connection Error</title></head>
        <body style="font-family: sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; background:#fff1f0;">
            <div style="background:white; padding:30px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); max-width:440px; text-align:center;">
                <h2 style="color:#cf1322;">OAuth Exchange Failed</h2>
                <p style="color:#666; font-size:0.9rem;">{str(e)}</p>
                <button onclick="window.close()" style="background:#cf1322; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;">Close</button>
            </div>
        </body>
        </html>
        """, status_code=500)

# -------------------------------------------------------------
# Model Context Protocol (MCP) Endpoints
# -------------------------------------------------------------
@app.get("/api/mcp/status")
def get_mcp_status():
    """Returns connected MCP servers and discovered tools."""
    return mcp_mgr.get_all_servers_status()

@app.post("/api/mcp/refresh")
def refresh_mcp_servers():
    """Forces refreshing tool discovery via JSON-RPC tools/list."""
    for s_id in mcp_mgr.servers.keys():
        mcp_mgr.list_mcp_tools(s_id)
    return mcp_mgr.get_all_servers_status()

class MCPCallRequest(BaseModel):
    server_id: str
    tool_name: str
    arguments: Dict[str, Any] = {}

@app.post("/api/mcp/call")
def call_mcp_tool_endpoint(req: MCPCallRequest):
    """Directly test an MCP tool via JSON-RPC tools/call."""
    res = mcp_mgr.call_mcp_tool(req.server_id, req.tool_name, req.arguments)
    return res

# Serve the static frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
