import json
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any, Tuple

from backend.tools import (
    TOOL_DEFINITIONS,
    TOOL_FUNCTIONS,
    LOCAL_GMAIL_TOOLS,
    LOCAL_CALENDAR_TOOLS,
    LOCAL_GENERAL_TOOLS
)
from backend.integrations import integrations_mgr
from backend.mcp_client import mcp_mgr

load_dotenv()

def get_openai_client() -> OpenAI:
    """Retrieve or initialize the OpenAI/OpenRouter client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY. Please add your API key in the .env file.")
    
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    return OpenAI(api_key=api_key, base_url=base_url)

def determine_service_modes(user_message: str = "") -> Tuple[bool, bool]:
    """
    Determines whether Gmail and Calendar should use sandbox (local tools) or live (MCP tools).
    - If in sandbox mode OR live isn't available -> local tools are called (sandbox)
    - Otherwise -> MCP tools are called (live)
    """
    integrations_mgr.reload_state()
    gmail_state = integrations_mgr.state.get("gmail", {})
    calendar_state = integrations_mgr.state.get("calendar", {})
    gmail_mode = gmail_state.get("mode", "sandbox")
    calendar_mode = calendar_state.get("mode", "sandbox")

    oauth_cfg = integrations_mgr.state.get("oauth_config", {})
    live_is_available = bool(oauth_cfg.get("access_token") and oauth_cfg.get("user_email"))

    # When live isn't available, always default to sandbox
    if not live_is_available:
        return True, True

    msg_lower = user_message.lower()
    force_sandbox = any(phrase in msg_lower for phrase in ["sandbox mode", "in sandbox", "use sandbox", "testing sandbox", "test sandbox"])
    force_mcp = any(phrase in msg_lower for phrase in ["mcp mode", "use mcp", "via mcp", "mcp tool", "mcp server", "live mode"])

    if force_sandbox and not force_mcp:
        gmail_is_sandbox = True
        calendar_is_sandbox = True
    elif force_mcp and not force_sandbox:
        gmail_is_sandbox = False
        calendar_is_sandbox = False
    else:
        gmail_is_sandbox = (gmail_mode == "sandbox")
        calendar_is_sandbox = (calendar_mode == "sandbox")

    return gmail_is_sandbox, calendar_is_sandbox

def get_available_tools(gmail_is_sandbox: bool, calendar_is_sandbox: bool) -> List[Dict[str, Any]]:
    """
    Returns the tool definitions to pass to OpenAI:
    - In Sandbox mode: local tools from backend/tools.py are used
    - Otherwise (OAuth, live, or unconfigured): MCP tools from MCPClientManager are used
    """
    tools = []

    # 1. Base tools (calculate_total)
    for t in TOOL_DEFINITIONS:
        if t["function"]["name"] in LOCAL_GENERAL_TOOLS:
            tools.append(t)

    # 2. Gmail tools: local if sandbox, MCP otherwise
    if gmail_is_sandbox:
        for t in TOOL_DEFINITIONS:
            if t["function"]["name"] in LOCAL_GMAIL_TOOLS:
                tools.append(t)
    else:
        try:
            mcp_gmail_tools = mcp_mgr.get_openai_mcp_tools(server_id="google-gmail")
            if not mcp_gmail_tools:
                mcp_gmail_tools = mcp_mgr.get_openai_mcp_tools(server_id="gmail_mcp")
            tools.extend(mcp_gmail_tools)
        except Exception as e:
            print(f"[Agent] Warning: could not load Gmail MCP tools: {e}")

    # 3. Calendar tools: local if sandbox, MCP otherwise
    if calendar_is_sandbox:
        for t in TOOL_DEFINITIONS:
            if t["function"]["name"] in LOCAL_CALENDAR_TOOLS:
                tools.append(t)
    else:
        try:
            mcp_cal_tools = mcp_mgr.get_openai_mcp_tools(server_id="google-calendar")
            tools.extend(mcp_cal_tools)
        except Exception as e:
            print(f"[Agent] Warning: could not load Google Calendar MCP tools: {e}")

    return tools

def get_system_prompt(gmail_is_sandbox: bool, calendar_is_sandbox: bool) -> dict:
    now = datetime.now()
    now_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
    iso_str = now.strftime("%Y-%m-%dT%H:%M:%S")

    gmail_status_str = "SANDBOX MODE (calling local mock tools for Alex Morgan)" if gmail_is_sandbox else "MCP / LIVE MODE (calling Gmail MCP server tools)"
    cal_status_str = "SANDBOX MODE (calling local mock tools for Alex Morgan)" if calendar_is_sandbox else "MCP / LIVE MODE (calling Google Calendar MCP server tools)"

    prompt_text = (
        "You are an intelligent, precise AI assistant connected to Google Workspace tools.\n"
        f"CURRENT REAL-TIME DATE & TIME: {now_str} (ISO: {iso_str}).\n\n"
        "ACTIVE OPERATING MODES:\n"
        f"- Gmail: {gmail_status_str}\n"
        f"- Calendar: {cal_status_str}\n\n"
        "TOOL ROUTING RULES:\n"
        "- In SANDBOX mode, you are provided with LOCAL tools (e.g. get_unread_emails, search_emails, send_email, create_email_draft, list_calendar_events, check_calendar_availability, create_calendar_event). Always call these local tools to inspect and modify sandbox data.\n"
        "- In MCP / LIVE mode (otherwise), you are provided with Model Context Protocol (MCP) tools prefixed with 'mcp_' (e.g. mcp_list_messages, mcp_send_message, mcp_list_events, mcp_create_event, etc.). Always call these MCP tools to interact with real Google accounts.\n\n"
        "CORE RULES:\n"
        "1. When calling tools, you are STRICTLY FORBIDDEN from guessing, assuming, or making up any parameters. "
        "If the user does not explicitly provide the information required for a tool, you MUST ask the user for it. "
        "Never use default values for required parameters.\n"
        "2. When scheduling calendar events or checking availability, use the current date and time above to calculate "
        "relative dates (such as 'today', 'tomorrow', 'next Monday') and format them as ISO 8601 strings (e.g. YYYY-MM-DDTHH:MM:SS).\n"
        "3. When executing tools, report results clearly and concisely to the user.\n"
        "4. If a tool indicates that Google Workspace Developer Preview Program enrollment is required or a service is disconnected, "
        "explain this clearly and guide the user on next steps."
    )
    return {"role": "system", "content": prompt_text}

def run_conversation(user_message: str, message_history: list):
    """
    The Core Loop: User -> Model -> Tool -> Model -> Response
    Supports both native local tools (Sandbox mode) and Model Context Protocol (MCP) server tools (otherwise).
    """
    client = get_openai_client()

    # Determine service modes (sandbox vs MCP)
    gmail_is_sandbox, calendar_is_sandbox = determine_service_modes(user_message)
    available_tools = get_available_tools(gmail_is_sandbox, calendar_is_sandbox)

    # Filter out any old system prompts to always use the freshest timestamped system prompt with mode status
    cleaned_history = [m for m in message_history if m.get("role") != "system"]
    messages = [get_system_prompt(gmail_is_sandbox, calendar_is_sandbox)] + cleaned_history + [{"role": "user", "content": user_message}]

    # Allow up to 5 tool-calling turns for complex/multi-step requests
    max_turns = 5
    turn_count = 0

    while turn_count < max_turns:
        turn_count += 1
        
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages,
            tools=available_tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        message_dict = response_message.model_dump(exclude_unset=True)
        messages.append(message_dict)

        # If no tool calls were made, we have the final assistant response
        if not response_message.tool_calls:
            return response_message.content, messages

        # Execute each requested tool call
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            raw_args = tool_call.function.arguments or "{}"
            try:
                function_args = json.loads(raw_args)
            except Exception:
                function_args = {}

            print(f"[Tool Call] Executing '{tool_name}' with args: {function_args}")

            # Check if this is an MCP tool
            if tool_name.startswith("mcp_"):
                try:
                    tool_result = mcp_mgr.dispatch_tool(tool_name, function_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": str(tool_result),
                    })
                except Exception as e:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps({"error": f"MCP error: {str(e)}"})
                    })
                continue

            # Native tool
            if tool_name not in TOOL_FUNCTIONS:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps({"error": f"Tool '{tool_name}' not found."})
                })
                continue
                
            function_to_call = TOOL_FUNCTIONS[tool_name]
            try:
                tool_result = function_to_call(**function_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result),
                })
            except Exception as e:
                print(f"[Tool Error] Error executing '{tool_name}': {e}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps({"error": str(e)})
                })

    # Fallback if loop exceeded max_turns: generate final answer
    final_response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=messages
    )
    final_answer = final_response.choices[0].message.content
    messages.append({"role": "assistant", "content": final_answer})
    return final_answer, messages
