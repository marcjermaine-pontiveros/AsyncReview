"""Provider registry for automatic provider detection."""

from .base import MergeRequestProvider
from .github import GitHubProvider
from .gitlab import GitLabProvider


# Ordered list of providers - first match wins
PROVIDERS: list[type[MergeRequestProvider]] = [
    GitLabProvider,  # Check GitLab first (more specific URL pattern)
    GitHubProvider,
]

# Cache provider instances by review_id for file fetching
_provider_cache: dict[str, MergeRequestProvider] = {}


def get_provider_for_url(url: str) -> MergeRequestProvider:
    """Return the appropriate provider for a given URL.
    
    Args:
        url: A merge/pull request URL
        
    Returns:
        An instance of the appropriate provider
        
    Raises:
        ValueError: If no provider can handle the URL
    """
    for provider_cls in PROVIDERS:
        if provider_cls.can_handle(url):
            return provider_cls()
    raise ValueError(f"No provider found for URL: {url}")


def get_provider_for_review(review_id: str) -> MergeRequestProvider | None:
    """Get the provider instance for a cached review.
    
    Args:
        review_id: The review ID from load_mr
        
    Returns:
        The provider instance or None if not found
    """
    return _provider_cache.get(review_id)


def cache_provider(review_id: str, provider: MergeRequestProvider) -> None:
    """Cache a provider instance by review ID.
    
    Args:
        review_id: The review ID from load_mr
        provider: The provider instance to cache
    """
    _provider_cache[review_id] = provider


def clear_provider_cache() -> None:
    """Clear the provider cache (for testing)."""
    _provider_cache.clear()
