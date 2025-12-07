# Inxtinct Assignment 
###  ~By Priyanshu Kumar Rai
### Demo- https://drive.google.com/drive/folders/1m4Rt9AMQJ48j-BsautLSo7uzq6WRxcy-

This is AI-powered application that leverages the **Model Context Protocol (MCP)** to connect a Large Language Model (LLM) with various local and remote tools. It features a modern **Streamlit** user interface that acts as a central hub for chatting with an agent capable of tracking expenses, checking weather, and interacting with social media.

## 🏗 Architecture

The project follows a multi-server MCP architecture:

1.  **Client (`/Client`)**: A Streamlit frontend that connects to multiple MCP servers. It uses **LangChain** to orchestrate interactions between the user, the LLM (Groq), and the available tools.
2.  **Database Server (`/DatabaseServer`)**: A local **FastAPI** + **SQLite** server that provides expense tracking capabilities (Add, List, Summarize).
3.  **Weather Server (`/WeatherServer`)**: A **FastAPI** server that fetches real-time weather data from open-meteo APIs.
4.  **Twitter MCP**: An external MCP server (via `npx`) for Twitter interactions.

## 🚀 Technologies Used

*   **Frontend**: [Streamlit](https://streamlit.io/) (with custom CSS for a fixed-layout Dashboard)
*   **AI/LLM orchestration**:
    *   [LangChain](https://www.langchain.com/)
    *   `langchain-mcp-adapters`
    *   `langchain-groq`
*   **Backend / Servers**:
    *   [FastMCP](https://github.com/jlowin/fastmcp)
    *   `uv` and `pip` for dependency management
*   **Database**: SQLite (for Expense Tracker)
*   **External APIs**: Open-Meteo (Weather), Twitter API.

## 📂 Project Structure

```
Inxtinct/
├── Client/
│   └── main.py          # Main Streamlit application & MCP Client
├── DatabaseServer/
│   ├── server.py        # FastAPI server for Expenses
│   ├── main.py          # MCP Entrypoint
│   └── expenses.db      # SQLite Database
├── WeatherServer/
│   ├── server.py        # FastAPI server for Weather
│   └── main.py          # MCP Entrypoint
└── pyproject.toml       # Project Dependencies
```

## 🛠️ Setup & Usage

### Prerequisites
*   Python 3.13+
*   `uv` (Package manager)
*   Node.js & `npx` (for Twitter MCP)
*   Groq API Key
*   Twitter API Keys (if using Twitter tools)

### Environment Variables
Create a `.env` file in the `Client/` directory with the following keys:

```env
GROQ_API_KEY=your_groq_api_key
twitter api keys
```

### Running the App

The application uses `uv` to manage dependencies and run the client.

```bash
# Navigate to the Client directory
cd Client

# Run the Streamlit App
uv run streamlit run main.py
```

*Note: The separate MCP servers (Database, Weather) are automatically started by the Client script as subprocesses.*

## ✨ Features

*   **Natural Language Expense Tracking**: "Add 500 for lunch" -> Automatically categorized and saved to DB.
*   **Live Weather Updates**: "What's the weather in London?" -> Fetches live data.
*   **Twitter Integration**: Post and search tweets directly from the chat.
*   **Persistent Chat History**: Maintains context during the session.
*   **Modern UI**: Dark-themed, fixed-layout interface with dedicated Tools sidebar.

## Issues

* the compromised twitter api keys have been taken care of.
