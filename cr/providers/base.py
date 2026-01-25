"""Abstract base class for Git hosting providers."""

from abc import ABC, abstractmethod
from typing import ClassVar

from ..diff_types import PRInfo, FileContents


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
