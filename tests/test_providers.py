"""Tests for provider abstraction and GitLab provider."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from cr.providers import get_provider_for_url
from cr.providers.github import GitHubProvider
from cr.providers.gitlab import GitLabProvider
from cr.providers.registry import get_provider_for_review, cache_provider, clear_provider_cache
from cr.diff_types import PRInfo


class TestProviderDetection:
    """Tests for provider URL detection."""

    def test_github_can_handle_github_com(self):
        """GitHub provider handles github.com URLs."""
        assert GitHubProvider.can_handle("https://github.com/owner/repo/pull/123")
        assert GitHubProvider.can_handle("https://github.com/org/project/pull/1")
    
    def test_github_can_handle_enterprise(self):
        """GitHub provider handles GitHub Enterprise URLs."""
        assert GitHubProvider.can_handle("https://github.example.com/owner/repo/pull/42")
        assert GitHubProvider.can_handle("https://github-enterprise.company.com/org/repo/pull/99")
    
    def test_github_rejects_gitlab(self):
        """GitHub provider rejects GitLab URLs."""
        assert not GitHubProvider.can_handle("https://gitlab.com/owner/repo/-/merge_requests/1")
    
    def test_gitlab_can_handle_gitlab_com(self):
        """GitLab provider handles gitlab.com URLs."""
        assert GitLabProvider.can_handle("https://gitlab.com/owner/repo/-/merge_requests/123")
        assert GitLabProvider.can_handle("https://gitlab.com/group/subgroup/project/-/merge_requests/1")
    
    def test_gitlab_can_handle_self_hosted(self):
        """GitLab provider handles self-hosted GitLab URLs."""
        assert GitLabProvider.can_handle("https://gitlab.example.com/org/project/-/merge_requests/42")
        assert GitLabProvider.can_handle("https://git.company.com/team/repo/-/merge_requests/99")
    
    def test_gitlab_rejects_github(self):
        """GitLab provider rejects GitHub URLs."""
        assert not GitLabProvider.can_handle("https://github.com/owner/repo/pull/1")
    
    def test_get_provider_for_url_github(self):
        """Registry returns GitHub provider for GitHub URLs."""
        provider = get_provider_for_url("https://github.com/test/repo/pull/42")
        assert isinstance(provider, GitHubProvider)
        assert provider.name == "github"
    
    def test_get_provider_for_url_gitlab(self):
        """Registry returns GitLab provider for GitLab URLs."""
        provider = get_provider_for_url("https://gitlab.com/test/repo/-/merge_requests/42")
        assert isinstance(provider, GitLabProvider)
        assert provider.name == "gitlab"
    
    def test_get_provider_for_url_unknown(self):
        """Registry raises error for unknown URLs."""
        with pytest.raises(ValueError, match="No provider found"):
            get_provider_for_url("https://bitbucket.org/owner/repo/pull-requests/1")


class TestGitHubProviderUrlParsing:
    """Tests for GitHub URL parsing."""
    
    def test_parse_standard_url(self):
        """Parse standard github.com URL."""
        owner, repo, number = GitHubProvider.parse_pr_url("https://github.com/AsyncFuncAI/deepwiki/pull/448")
        assert owner == "AsyncFuncAI"
        assert repo == "deepwiki"
        assert number == 448
    
    def test_parse_with_trailing(self):
        """Parse URL with trailing path."""
        owner, repo, number = GitHubProvider.parse_pr_url("https://github.com/owner/repo/pull/123/files")
        assert owner == "owner"
        assert repo == "repo"
        assert number == 123
    
    def test_parse_invalid_raises(self):
        """Invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
            GitHubProvider.parse_pr_url("https://gitlab.com/owner/repo/-/merge_requests/1")


class TestGitLabProviderUrlParsing:
    """Tests for GitLab URL parsing."""
    
    def test_parse_standard_url(self):
        """Parse standard gitlab.com URL."""
        host, project, iid = GitLabProvider.parse_mr_url("https://gitlab.com/owner/repo/-/merge_requests/123")
        assert host == "gitlab.com"
        assert project == "owner/repo"
        assert iid == 123
    
    def test_parse_nested_group(self):
        """Parse URL with nested groups."""
        host, project, iid = GitLabProvider.parse_mr_url("https://gitlab.com/group/subgroup/project/-/merge_requests/42")
        assert host == "gitlab.com"
        assert project == "group/subgroup/project"
        assert iid == 42
    
    def test_parse_self_hosted(self):
        """Parse self-hosted GitLab URL."""
        host, project, iid = GitLabProvider.parse_mr_url("https://gitlab.example.com/org/repo/-/merge_requests/99")
        assert host == "gitlab.example.com"
        assert project == "org/repo"
        assert iid == 99
    
    def test_parse_invalid_raises(self):
        """Invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitLab MR URL"):
            GitLabProvider.parse_mr_url("https://github.com/owner/repo/pull/1")


class TestGitLabProvider:
    """Tests for GitLab provider API calls."""

    @pytest.fixture
    def mock_mr_response(self):
        """Mock GitLab MR API response."""
        return {
            "iid": 123,
            "title": "Add feature",
            "description": "This MR adds a feature",
            "source_branch": "feature-branch",
            "target_branch": "main",
            "state": "opened",
            "draft": False,
            "author": {"username": "testuser", "avatar_url": "https://example.com/avatar"},
            "diff_refs": {
                "base_sha": "abc123base",
                "head_sha": "def456head",
                "start_sha": "start123",
            },
        }

    @pytest.fixture
    def mock_changes_response(self):
        """Mock GitLab MR changes API response."""
        return {
            "changes": [
                {
                    "new_path": "src/main.py",
                    "old_path": "src/main.py",
                    "new_file": False,
                    "deleted_file": False,
                    "renamed_file": False,
                    "diff": "@@ -1,5 +1,10 @@\n+new line",
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_load_mr_success(self, mock_mr_response, mock_changes_response):
        """Test successful MR loading."""
        provider = GitLabProvider()
        
        with patch("cr.providers.gitlab.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock MR response
            mr_resp = MagicMock()
            mr_resp.json.return_value = mock_mr_response
            mr_resp.raise_for_status = MagicMock()
            
            # Mock changes response
            changes_resp = MagicMock()
            changes_resp.json.return_value = mock_changes_response
            changes_resp.raise_for_status = MagicMock()
            
            # Mock commits response
            commits_resp = MagicMock()
            commits_resp.status_code = 200
            commits_resp.json.return_value = []
            
            # Mock notes response
            notes_resp = MagicMock()
            notes_resp.status_code = 200
            notes_resp.json.return_value = []
            
            mock_client.get = AsyncMock(side_effect=[mr_resp, changes_resp, commits_resp, notes_resp])
            
            pr_info = await provider.load_mr("https://gitlab.com/test/repo/-/merge_requests/123")
            
            assert pr_info.owner == "test"
            assert pr_info.repo == "repo"
            assert pr_info.number == 123
            assert pr_info.title == "Add feature"
            assert pr_info.base_sha == "abc123base"
            assert pr_info.head_sha == "def456head"
            assert len(pr_info.files) == 1
            
            # Check caching
            cached = provider.get_cached_mr(pr_info.review_id)
            assert cached is not None


class TestProviderCache:
    """Tests for provider caching."""
    
    def setup_method(self):
        """Clear cache before each test."""
        clear_provider_cache()
    
    def test_cache_and_retrieve(self):
        """Test caching and retrieving providers."""
        provider = GitHubProvider()
        cache_provider("test123", provider)
        
        retrieved = get_provider_for_review("test123")
        assert retrieved is provider
    
    def test_retrieve_missing(self):
        """Test retrieving non-existent provider."""
        result = get_provider_for_review("nonexistent")
        assert result is None
