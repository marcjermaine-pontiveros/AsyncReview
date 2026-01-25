"""Tests for FastAPI server."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from cr.server import app
from cr.diff_types import PRInfo, FileContents, AnswerBlock, DiffCitation


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health(self, client):
        """Test health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestLoadPREndpoint:
    """Tests for /api/github/load_pr endpoint."""

    def test_load_pr_success(self, client):
        """Test successful PR loading."""
        mock_pr_info = PRInfo(
            review_id="test123",
            owner="test",
            repo="repo",
            number=42,
            title="Test PR",
            body="Test body",
            base_sha="base",
            head_sha="head",
            files=[{"path": "file.py", "status": "modified"}],
        )
        
        with patch("cr.server.load_pr", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = mock_pr_info
            
            response = client.post(
                "/api/github/load_pr",
                json={"prUrl": "https://github.com/test/repo/pull/42"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["reviewId"] == "test123"
            assert data["title"] == "Test PR"
            assert data["repo"]["owner"] == "test"
            assert len(data["files"]) == 1

    def test_load_pr_invalid_url(self, client):
        """Test error on invalid PR URL."""
        with patch("cr.server.load_pr", new_callable=AsyncMock) as mock_load:
            mock_load.side_effect = ValueError("Invalid GitHub PR URL")
            
            response = client.post(
                "/api/github/load_pr",
                json={"prUrl": "invalid-url"},
            )
            
            assert response.status_code == 400


class TestGetFileEndpoint:
    """Tests for /api/github/file endpoint."""

    def test_get_file_success(self, client):
        """Test successful file fetch."""
        old_file = FileContents(name="file.py", contents="old", cache_key="old-key")
        new_file = FileContents(name="file.py", contents="new", cache_key="new-key")
        
        with patch("cr.server.get_file_contents", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (old_file, new_file)
            
            response = client.get("/api/github/file?reviewId=test123&path=file.py")
            
            assert response.status_code == 200
            data = response.json()
            assert data["oldFile"]["contents"] == "old"
            assert data["newFile"]["contents"] == "new"

    def test_get_file_added(self, client):
        """Test getting a newly added file."""
        new_file = FileContents(name="new.py", contents="new content")
        
        with patch("cr.server.get_file_contents", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (None, new_file)
            
            response = client.get("/api/github/file?reviewId=test123&path=new.py")
            
            assert response.status_code == 200
            data = response.json()
            assert data["oldFile"] is None
            assert data["newFile"]["contents"] == "new content"

    def test_get_file_not_found(self, client):
        """Test error when review not found."""
        with patch("cr.server.get_file_contents", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ValueError("Review not found")
            
            response = client.get("/api/github/file?reviewId=unknown&path=file.py")
            
            assert response.status_code == 404


class TestAskEndpoint:
    """Tests for /api/diff/ask endpoint."""

    def test_ask_success(self, client):
        """Test successful question."""
        mock_blocks = [AnswerBlock(type="markdown", content="Test answer")]
        mock_citations = [DiffCitation(path="file.py", side="additions", start_line=1, end_line=5)]
        
        with patch("cr.server.get_diff_qa_rlm") as mock_get_rlm:
            mock_rlm = MagicMock()
            mock_rlm.ask = AsyncMock(return_value=(mock_blocks, mock_citations))
            mock_get_rlm.return_value = mock_rlm
            
            response = client.post(
                "/api/diff/ask",
                json={
                    "reviewId": "test123",
                    "question": "What does this code do?",
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["answerBlocks"]) == 1
            assert data["answerBlocks"][0]["type"] == "markdown"
            assert len(data["citations"]) == 1


class TestReviewEndpoint:
    """Tests for /api/diff/review endpoint."""

    def test_review_success(self, client):
        """Test successful review."""
        from cr.diff_types import ReviewIssue
        
        mock_issues = [
            ReviewIssue(
                title="Potential null reference",
                severity="high",
                category="investigation",
                explanation_markdown="The code may throw a null reference exception.",
            )
        ]
        
        with patch("cr.server.get_auto_review_rlm") as mock_get_rlm:
            mock_rlm = MagicMock()
            mock_rlm.review = AsyncMock(return_value=(mock_issues, "Summary"))
            mock_get_rlm.return_value = mock_rlm
            
            response = client.post("/api/diff/review?reviewId=test123")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["issues"]) == 1
            assert data["issues"][0]["severity"] == "high"
            assert data["summary"] == "Summary"

