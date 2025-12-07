import streamlit as st
import asyncio
import os
import json
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

# Load environment variables
load_dotenv()

# Server Configuration (Duplicated from test.py)
SERVERS = { 
    "manim-server": {
      "transport": "stdio",
      "command": "C:\\Users\\priya\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": [
        "C:\\Users\\priya\\OneDrive\\Desktop\\current\\MCP\\manim-mcp-server\\src\\manim_server.py"
      ],
      "env": {
        "MANIM_EXECUTABLE": "C:\\Users\\priya\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\manim.exe"
      }
    },
    "twitter-mcp": {
      "transport": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@enescinar/twitter-mcp"
      ],
      "env": {
        "API_KEY": "z3GFFcVBAYDQyZK9rjTRvLwWv",
        "API_SECRET_KEY": "UIg06cGARg0tIdqxFlxr8D7ez7vnswmz2aH1602tgrPcSpNhVe",
        "ACCESS_TOKEN": "1785618844029214720-xxwvhoiRSLc4ivHZQZjR7VKnXyfTyC",
        "ACCESS_TOKEN_SECRET": "iNsfbIyAiF0071boJE1CTDF9luOVRvjTmSpp8n35PLcik"
      }
    },
    "ExpenseTracker": {
      "transport": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "C:\\Users\\priya\\OneDrive\\Desktop\\current\\MCP\\demo-server-1\\main.py"
      ]
    },
    "weather-server": {
      "transport": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "--with",
        "httpx",
        "fastmcp",
        "run",
        "C:\\Users\\priya\\OneDrive\\Desktop\\current\\MCP\\weather-server\\main.py"
      ]
    }
}

# Streamlit Page Configuration
st.set_page_config(layout="wide", page_title="Inxtinct MCP Client")

# Custom CSS for Dark Theme, No Rounded Corners, No Gradients
st.markdown("""
<style>
    /* Force Dark Theme Backgrounds */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Remove rounded corners from everything */
    * {
        border-radius: 0px !important;
    }
    
    /* Remove gradients and shadows */
    .stChatInputContainer, div[data-testid="stChatMessage"] {
        box-shadow: none !important;
        background-image: none !important;
    }
    
    /* Custom Styling for Chat Messages */
    div[data-testid="stChatMessage"] {
        border: 1px solid #333;
        background-color: #1a1c24;
    }
    
    /* Right Side Panel Styling */
    div[data-testid="column"]:nth-of-type(2) {
        border-left: 1px solid #333;
        padding-left: 1rem;
    }
    
    /* Input Box Styling */
    .stTextInput input, .stTextArea textarea {
        background-color: #1a1c24;
        border: 1px solid #333;
        color: white;
    }
    
    /* Button Styling */
    button {
        border: 1px solid #333;
        box-shadow: none !important;
    }

</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def get_llm():
    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0
    )

async def get_mcp_tools():
    """Fetches tools from MCP servers. 
    Note: In a production app, we would want to persist the client connection.
    Here we might reconnect per run to be safe with asyncio loops in Streamlit."""
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()
    return tools, client

async def process_message(prompt, chat_history):
    llm = get_llm()
    # Temporarily reconstruct client to get tools and bind them
    # This is expensive but ensures fresh loop context
    client = MultiServerMCPClient(SERVERS)
    try:
        tools = await client.get_tools()
        named_tools = {tool.name: tool for tool in tools}
        llm_with_tools = llm.bind_tools(tools)
        
        # Prepare history
        messages = []
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                # We simplified history for display, but ideally we'd keep ToolMessages too.
                # For this simple UI, we'll just append previous text.
                # A more robust history would serialize full message objects.
                messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=prompt))
        
        # 1. LLM Step
        response = await llm_with_tools.ainvoke(messages)
        
        tool_results = []
        
        # 2. Tool Invocation Step if needed
        if getattr(response, "tool_calls", None):
            tool_messages = []
            for tc in response.tool_calls:
                selected_tool_name = tc["name"]
                selected_tool_args = tc.get("args") or {}
                selected_tool_id = tc["id"]
                
                # Update UI with "Thinking/Working..." equivalent
                # st.toast(f"Running tool: {selected_tool_name}...") 
                
                result = await named_tools[selected_tool_name].ainvoke(selected_tool_args)
                
                tool_messages.append(
                    ToolMessage(tool_call_id=selected_tool_id, content=json.dumps(result))
                )
                tool_results.append(f"Used {selected_tool_name}: {json.dumps(result)}")

            # 3. Final Response with Tool Outputs
            final_response = await llm_with_tools.ainvoke(messages + [response, *tool_messages])
            return final_response.content, tool_results
        
        return response.content, tool_results

    finally:
        # Cleanup if client has close method (MultiServerMCPClient currently doesn't expose explicit close easily in async context unless used as context manager, 
        # but garbage collection should handle stdio pipes eventually or OS cleaning up orphan processes if main process dies.
        # For a persistent app, managing lifecycle is critical.)
        pass

# Layout: Chat (Left) | Tools (Right)
chat_col, tools_col = st.columns([0.75, 0.25])

with tools_col:
    st.header("Tools")
    st.caption("Available MCP Tools")
    
    # We fetch tools to display them. 
    # To avoid re-spawning servers just for listing, we cache the list if possible, or just fetch.
    # For now, let's fetch.
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Just getting tools description
        # We use a separate quick function or cache this data to avoid heavy startup every time.
        # But since we can't easily cache async client across reruns safely without robust loop handling:
        # We will just show a static placeholder or try to fetch if we had a persistent state.
        # Let's try to fetch live but show a spinner.
        with st.spinner("Loading tools..."):
            # Simplified tool fetching for display only
            async def fetch_tool_names():
                c = MultiServerMCPClient(SERVERS)
                t = await c.get_tools()
                return [tool.name for tool in t]
            
            tool_names = loop.run_until_complete(fetch_tool_names())
            
            for name in tool_names:
                st.code(name, language="text")
                
    except Exception as e:
        st.error(f"Could not load tools: {e}")

with chat_col:
    st.header("Chat")
    
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Enter your prompt..."):
        # Display User Message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Variable to hold tool outputs for display
        tool_outputs_display = []
        
        # Run Agent
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                # We need a fresh loop for correct async execution in the event handler
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                response_text, tool_logs = loop.run_until_complete(process_message(prompt, st.session_state.messages[:-1]))
                
                # Append tool logs to response for visibility if desired, or just show final
                full_response = response_text
                if tool_logs:
                    with st.expander("Tool Usage Details"):
                        for log in tool_logs:
                            st.code(log, language="json")
                
                message_placeholder.markdown(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                message_placeholder.error(f"Error: {str(e)}")
