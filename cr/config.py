"""Shared configuration loaded from .env"""

import os
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Make environment loading explicit with opt-out mechanism
if os.getenv("CR_AUTO_LOAD_DOTENV", "true").lower() == "true":
    load_dotenv()


def _get_int(env_var: str, default: int, name: str) -> int:
    """Safely convert environment variable to int with fallback.

    Args:
        env_var: Environment variable name
        default: Default value if env var is not set or invalid
        name: Human-readable name for error messages

    Returns:
        Integer value from env var or default
    """
    value = os.getenv(env_var, str(default))
    try:
        result = int(value)
        if result < 0:
            warnings.warn(f"{name} must be non-negative, got {result}. Using default {default}.")
            return default
        return result
    except ValueError:
        warnings.warn(f"Invalid {env_var} value '{value}', using default {default}")
        return default


def _parse_list_env(value: str | None) -> list[str]:
    """Parse comma-separated environment variable into list.

    Args:
        value: Environment variable value (may be None or empty string)

    Returns:
        List of non-empty stripped strings, or empty list
    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def ensure_cache_dirs() -> None:
    """Create cache directories if they don't exist."""
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)


# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAIN_MODEL = os.getenv("MAIN_MODEL", "gemini/gemini-3-pro-preview")
SUB_MODEL = os.getenv("SUB_MODEL", "gemini/gemini-3-flash-preview")
MAX_ITERATIONS = _get_int("MAX_ITERATIONS", 20, "MAX_ITERATIONS")
MAX_LLM_CALLS = _get_int("MAX_LLM_CALLS", 25, "MAX_LLM_CALLS")

# Repo snapshot constraints
MAX_FILE_BYTES = _get_int("MAX_FILE_BYTES", 200000, "MAX_FILE_BYTES")  # 200KB per file
MAX_TOTAL_BYTES = _get_int("MAX_TOTAL_BYTES", 5000000, "MAX_TOTAL_BYTES")  # 5MB total
INCLUDE_GLOBS = _parse_list_env(os.getenv("INCLUDE_GLOBS"))
EXCLUDE_GLOBS = _parse_list_env(os.getenv("EXCLUDE_GLOBS"))

# Cache/trace directory
CR_CACHE_DIR = Path(os.getenv("CR_CACHE_DIR", os.path.expanduser("~/.cr")))
TRACES_DIR = CR_CACHE_DIR / "traces"
REVIEWS_DIR = CR_CACHE_DIR / "reviews"

# GitHub API configuration (Part 2)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = os.getenv("GITHUB_API_BASE", "https://api.github.com")

# GitLab API configuration
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_API_BASE = os.getenv("GITLAB_API_BASE", "https://gitlab.com/api/v4")

# API Server configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = _get_int("API_PORT", 8000, "API_PORT")

# RLM display limits (moved from diff_rlm.py magic numbers)
MAX_VISIBLE_FILES = 50
MAX_REVIEW_FILES = 100  # Higher limit for auto-review (uses patches only)
MAX_FILE_CONTENT_CHARS = 10000
MAX_PATCH_CHARS = 5000
MAX_RLM_OUTPUT_CHARS = 5000

# Default ignore patterns (always excluded)
DEFAULT_IGNORE_PATTERNS = [
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".svn",
    ".hg",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "*.bin",
    "*.o",
    "*.a",
    "*.class",
    "*.jar",
    "*.war",
    "*.ear",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.rar",
    "*.7z",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.svg",
    "*.woff",
    "*.woff2",
    "*.ttf",
    "*.eot",
    "*.mp3",
    "*.mp4",
    "*.avi",
    "*.mov",
    "*.pdf",
    "*.doc",
    "*.docx",
    "*.xls",
    "*.xlsx",
    "*.ppt",
    "*.pptx",
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "poetry.lock",
    "Cargo.lock",
    ".DS_Store",
    "Thumbs.db",
]

# Priority patterns for inclusion (checked first when building snapshot)
# These files are included first before hitting the MAX_TOTAL_BYTES limit
PRIORITY_PATTERNS = [
    # Documentation
    "README*",
    "readme*",
    # Package manifests
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    # Build files
    "Makefile",
    "Dockerfile",
    "docker-compose*.yml",
    ".env.example",
    # Source code at root level (important for small projects)
    "*.py",
    "*.ts",
    "*.js",
    "*.tsx",
    "*.jsx",
    "*.go",
    "*.rs",
    "*.java",
    "*.rb",
    "*.php",
    # Source directories
    "src/**",
    "lib/**",
    "app/**",
    "pkg/**",
    "cmd/**",
    # Test directories
    "tests/**",
    "test/**",
    "spec/**",
]
