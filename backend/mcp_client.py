import json
import os
import subprocess
import httpx
from typing import Dict, Any, List, Optional
from backend.integrations import integrations_mgr

class MCPClientManager:
    """
    Client for Model Context Protocol (MCP) servers.
    Supports:
    - Open-source Google Calendar MCP (@cocal/google-calendar-mcp) over stdio
    - Open-source Gmail MCP (@gongrzhe/server-gmail-autoauth-mcp) over stdio
    """

    def __init__(self):
        # Resolve path to gcp-oauth.keys.json
        default_keys_path = os.getenv(
            "GOOGLE_OAUTH_CREDENTIALS",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gcp-oauth.keys.json"))
        )

        self.default_keys_path = default_keys_path

        self.servers = {
            # =============================================================
            # COMMENTED OUT: Official Google Gmail Remote MCP Server
            # (Replaced by open-source STDIO Gmail MCP)
            # =============================================================
            # "gmail_mcp": {
            #     "name": "Google Gmail MCP Server (Official Google)",
            #     "url": "https://gmailmcp.googleapis.com/mcp/v1",
            #     "type": "http",
            #     "enabled": False,
            #     "cached_tools": []
            # },

            # =============================================================
            # Open-Source Gmail MCP Server (@gongrzhe/server-gmail-autoauth-mcp)
            # =============================================================
            "google-gmail": {
                "name": "Gmail (@gongrzhe/server-gmail-autoauth-mcp)",
                "command": "npx",
                "args": ["-y", "@gongrzhe/server-gmail-autoauth-mcp"],
                "env": {
                    "GMAIL_OAUTH_PATH": default_keys_path
                },
                "type": "stdio",
                "enabled": True,
                "cached_tools": []
            },

            # =============================================================
            # COMMENTED OUT: Official Google Calendar Remote MCP Server
            # (Replaced by open-source @cocal/google-calendar-mcp)
            # =============================================================
            # "calendar_mcp": {
            #     "name": "Google Calendar MCP Server (Official Google)",
            #     "url": "https://calendarmcp.googleapis.com/mcp/v1",
            #     "type": "google_workspace",
            #     "enabled": False,
            #     "cached_tools": []
            # },

            # =============================================================
            # Open-Source Google Calendar MCP Server (@cocal/google-calendar-mcp)
            # =============================================================
            "google-calendar": {
                "name": "Google Calendar (@cocal/google-calendar-mcp)",
                "command": "npx",
                "args": ["-y", "@cocal/google-calendar-mcp"],
                "env": {
                    "GOOGLE_OAUTH_CREDENTIALS": default_keys_path
                },
                "type": "stdio",
                "enabled": True,
                "cached_tools": []
            }
        }

    def _sync_oauth_credentials(self):
        """
        Ensures gcp-oauth.keys.json exists and tokens are synced to:
        1. ~/.config/google-calendar-mcp/tokens.json for @cocal/google-calendar-mcp
        2. ~/.gmail-mcp/credentials.json & gcp-oauth.keys.json for @gongrzhe/server-gmail-autoauth-mcp
        """
        import shutil
        oauth = integrations_mgr.state.get("oauth_config", {})
        client_id = oauth.get("client_id")
        client_secret = oauth.get("client_secret")
        access_token = oauth.get("access_token")
        refresh_token = oauth.get("refresh_token")

        # 1. Ensure keys file exists
        keys_path = self.default_keys_path
        if keys_path and not os.path.exists(keys_path) and client_id and client_secret:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(keys_path)), exist_ok=True)
                with open(keys_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "installed": {
                            "client_id": client_id,
                            "project_id": "mcp-wrokshop",
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "client_secret": client_secret,
                            "redirect_uris": ["http://localhost"]
                        }
                    }, f, indent=2)
            except Exception as e:
                print(f"[MCP] Warning: could not write keys file: {e}")

        # If no tokens, clean up any persisted MCP credentials so re-authorization is required
        cal_token_file = os.path.expanduser("~/.config/google-calendar-mcp/tokens.json")
        gmail_token_file = os.path.expanduser("~/.gmail-mcp/credentials.json")
        if not (access_token or refresh_token):
            for fpath in [cal_token_file, gmail_token_file]:
                try:
                    if os.path.exists(fpath):
                        os.remove(fpath)
                except Exception:
                    pass
            return

        # 2. Sync token to ~/.config/google-calendar-mcp/tokens.json
        if access_token or refresh_token:
            try:
                cal_token_dir = os.path.expanduser("~/.config/google-calendar-mcp")
                os.makedirs(cal_token_dir, exist_ok=True)
                cal_token_file = os.path.join(cal_token_dir, "tokens.json")
                cal_token_data = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "scope": "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar.readonly openid email profile",
                    "token_type": "Bearer",
                    "expiry_date": int(oauth.get("expires_at", 0) * 1000)
                }
                with open(cal_token_file, "w", encoding="utf-8") as f:
                    json.dump(cal_token_data, f, indent=2)
            except Exception as e:
                print(f"[MCP] Warning: could not sync tokens to @cocal calendar storage: {e}")

        # 3. Sync token and keys to ~/.gmail-mcp/ for @gongrzhe/server-gmail-autoauth-mcp
        if access_token or refresh_token:
            try:
                gmail_dir = os.path.expanduser("~/.gmail-mcp")
                os.makedirs(gmail_dir, exist_ok=True)
                if os.path.exists(keys_path):
                    shutil.copy(keys_path, os.path.join(gmail_dir, "gcp-oauth.keys.json"))
                gmail_token_file = os.path.join(gmail_dir, "credentials.json")
                gmail_token_data = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "scope": "https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.settings.basic openid email profile",
                    "token_type": "Bearer",
                    "expiry_date": int(oauth.get("expires_at", 0) * 1000)
                }
                with open(gmail_token_file, "w", encoding="utf-8") as f:
                    json.dump(gmail_token_data, f, indent=2)
            except Exception as e:
                print(f"[MCP] Warning: could not sync tokens to ~/.gmail-mcp storage: {e}")

    # Backward compatibility alias
    def _sync_calendar_oauth(self):
        self._sync_oauth_credentials()

    def _run_stdio_jsonrpc(self, server: dict, method: str, params: dict) -> Dict[str, Any]:
        """
        Executes a JSON-RPC request over STDIO to an MCP server process.
        """
        self._sync_oauth_credentials()

        env = os.environ.copy()
        env.update(server.get("env", {}))

        cmd = [server.get("command", "npx")] + server.get("args", [])

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env
            )

            def _read_json_response():
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        return None
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        return json.loads(line)
                    except Exception:
                        continue

            # Step 1: Initialize
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "tool-calling-assistant", "version": "1.0.0"}
                }
            }
            proc.stdin.write(json.dumps(init_req) + "\n")
            proc.stdin.flush()
            _ = _read_json_response()

            # Step 2: Initialized notification
            notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            proc.stdin.write(json.dumps(notif) + "\n")
            proc.stdin.flush()

            # Step 3: Execute method
            exec_req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": method,
                "params": params
            }
            proc.stdin.write(json.dumps(exec_req) + "\n")
            proc.stdin.flush()

            resp = _read_json_response()
            proc.terminate()

            if resp:
                return resp
            else:
                stderr_output = proc.stderr.read()
                return {"error": f"Process produced no output. Stderr: {stderr_output}"}
        except Exception as e:
            return {"error": f"Error running stdio MCP server: {str(e)}"}

    def get_auth_token(self) -> Optional[str]:
        return integrations_mgr._get_valid_access_token()

    def list_mcp_tools(self, server_id: str) -> List[Dict[str, Any]]:
        server = self.servers.get(server_id)
        if not server:
            return []

        # If stdio server
        if server.get("type") == "stdio":
            resp = self._run_stdio_jsonrpc(server, "tools/list", {})
            tools = resp.get("result", {}).get("tools", [])
            server["cached_tools"] = tools
            return tools

        # If HTTP server (e.g. Gmail MCP)
        token = self.get_auth_token()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(server["url"], headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    tools = data.get("result", {}).get("tools", [])
                    server["cached_tools"] = tools
                    return tools
                else:
                    print(f"[MCP] Failed to list tools from {server['url']}: {resp.status_code}")
        except Exception as e:
            print(f"[MCP] Error listing tools from {server.get('url')}: {e}")
        return server.get("cached_tools", [])

    def call_mcp_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        server = self.servers.get(server_id)
        if not server:
            return {"error": f"MCP server '{server_id}' not found."}

        # If stdio server (@cocal/google-calendar-mcp)
        if server.get("type") == "stdio":
            resp = self._run_stdio_jsonrpc(server, "tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            if "result" in resp:
                content = resp["result"].get("content", [])
                text_content = ""
                for c in content:
                    if c.get("type") == "text":
                        text_content += c.get("text", "")
                return {
                    "mcp_server": server["name"],
                    "status": "success",
                    "result": text_content or resp["result"]
                }
            return resp

        # If HTTP server
        token = self.get_auth_token()
        if not token:
            return {
                "error": "Google OAuth access token is required. Please sign in with Google in the app header."
            }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            with httpx.Client(timeout=25.0) as client:
                resp = client.post(server["url"], headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    res = data.get("result", {})
                    if res.get("isError"):
                        err_text = ""
                        for c in res.get("content", []):
                            err_text += c.get("text", "")
                        return {
                            "mcp_server": server["name"],
                            "status": "mcp_error",
                            "message": err_text,
                            "raw_result": res
                        }
                    return {
                        "mcp_server": server["name"],
                        "status": "success",
                        "result": res
                    }
                else:
                    return {"error": f"MCP server returned HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"error": f"Exception calling MCP server tool '{tool_name}': {str(e)}"}

    def get_all_servers_status(self) -> Dict[str, Any]:
        result = {}
        for s_id, s_info in self.servers.items():
            cached_count = len(s_info.get("cached_tools", []))
            if cached_count == 0:
                tools = self.list_mcp_tools(s_id)
                cached_count = len(tools)
            is_authenticated = False
            if s_info.get("type") == "stdio":
                is_authenticated = bool(
                    integrations_mgr.state.get("oauth_config", {}).get("access_token")
                    or integrations_mgr.state.get("oauth_config", {}).get("refresh_token")
                    or os.path.exists(self.default_keys_path)
                )
            else:
                is_authenticated = bool(self.get_auth_token())

            cred_path = (
                s_info.get("env", {}).get("GOOGLE_OAUTH_CREDENTIALS")
                or s_info.get("env", {}).get("GMAIL_OAUTH_PATH")
                or self.default_keys_path
            )

            result[s_id] = {
                "name": s_info["name"],
                "url": s_info.get("url", s_info.get("command")),
                "type": s_info["type"],
                "enabled": s_info["enabled"],
                "authenticated": is_authenticated,
                "command": s_info.get("command"),
                "args": s_info.get("args"),
                "credentials_path": cred_path,
                "tool_count": cached_count,
                "tools": [
                    {
                        "name": t.get("name"),
                        "title": t.get("annotations", {}).get("title", t.get("title", t.get("name"))),
                        "description": t.get("description", "")[:120]
                    } for t in s_info.get("cached_tools", [])
                ]
            }
        return result

    def get_openai_mcp_tools(self, server_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Convert all discovered MCP tools into OpenAI function calling format.
        If server_id is provided, only tools from that server are returned.
        """
        openai_tools = []
        for s_id, s_info in self.servers.items():
            if not s_info.get("enabled"):
                continue
            if server_id and s_id != server_id:
                continue
            tools = s_info.get("cached_tools")
            if not tools:
                tools = self.list_mcp_tools(s_id)

            for t in tools:
                schema = t.get("inputSchema", {"type": "object", "properties": {}})
                clean_schema = {
                    "type": schema.get("type", "object"),
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", [])
                }
                # Sanitize name for OpenAI function calling (replace hyphens with underscores if needed)
                clean_name = t["name"].replace("-", "_")
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": f"mcp_{clean_name}",
                        "description": f"[{s_info['name']}] {t.get('description', '')}",
                        "parameters": clean_schema
                    }
                })
        return openai_tools

    def dispatch_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Dispatch a tool call from OpenAI/OpenRouter to the corresponding MCP server.
        """
        real_name = tool_name
        if real_name.startswith("mcp_"):
            real_name = real_name[4:]

        # Find which server has this tool (checking both underscore and hyphen forms)
        for s_id, s_info in self.servers.items():
            if not s_info.get("enabled"):
                continue
            tools = s_info.get("cached_tools")
            if not tools:
                tools = self.list_mcp_tools(s_id)
            for t in tools:
                t_name = t.get("name")
                if t_name == real_name or t_name.replace("-", "_") == real_name:
                    res = self.call_mcp_tool(s_id, t_name, arguments)
                    return json.dumps(res, indent=2)

        return json.dumps({"error": f"Tool '{tool_name}' not found on any connected MCP server."})

# Global MCP Client Manager instance
mcp_mgr = MCPClientManager()
