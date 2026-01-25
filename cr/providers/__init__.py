"""Git hosting providers for AsyncReview.

Supports GitHub (cloud + Enterprise) and GitLab (cloud + self-hosted).
"""

from .base import MergeRequestProvider
from .registry import get_provider_for_url, PROVIDERS

__all__ = ["MergeRequestProvider", "get_provider_for_url", "PROVIDERS"]
