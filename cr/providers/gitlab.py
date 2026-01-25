"""GitLab provider for AsyncReview.

Supports GitLab.com and self-hosted GitLab via GITLAB_API_BASE.
"""

import re
import uuid
from datetime import datetime
from urllib.parse import quote_plus

import httpx

from ..config import GITLAB_TOKEN, GITLAB_API_BASE
from ..diff_types import PRInfo, FileContents
from .base import MergeRequestProvider


class GitLabProvider(MergeRequestProvider):
    """GitLab provider for Merge Requests.
    
    Supports:
    - https://gitlab.com/owner/repo/-/merge_requests/123
    - https://gitlab.com/group/subgroup/project/-/merge_requests/456
    - https://gitlab.example.com/project/-/merge_requests/789
    """
    
    name = "gitlab"
    
    # Pattern matches any domain with /-/merge_requests/ in the path
    # Captures the project path (can include groups/subgroups) and MR IID
    _URL_PATTERN = re.compile(r"([^/]+\.[^/]+)/(.+?)/-/merge_requests/(\d+)")
    
    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Return True if URL looks like a GitLab MR URL."""
        return "/-/merge_requests/" in url
    
    @classmethod
    def parse_mr_url(cls, url: str) -> tuple[str, str, int]:
        """Parse a GitLab MR URL into (host, project_path, iid).
        
        Args:
            url: GitLab MR URL like https://gitlab.com/owner/repo/-/merge_requests/123
            
        Returns:
            Tuple of (host, project_path, mr_iid)
            
        Raises:
            ValueError: If URL format is invalid
        """
        match = cls._URL_PATTERN.search(url)
        if not match:
            raise ValueError(f"Invalid GitLab MR URL: {url}")
        return match.group(1), match.group(2), int(match.group(3))
    
    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for GitLab API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "cr-review-tool",
        }
        if GITLAB_TOKEN:
            headers["PRIVATE-TOKEN"] = GITLAB_TOKEN
        return headers
    
    def _get_api_base(self, host: str) -> str:
        """Get the API base URL for a given host.
        
        If the host matches the configured GITLAB_API_BASE, use that.
        Otherwise, construct the API URL from the host.
        """
        # Check if host matches configured base
        if GITLAB_API_BASE and host in GITLAB_API_BASE:
            return GITLAB_API_BASE
        # Default: construct API URL from host
        return f"https://{host}/api/v4"
    
    async def load_mr(self, url: str) -> PRInfo:
        """Load MR metadata from GitLab.
        
        Args:
            url: GitLab MR URL
            
        Returns:
            PRInfo with metadata and file list
        """
        host, project_path, iid = self.parse_mr_url(url)
        review_id = str(uuid.uuid4())[:8]
        api_base = self._get_api_base(host)
        
        # URL-encode the project path for API calls
        encoded_project = quote_plus(project_path)
        
        async with httpx.AsyncClient() as client:
            # Fetch MR metadata
            mr_resp = await client.get(
                f"{api_base}/projects/{encoded_project}/merge_requests/{iid}",
                headers=self._get_headers(),
                timeout=30.0,
            )
            mr_resp.raise_for_status()
            mr_data = mr_resp.json()
            
            # Fetch changed files (includes diffs)
            changes_resp = await client.get(
                f"{api_base}/projects/{encoded_project}/merge_requests/{iid}/changes",
                headers=self._get_headers(),
                timeout=30.0,
            )
            changes_resp.raise_for_status()
            changes_data = changes_resp.json()
            
            # Fetch commits
            commits_resp = await client.get(
                f"{api_base}/projects/{encoded_project}/merge_requests/{iid}/commits",
                headers=self._get_headers(),
                params={"per_page": 100},
                timeout=30.0,
            )
            commits_list = []
            if commits_resp.status_code == 200:
                commits_data = commits_resp.json()
                commits_list = [
                    {
                        "sha": c["id"],
                        "message": c["message"],
                        "author": {
                            "name": c["author_name"],
                            "date": c["created_at"],
                            "login": c.get("author_email"),
                            "avatar_url": None,
                        },
                        "html_url": c["web_url"],
                    }
                    for c in commits_data
                ]
            
            # Fetch comments (notes)
            notes_resp = await client.get(
                f"{api_base}/projects/{encoded_project}/merge_requests/{iid}/notes",
                headers=self._get_headers(),
                params={"per_page": 100},
                timeout=30.0,
            )
            comments_list = []
            if notes_resp.status_code == 200:
                notes_data = notes_resp.json()
                comments_list = [
                    {
                        "id": n["id"],
                        "user": {
                            "login": n["author"]["username"],
                            "avatar_url": n["author"].get("avatar_url"),
                        },
                        "body": n["body"],
                        "created_at": n["created_at"],
                        "html_url": f"{url}#note_{n['id']}",
                    }
                    for n in notes_data
                    if not n.get("system", False)  # Exclude system notes
                ]
        
        # Parse files from changes response
        files = []
        for change in changes_data.get("changes", []):
            # Determine status
            if change.get("new_file"):
                status = "added"
            elif change.get("deleted_file"):
                status = "removed"
            elif change.get("renamed_file"):
                status = "renamed"
            else:
                status = "modified"
            
            # Count additions/deletions from diff
            diff = change.get("diff", "")
            additions = diff.count("\n+") - diff.count("\n+++")
            deletions = diff.count("\n-") - diff.count("\n---")
            
            files.append({
                "path": change.get("new_path") or change.get("old_path"),
                "status": status,
                "additions": max(0, additions),
                "deletions": max(0, deletions),
                "patch": diff,
            })
        
        # Extract owner/repo from project path
        path_parts = project_path.split("/")
        if len(path_parts) >= 2:
            owner = "/".join(path_parts[:-1])  # Group/subgroup path
            repo = path_parts[-1]
        else:
            owner = ""
            repo = project_path
        
        pr_info = PRInfo(
            review_id=review_id,
            owner=owner,
            repo=repo,
            number=iid,
            title=mr_data.get("title", ""),
            body=mr_data.get("description") or "",
            base_sha=mr_data["diff_refs"]["base_sha"],
            head_sha=mr_data["diff_refs"]["head_sha"],
            files=files,
            created_at=datetime.now(),
            user={
                "login": mr_data["author"]["username"],
                "avatar_url": mr_data["author"].get("avatar_url"),
            },
            state=mr_data.get("state", "opened"),
            draft=mr_data.get("draft", False) or mr_data.get("work_in_progress", False),
            head_ref=mr_data.get("source_branch", ""),
            base_ref=mr_data.get("target_branch", ""),
            commits=len(commits_list),
            additions=sum(f.get("additions", 0) for f in files),
            deletions=sum(f.get("deletions", 0) for f in files),
            changed_files=len(files),
            commits_list=commits_list,
            comments=comments_list,
        )
        
        # Store additional GitLab-specific data for file fetching
        pr_info._gitlab_host = host  # type: ignore
        pr_info._gitlab_project = project_path  # type: ignore
        
        # Cache for later file fetching
        self._mr_cache[review_id] = pr_info
        
        return pr_info

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
        pr_info = self._mr_cache.get(review_id)
        if not pr_info:
            raise ValueError(f"Review {review_id} not found")
        
        # Get GitLab-specific data
        host = getattr(pr_info, "_gitlab_host", "gitlab.com")
        project_path = getattr(pr_info, "_gitlab_project", f"{pr_info.owner}/{pr_info.repo}")
        api_base = self._get_api_base(host)
        encoded_project = quote_plus(project_path)
        encoded_path = quote_plus(path)
        
        base_sha, head_sha = pr_info.base_sha, pr_info.head_sha
        
        async with httpx.AsyncClient() as client:
            old_file = None
            new_file = None
            
            # Fetch base version
            try:
                base_resp = await client.get(
                    f"{api_base}/projects/{encoded_project}/repository/files/{encoded_path}/raw",
                    headers=self._get_headers(),
                    params={"ref": base_sha},
                    timeout=30.0,
                )
                if base_resp.status_code == 200:
                    old_file = FileContents(
                        name=path,
                        contents=base_resp.text,
                        cache_key=f"{project_path}/{base_sha}/{path}",
                    )
            except httpx.HTTPStatusError:
                pass  # File doesn't exist in base (new file)
            
            # Fetch head version
            try:
                head_resp = await client.get(
                    f"{api_base}/projects/{encoded_project}/repository/files/{encoded_path}/raw",
                    headers=self._get_headers(),
                    params={"ref": head_sha},
                    timeout=30.0,
                )
                if head_resp.status_code == 200:
                    new_file = FileContents(
                        name=path,
                        contents=head_resp.text,
                        cache_key=f"{project_path}/{head_sha}/{path}",
                    )
            except httpx.HTTPStatusError:
                pass  # File doesn't exist in head (deleted file)
        
        return old_file, new_file
