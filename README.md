# Inxtinct Assignment 
###  ~By Priyanshu Kumar Rai
### Demo- https://www.loom.com/share/b64ce434bba94ff78f5f987faf5cdeb2

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
Inxtinct_MCP/
├── Client/
│   ├── main.py              # Main Streamlit application & MCP Client
│   ├── test.py              # Testing utilities
│   └── .env                 # Environment variables (create this)
├── DatabaseServer/
│   ├── server.py            # FastAPI server for Expenses
│   ├── main.py              # MCP Entrypoint
│   ├── categories.json      # Expense categories configuration
│   └── expenses.db          # SQLite Database (auto-generated)
├── WeatherServer/
│   ├── server.py            # FastAPI server for Weather
│   └── main.py              # MCP Entrypoint
├── pyproject.toml           # Project metadata & dependencies
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## 🛠️ Setup & Installation

### Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.13+** - [Download Python](https://www.python.org/downloads/)
*   **uv** (Package manager) - Install via:
    ```bash
    # Windows (PowerShell)
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
*   **Node.js 18+** and **npx** - [Download Node.js](https://nodejs.org/) (npx comes bundled)
*   **Git** - [Download Git](https://git-scm.com/downloads)

### Step-by-Step Installation

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Devgambo/Inxtinct_MCP.git
cd Inxtinct_MCP
```

#### 2️⃣ Install Dependencies

Install all required Python packages using `uv`:

```bash
uv sync
```

Alternatively, if you prefer using pip:

```bash
pip install -r requirements.txt
```

#### 3️⃣ Configure Environment Variables

Create a `.env` file in the `Client/` directory with your API keys:

```bash
cd Client
# Create .env file (Windows)
New-Item .env -ItemType File

# Create .env file (macOS/Linux)
touch .env
```

Add the following configuration to your `.env` file:

```env
# Groq API Configuration (Required)
GROQ_API_KEY=your_groq_api_key_here

# Twitter API Configuration (Optional - only if using Twitter features)
API_KEY=your_twitter_api_key
API_SECRET_KEY=your_twitter_api_secret_key
ACCESS_TOKEN=your_twitter_access_token
ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
```

**How to get API Keys:**
- **Groq API Key**: Sign up at [console.groq.com](https://console.groq.com/)
- **Twitter API Keys**: Create a developer account at [developer.twitter.com](https://developer.twitter.com/)

#### 4️⃣ **IMPORTANT: Update Server Paths** ⚠️

After cloning, you **MUST** update the absolute file paths in `Client/main.py` to match your local setup.

Open `Client/main.py` and locate the `SERVERS` configuration (around lines 14-53). Update the paths in the `args` sections:

**Before (Example paths):**
```python
"ExpenseTracker": {
    "args": [
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "C:\\Users\\priya\\OneDrive\\Desktop\\Inxtinct\\DatabaseServer\\main.py",  # ← Change this
    ]
},
"weather-server": {
    "args": [
        "run",
        "--with",
        "fastmcp",
        "--with",
        "httpx",
        "fastmcp",
        "run",
        "C:\\Users\\priya\\OneDrive\\Desktop\\Inxtinct\\WeatherServer\\main.py"  # ← Change this
    ]
}
```

**After (Your actual paths):**
```python
# Replace with your actual project path
# Windows example: C:\\Users\\YourUsername\\path\\to\\Inxtinct_MCP\\DatabaseServer\\main.py
# macOS/Linux example: /home/yourusername/path/to/Inxtinct_MCP/DatabaseServer/main.py

"ExpenseTracker": {
    "args": [
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "YOUR_ABSOLUTE_PATH/DatabaseServer/main.py",  # Update this path
    ]
},
"weather-server": {
    "args": [
        "run",
        "--with",
        "fastmcp",
        "--with",
        "httpx",
        "fastmcp",
        "run",
        "YOUR_ABSOLUTE_PATH/WeatherServer/main.py"  # Update this path
    ]
}
```

**💡 Tip:** To get your current directory path:
- **Windows PowerShell**: Run `Get-Location` or `pwd`
- **macOS/Linux**: Run `pwd`

### Running the Application

Once setup is complete, navigate to the Client directory and start the app:

```bash
# From the project root
cd Client

# Run the Streamlit application
uv run streamlit run main.py

# Alternative (if using pip)
streamlit run main.py
```

The application will open in your default browser at `http://localhost:8501`

**Note:** The Database and Weather MCP servers are automatically started as subprocesses by the client. You don't need to run them separately.

## ✨ Features

*   **Natural Language Expense Tracking**: "Add 500 for lunch" -> Automatically categorized and saved to DB.
*   **Live Weather Updates**: "What's the weather in London?" -> Fetches live data.
*   **Twitter Integration**: Post and search tweets directly from the chat.
*   **Persistent Chat History**: Maintains context during the session.
*   **Modern UI**: Dark-themed, fixed-layout interface with dedicated Tools sidebar.

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. ModuleNotFoundError or Import Errors
**Problem:** Missing Python dependencies

**Solution:**
```bash
# Reinstall dependencies
uv sync

# Or with pip
pip install -r requirements.txt
```

#### 2. "GROQ_API_KEY not found" Error
**Problem:** Environment variables not loaded

**Solution:**
- Verify `.env` file exists in `Client/` directory
- Check that `GROQ_API_KEY` is correctly set in `.env`
- Restart the Streamlit application

#### 3. Server Connection Failed
**Problem:** Incorrect server paths in `SERVERS` configuration

**Solution:**
- Double-check the absolute paths in `Client/main.py` match your system
- Ensure paths use correct separators (`\\` for Windows, `/` for macOS/Linux)
- Verify `DatabaseServer/main.py` and `WeatherServer/main.py` exist

#### 4. Twitter Tools Not Working
**Problem:** Missing or invalid Twitter API credentials

**Solution:**
- Twitter features are optional - the app will work without them
- If needed, add all four Twitter API keys to your `.env` file
- Verify credentials at [developer.twitter.com](https://developer.twitter.com/)

#### 5. Port Already in Use
**Problem:** Streamlit default port (8501) is occupied

**Solution:**
```bash
# Specify a different port
uv run streamlit run main.py --server.port 8502
```

#### 6. UV Command Not Found
**Problem:** `uv` is not installed or not in PATH

**Solution:**
```bash
# Reinstall uv (Windows PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Restart your terminal after installation
```

### Getting Help

If you encounter issues not listed here:
1. Check the terminal output for specific error messages
2. Verify all prerequisites are installed correctly
3. Ensure you're using Python 3.13 or higher: `python --version`
4. Open an issue on [GitHub](https://github.com/Devgambo/Inxtinct_MCP/issues)

## 📝 Notes

* the compromised twitter api keys have been taken care of.
