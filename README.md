# AsyncReview

**Agentic Code Review for GitHub PRs and Issues**

AsyncReview uses Recursive Language Models (RLM) to go beyond simple diff analysis. It autonomously explores your repository, fetches relevant context, and verifies its findings in a secure sandbox before answering.

- **Python 3.11+**
- **Node.js** (or Bun)
- **uv** (recommended for Python package management)
- **Deno** (Required for sandboxed code execution)


https://github.com/user-attachments/assets/e17951e6-d73d-4cc0-8199-66c7e02f049f




<img width="1146" height="609" alt="Screenshot 2026-01-24 at 10 37 53 PM" src="https://github.com/user-attachments/assets/1b67cf2d-6923-46b8-8fac-83e6bf707ce3" />

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

   **Optional (GitLab Support):**
   - `GITLAB_TOKEN`: GitLab Personal Access Token.
   - `GITLAB_API_BASE`: For self-hosted GitLab (default: `https://gitlab.com/api/v4`).

   **Self-hosted GitHub Enterprise:**
   - `GITHUB_API_BASE`: For GitHub Enterprise (default: `https://api.github.com`).

## Supported Providers

| Provider | Example URL |
|----------|-------------|
| GitHub | `https://github.com/owner/repo/pull/123` |
| GitHub Enterprise | `https://github.example.com/owner/repo/pull/123` |
| GitLab | `https://gitlab.com/owner/repo/-/merge_requests/123` |
| GitLab (self-hosted) | `https://gitlab.example.com/owner/repo/-/merge_requests/123` |

## Running

### 1. Start the API Server
```bash
cr serve
# or
uv run uvicorn cr.server:app --reload
```
       User Request
     "Verify this PR/Issue"
           │
           ▼
+-------------------------------------------------------+
|  AsyncReview Agent (Recursive Loop)                   |
|                                                       |
|  1. Reason & Plan                                     |
|  2. Generate Python Code                              |
|       │                                               |
|       ▼                                               |
|  3. [Python REPL Sandbox]                             |
|     (Executes logic + llm_query() + tool commands)    |
|       │                                               |
|       ▼                                               |
|  4. Tool Interceptor <-----> [GitHub API]             |
|     (FETCH_FILE, SEARCH)     (Fetches real data)      |
|       │                                               |
|       ▼                                               |
|  5. Observe Result & Repeat Recursively               |
+-------------------------------------------------------+
           │
           ▼
      [10x High Quality Answer]
```

#
<img width="588" height="596" alt="image" src="https://github.com/user-attachments/assets/daad14de-119f-45a8-9ad9-db6649dc9c44" />


## Why AsyncReview?

Most AI review tools only look at the lines changed in a Pull Request (the diff). This leads to shallow feedback and hallucinations about files that don't exist. AsyncReview takes a different approach.

| Other Code Review Tools | AsyncReview |
|-------------|-------------|
| **Limited Context:** Only sees the git diff | **Full Context:** Can read any file in the repo to understand dependencies |
| **Static Analysis:** Guesses how code works | **Agentic Analysis:** Can execute search queries and run verification scripts |
| **Hallucinations:** Invents library methods | **Grounded:** cites existing file paths and lines |
| **Simple Prompts:** One-shot generation | **Recursive Reasoning:** Thinks, plans, and iterates before answering |

## Quick Start

No installation required. Run directly with npx:

```bash
npx asyncreview review --url https://github.com/org/repo/pull/123 -q "Check for breaking changes"
```

OR

```bash
npx skills add AsyncFuncAI/AsyncReview
```

## Usage

### Public Repositories

For public repos, you only need a Gemini API key.

```bash
export GEMINI_API_KEY="your-key"
npx asyncreview review --url https://github.com/org/repo/pull/123 -q "Review this"
```

### Private Repositories

For private repos, you also need a GitHub token.

1. **Set your GitHub Token** (or use the `--github-token` flag)
   ```bash
   # If you have GitHub CLI installed
   export GITHUB_TOKEN=$(gh auth token)
   
   # Or manually set it
   export GITHUB_TOKEN="ghp_..."
   ```

2. **Run the review**
   ```bash
   npx asyncreview review --url https://github.com/org/private-repo/pull/456 -q "Security audit"
   ```

## Configuration

**Required:**
- **Gemini API Key:** Get one from Google AI Studio. Set as `GEMINI_API_KEY`.

**Optional:**
- **GitHub Token:** Required for private repositories to access file contents. Set as `GITHUB_TOKEN`.

## For Agents (Claude, Cursor, OpenCode, Gemini, Codex, etc.)

AsyncReview is designed to be used as a **Skill** by other agentic providers. It allows them to "see" and "reason" about codebases they don't have local access to.

### Install via Skills CLI

Run this command to automatically add AsyncReview to your agent's capabilities:

```bash
npx skills add AsyncFuncAI/AsyncReview
```

This works with [vercel/skills](https://github.com/vercel/skills) compatible agents.

### Manual Setup

If you prefer manual configuration, point your agent to the skill definition file:
`skills/asyncreview/SKILL.md`

## Advanced Setup

To run the full backend server or web interface locally, please see the [Installation Guide](INSTALLATION.md).

## License

MIT
