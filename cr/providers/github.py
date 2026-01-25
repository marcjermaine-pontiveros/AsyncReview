"""GitHub provider for AsyncReview.

Supports GitHub.com and self-hosted GitHub Enterprise via GITHUB_API_BASE.
"""

import re
import uuid
from datetime import datetime

import httpx

from ..config import GITHUB_TOKEN, GITHUB_API_BASE
from ..diff_types import PRInfo, FileContents
from .base import MergeRequestProvider


class GitHubProvider(MergeRequestProvider):
    """GitHub provider for Pull Requests.
    
    Supports:
    - https://github.com/owner/repo/pull/123
    - https://github.enterprise.com/owner/repo/pull/456
    """
    
    name = "github"
    
    # Pattern matches github.com or any domain with /pull/ in the path
    _URL_PATTERN = re.compile(r"github[^/]*/([^/]+)/([^/]+)/pull/(\d+)")
    
    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Return True if URL looks like a GitHub PR URL."""
        # Match github.com or any domain containing 'github' with /pull/ path
        return bool(cls._URL_PATTERN.search(url))
    
    @classmethod
    def parse_pr_url(cls, url: str) -> tuple[str, str, int]:
        """Parse a GitHub PR URL into (owner, repo, number).
        
        Args:
            url: GitHub PR URL like https://github.com/owner/repo/pull/123
            
        Returns:
            Tuple of (owner, repo, pr_number)
            
        Raises:
            ValueError: If URL format is invalid
        """
        match = cls._URL_PATTERN.search(url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {url}")
        return match.group(1), match.group(2), int(match.group(3))
    
    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "cr-review-tool",
        }
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        return headers
    
    async def load_mr(self, url: str) -> PRInfo:
        """Load PR metadata from GitHub.
        
        Args:
            url: GitHub PR URL
            
        Returns:
            PRInfo with metadata and file list
        """
        owner, repo, number = self.parse_pr_url(url)
        review_id = str(uuid.uuid4())[:8]
        
        async with httpx.AsyncClient() as client:
            # Fetch PR metadata
            pr_resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}",
                headers=self._get_headers(),
                timeout=30.0,
            )
            pr_resp.raise_for_status()
            pr_data = pr_resp.json()
            
            # Fetch changed files
            files_resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}/files",
                headers=self._get_headers(),
                params={"per_page": 100},
                timeout=30.0,
            )
            files_resp.raise_for_status()
            files_data = files_resp.json()
        
            # Fetch commits
            commits_resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}/commits",
                headers=self._get_headers(),
                params={"per_page": 100},
                timeout=30.0,
            )
            commits_list = []
            if commits_resp.status_code == 200:
                commits_data = commits_resp.json()
                commits_list = [
                    {
                        "sha": c["sha"],
                        "message": c["commit"]["message"],
                        "author": {
                            "name": c["commit"]["author"]["name"],
                            "date": c["commit"]["author"]["date"],
                            "login": c["author"]["login"] if c.get("author") else None,
                            "avatar_url": c["author"]["avatar_url"] if c.get("author") else None,
                        },
                        "html_url": c["html_url"],
                    }
                    for c in commits_data
                ]

            # Fetch comments (using issue comments for main conversation)
            comments_resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{number}/comments",
                headers=self._get_headers(),
                params={"per_page": 100},
                timeout=30.0,
            )
            comments_list = []
            if comments_resp.status_code == 200:
                 comments_data = comments_resp.json()
                 comments_list = [
                     {
                         "id": c["id"],
                         "user": {
                             "login": c["user"]["login"],
                             "avatar_url": c["user"]["avatar_url"],
                         },
                         "body": c["body"],
                         "created_at": c["created_at"],
                         "html_url": c["html_url"],
                     }
                     for c in comments_data
                 ]

        files = [
            {
                 "path": f["filename"],
                 "status": f.get("status", "modified"),
                 "additions": f.get("additions", 0),
                 "deletions": f.get("deletions", 0),
                 "patch": f.get("patch"),
            }
            for f in files_data
        ]
        
        pr_info = PRInfo(
            review_id=review_id,
            owner=owner,
            repo=repo,
            number=number,
            title=pr_data.get("title", ""),
            body=pr_data.get("body") or "",
            base_sha=pr_data["base"]["sha"],
            head_sha=pr_data["head"]["sha"],
            files=files,
            created_at=datetime.now(),
            user={"login": pr_data["user"]["login"], "avatar_url": pr_data["user"]["avatar_url"]},
            state=pr_data.get("state", "open"),
            draft=pr_data.get("draft", False),
            head_ref=pr_data["head"]["ref"],
            base_ref=pr_data["base"]["ref"],
            commits=pr_data.get("commits", 0),
            additions=pr_data.get("additions", 0),
            deletions=pr_data.get("deletions", 0),
            changed_files=pr_data.get("changed_files", 0),
            commits_list=commits_list,
            comments=comments_list,
        )
        
        # Cache for later file fetching
        self._mr_cache[review_id] = pr_info
        
        return pr_info

    async def get_file_contents(
        self, review_id: str, path: str
    ) -> tuple[FileContents | None, FileContents | None]:
        """Get old and new file contents for a file in a PR.
        
        Args:
            review_id: The review ID from load_mr
            path: File path within the repo
            
        Returns:
            Tuple of (old_file, new_file) - either can be None for added/deleted files
        """
        pr_info = self._mr_cache.get(review_id)
        if not pr_info:
            raise ValueError(f"Review {review_id} not found")
        
        owner, repo = pr_info.owner, pr_info.repo
        base_sha, head_sha = pr_info.base_sha, pr_info.head_sha
        
        async with httpx.AsyncClient() as client:
            old_file = None
            new_file = None
            
            # Fetch base version
            try:
                base_resp = await client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                    headers={**self._get_headers(), "Accept": "application/vnd.github.v3.raw"},
                    params={"ref": base_sha},
                    timeout=30.0,
                )
                if base_resp.status_code == 200:
                    old_file = FileContents(
                        name=path,
                        contents=base_resp.text,
                        cache_key=f"{owner}/{repo}/{base_sha}/{path}",
                    )
            except httpx.HTTPStatusError:
                pass  # File doesn't exist in base (new file)
            
            # Fetch head version
            try:
                head_resp = await client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                    headers={**self._get_headers(), "Accept": "application/vnd.github.v3.raw"},
                    params={"ref": head_sha},
                    timeout=30.0,
                )
                if head_resp.status_code == 200:
                    new_file = FileContents(
                        name=path,
                        contents=head_resp.text,
                        cache_key=f"{owner}/{repo}/{head_sha}/{path}",
                    )
            except httpx.HTTPStatusError:
                pass  # File doesn't exist in head (deleted file)
        
        return old_file, new_file
