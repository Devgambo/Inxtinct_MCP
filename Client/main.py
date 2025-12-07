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
    "twitter-mcp": {
      "transport": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@enescinar/twitter-mcp"
      ],
      "env": {
        "API_KEY": os.getenv("API_KEY"),
        "API_SECRET_KEY": os.getenv("API_SECRET_KEY"),
        "ACCESS_TOKEN": os.getenv("ACCESS_TOKEN"),
        "ACCESS_TOKEN_SECRET": os.getenv("ACCESS_TOKEN_SECRET")
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
        "C:\\Users\\priya\\OneDrive\\Desktop\\Inxtinct\\DatabaseServer\\main.py",
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
        "C:\\Users\\priya\\OneDrive\\Desktop\\Inxtinct\\WeatherServer\\main.py"
      ]
    }
}

# Streamlit Page Configuration
st.set_page_config(layout="wide", page_title="Inxtinct MCP Client")

# Custom CSS for Dark Theme, No Rounded Corners, No Gradients
st.markdown("""
<style>
    /* Force Dark Theme & Full Height */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Remove rounding & standard Streamlit spacing */
    * {
        border-radius: 0px !important;
    }
    .block-container {
        padding-top: 2rem !important; /* Reduce top padding */
        padding-bottom: 5rem !important; /* Space for bottom input */
        max-width: 100% !important;
    }
    
    /* Remove gradients/shadows */
    .stChatInputContainer, div[data-testid="stChatMessage"] {
        box-shadow: none !important;
        background-image: none !important;
    }
    
    /* Chat Message Styling */
    div[data-testid="stChatMessage"] {
        border: 1px solid #333;
        background-color: #1a1c24;
        margin-bottom: 1rem;
        border-right: none;
        border-left: none;
        border-top: none;
    }

    /* 
       LAYOUT ENGINE
    */

    /* LEFT COLUMN: CHAT (75%) */
    div[data-testid="column"]:nth-of-type(1) {
        /* Standard flow for Chat column */
        margin-right: 0; 
        width: 75% !important;
        flex: none !important;
        display: block !important;
    }

    /* RIGHT COLUMN: TOOLS (25%) */
    div[data-testid="column"]:nth-of-type(2) {
        position: fixed !important;
        right: 0;
        top: 3.5rem; /* Match header height approx */
        width: 25% !important;
        height: calc(100vh - 3.5rem) !important;
        background-color: #0e1117;
        border-left: 1px solid #333;
        padding: 1rem;
        overflow-y: auto !important;
        z-index: 99;
    }

    /* INPUT CONTAINER - The critical part */
    div[data-testid="stBottom"] {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 25%; /* Stop at 75% width (100% - 25%) */
        width: 75% !important; 
        background-color: #0e1117;
        z-index: 1000;
        border-top: 1px solid #333;
    }
    
    /* Header cleanup */
    header { 
        background-color: #0e1117 !important;
    }

    /* Input & Button Styling */
    .stTextInput input, .stTextArea textarea {
        background-color: #1a1c24;
        border: 1px solid #333;
        color: white;
    }
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
    # MOVED OUTSIDE OF COLUMN TO FORCE BOTTOM PINNING
    pass

# Main Chat Input (Pinned to Bottom via Streamlit Default + CSS Width Restriction)
if prompt := st.chat_input("Enter your prompt..."):
    # Display User Message
    with chat_col: # Show message in Chat Column
        with st.chat_message("user"):
            st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Run Agent
    with chat_col: # Show response in Chat Column
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
