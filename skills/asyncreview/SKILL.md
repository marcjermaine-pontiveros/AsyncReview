---
name: asyncreview
description: AI-powered GitHub PR/Issue reviews with agentic codebase access. Use when the user needs to review pull requests, analyze code changes, ask questions about PRs, or get AI feedback on GitHub issues.
allowed-tools: Bash(npx asyncreview:*)
---

# AsyncReview CLI

## When to use this skill

Use this skill when the user:
- Asks to review a GitHub pull request
- Wants AI feedback on code changes in a PR
- Needs to check if a PR breaks existing functionality
- Asks questions about a GitHub issue or PR
- Wants to verify if something was missed in a code change


## How to use this skill

1. **Check prerequisites** — Verify `GEMINI_API_KEY` is set
2. **Get the PR/Issue URL** — Ask user if not provided
3. **Formulate a question** — Convert user's request into a specific question
4. **Run the review command** — Execute `npx asyncreview review --url <URL> -q "<question>"`
5. **Present the results** — Share the AI's findings with sources

## Prerequisites

**Before running any command, check for `GEMINI_API_KEY`:**

```bash
echo $GEMINI_API_KEY
```

If empty or not set, ask the user to provide their Gemini API key:
> "AsyncReview requires a Gemini API key. Please set `GEMINI_API_KEY` in your environment or provide it now."

Then set it:
```bash
export GEMINI_API_KEY="user-provided-key"
```

## Quick start

```bash
npx asyncreview review --url <PR_URL> -q "question"   # Review a PR
npx asyncreview review --url <PR_URL> --output markdown     # Markdown output
```

## Core workflow

1. Get PR URL from user
2. Run review with specific question
3. Read the step-by-step reasoning output
4. Model can fetch files outside the diff autonomously

## Commands

### Review

```bash
npx asyncreview review --url <url> -q "question"      # Review with question
npx asyncreview review --url <url> -q "q" --output markdown # Markdown output
npx asyncreview review --url <url> -q "q" -o json     # JSON output
```

**URL formats supported:**
- `https://github.com/owner/repo/pull/123`
- `https://github.com/owner/repo/issues/456`


## Environment variables

```bash
GEMINI_API_KEY="your-key"         # Required: Google Gemini API key
GITHUB_TOKEN="ghp_xxx"            # Optional: For private repos / higher rate limits
```

## Example: Review a PR

```bash
npx asyncreview review \
  --url https://github.com/stanfordnlp/dspy/pull/9223 \
  -q "Does this change break any existing callers?"
```

**Output shows:**
- Step number
- 💭 Reasoning (what the AI is thinking)
- 📝 Code (Python being executed)
- 📤 Output (REPL result)
- Final answer with sources

## Example: Check if feature exists elsewhere

```bash
npx asyncreview review \
  --url https://github.com/owner/repo/pull/123 \
  -q "Fetch src/utils.py and check if deprecated_func is still used"
```

The AI will:
1. Search for the file path
2. Fetch the file via GitHub API
3. Analyze content in the Python sandbox
4. Report findings with evidence

## Output formats

| Format | Flag | Description |
|--------|------|-------------|
| Pretty | (default) | Rich terminal output with boxes |
| Markdown | `--output markdown` or `-o markdown` | Markdown formatted |
| JSON | `--output json` or `-o json` | Machine-readable |
