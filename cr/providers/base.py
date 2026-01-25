"""Abstract base class for Git hosting providers."""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import ClassVar

import httpx

from ..diff_types import PRInfo, FileContents

# Constants for API requests
DEFAULT_TIMEOUT = 30.0
DEFAULT_PER_PAGE = 100
REVIEW_ID_LENGTH = 8
USER_AGENT = "cr-review-tool"

logger = logging.getLogger(__name__)


class MergeRequestProvider(ABC):
    """Abstract base for Git hosting providers (GitHub, GitLab, etc.).
    
    Each provider implements:
    - URL pattern matching (can_handle)
    - MR/PR loading (load_mr)
    - File content fetching (get_file_contents)
    - Caching (get_cached_mr)
    """
    
    # Provider identifier (e.g., "github", "gitlab")
    name: ClassVar[str] = "unknown"
    
    # In-memory cache for loaded MRs (shared per provider instance)
    _mr_cache: dict[str, PRInfo]
    
    def __init__(self) -> None:
        self._mr_cache = {}

    @staticmethod
    def _generate_review_id() -> str:
        """Generate a unique review ID."""
        return str(uuid.uuid4())[:REVIEW_ID_LENGTH]

    @staticmethod
    async def _fetch_json_list(
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        params: dict[str, int] | None = None,
    ) -> list[dict]:
        """Fetch a JSON list from an API endpoint.

        Returns empty list if status is not 200.

        Args:
            client: HTTP client to use
            url: API endpoint URL
            headers: Request headers
            params: Query parameters (defaults to per_page=DEFAULT_PER_PAGE)

        Returns:
            List of JSON objects, or empty list if request fails
        """
        params = params or {"per_page": DEFAULT_PER_PAGE}
        resp = await client.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        logger.warning(
            "API request failed: %s returned status %d", 
            url, 
            resp.status_code
        )
        return []
    
    @classmethod
    @abstractmethod
    def can_handle(cls, url: str) -> bool:
        """Return True if this provider can handle the given URL.
        
        Args:
            url: A merge/pull request URL
            
        Returns:
            True if this provider should handle this URL
        """
        pass
    
    @abstractmethod
    async def load_mr(self, url: str) -> PRInfo:
        """Load merge/pull request metadata from the provider.
        
        Args:
            url: The MR/PR URL
            
        Returns:
            PRInfo with metadata, files, commits, and comments
        """
        pass
    
    @abstractmethod
    async def get_file_contents(
        self, review_id: str, path: str
    ) -> tuple[FileContents | None, FileContents | None]:
        """Get old and new file contents for a file in an MR.
        
        Args:
            review_id: The review ID from load_mr
            path: File path within the repo
            
        Returns:
            Tuple of (old_file, new_file) - either can be None for added/deleted files
        """
        pass
    
    def get_cached_mr(self, review_id: str) -> PRInfo | None:
        """Get a cached MR by review ID.
        
        Args:
            review_id: The review ID from load_mr
            
        Returns:
            The cached PRInfo or None if not found
        """
        return self._mr_cache.get(review_id)
