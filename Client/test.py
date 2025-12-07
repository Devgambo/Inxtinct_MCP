import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage
from dotenv import load_dotenv
import json
import os

load_dotenv()

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

async def main():
    
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()

    named_tools = {}
    for tool in tools:
        named_tools[tool.name] = tool

    print("Available tools:", named_tools.keys())

    # Initialize Groq LLM
    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0
    )
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Test prompt - must request at least 10 tweets (tool schema requirement)
    # prompt = "Add 1000 rupess I spent in buying cloths yesterday."
    prompt = "Whats the wheater right now in new york, usa?"
    
    response = await llm_with_tools.ainvoke(prompt)
    
    # Check if LLM called any tools
    if not getattr(response, "tool_calls", None):
        print("\nLLM Reply:", response.content)
        return
    
    print(f"\nLLM decided to use {len(response.tool_calls)} tool(s)")
    
    # Execute tool calls
    tool_messages = []
    for tc in response.tool_calls:
        selected_tool_name = tc["name"]
        selected_tool_args = tc.get("args") or {}
        selected_tool_id = tc["id"]
        
        print(f"Calling {selected_tool_name} with args: {selected_tool_args}")
        
        result = await named_tools[selected_tool_name].ainvoke(selected_tool_args)
        print(f"Result: {result}")
        
        tool_messages.append(
            ToolMessage(tool_call_id=selected_tool_id, content=json.dumps(result))
        )
    
    # Get final response with tool results
    final_response = await llm_with_tools.ainvoke([prompt, response, *tool_messages])
    print(f"\nFinal response: {final_response.content}")

if __name__ == '__main__':
    asyncio.run(main())