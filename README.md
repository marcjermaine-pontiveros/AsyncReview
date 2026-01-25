# AsyncReview
Open-source Agentic code review tool inspired by DevinReview, using Recursive Language Models (RLM)

## Prerequisites

- **Python 3.11+**
- **Node.js** (or Bun)
- **uv** (recommended for Python package management)
- **Deno** (Required for sandboxed code execution)

## Setup

1. **Install Backend (cr)**
   ```bash
   # Using uv (Recommended)
   uv pip install -e .

   # Or standard pip
   pip install -e .
   ```

2. **Install Frontend (web)**
   ```bash
   cd web
   bun install  # or npm install
   ```

3. **Environment Setup**
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   **Required variables:**
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `GITHUB_TOKEN`: GitHub Token (for PR access & higher rate limits).

## Running

### 1. Start the API Server
```bash
cr serve
# or
uv run uvicorn cr.server:app --reload
```
Server runs at `http://127.0.0.1:8000`.

### 2. Start the Web UI
```bash
cd web
bun dev
```
Open `http://localhost:3000` in your browser.

## CLI Usage

You can also use the tool directly from the terminal:

- **Interactive Q&A**: `cr ask`
- **One-shot Review**: `cr review -q "What does this repo do?"`
- **Help**: `cr --help`