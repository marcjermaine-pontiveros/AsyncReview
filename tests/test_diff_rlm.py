"""Tests for Diff RLM module."""

import pytest
from cr.diff_rlm import (
    _build_diff_context_text,
    _parse_citations,
    _parse_answer_blocks,
)
from cr.diff_types import (
    DiffFileContext,
    FileContents,
    DiffCitation,
    AnswerBlock,
)


class TestBuildDiffContextText:
    """Tests for _build_diff_context_text function."""

    def test_modified_file(self):
        """Test context for a modified file with old and new versions."""
        files = [
            DiffFileContext(
                path="src/main.py",
                old_file=FileContents(name="main.py", contents="old code"),
                new_file=FileContents(name="main.py", contents="new code"),
                status="modified",
                additions=5,
                deletions=2,
            )
        ]
        
        text = _build_diff_context_text(files)
        
        assert "src/main.py" in text
        assert "modified" in text
        assert "+5" in text
        assert "-2" in text
        assert "old code" in text
        assert "new code" in text

    def test_added_file(self):
        """Test context for a newly added file."""
        files = [
            DiffFileContext(
                path="src/new.py",
                old_file=None,
                new_file=FileContents(name="new.py", contents="new file content"),
                status="added",
                additions=10,
                deletions=0,
            )
        ]
        
        text = _build_diff_context_text(files)
        
        assert "new.py" in text
        assert "Added File" in text
        assert "new file content" in text

    def test_deleted_file(self):
        """Test context for a deleted file."""
        files = [
            DiffFileContext(
                path="src/old.py",
                old_file=FileContents(name="old.py", contents="deleted file content"),
                new_file=None,
                status="removed",
                additions=0,
                deletions=15,
            )
        ]
        
        text = _build_diff_context_text(files)
        
        assert "old.py" in text
        assert "Deleted File" in text
        assert "deleted file content" in text

    def test_patch_only(self):
        """Test context when only patch is available."""
        files = [
            DiffFileContext(
                path="src/patched.py",
                patch="@@ -1,5 +1,10 @@\n-old line\n+new line",
                status="modified",
                additions=5,
                deletions=0,
            )
        ]
        
        text = _build_diff_context_text(files)
        
        assert "patched.py" in text
        assert "Patch:" in text
        assert "-old line" in text
        assert "+new line" in text


class TestParseCitations:
    """Tests for _parse_citations function."""

    def test_parse_string_simple(self):
        """Test parsing simple path:line citations."""
        raw = "src/main.py:10, src/utils.py:25"
        citations = _parse_citations(raw)
        
        assert len(citations) == 2
        assert citations[0].path == "src/main.py"
        assert citations[0].start_line == 10
        assert citations[0].end_line == 10

    def test_parse_string_range(self):
        """Test parsing path:start-end citations."""
        raw = "src/main.py:10-20"
        citations = _parse_citations(raw)
        
        assert len(citations) == 1
        assert citations[0].start_line == 10
        assert citations[0].end_line == 20

    def test_parse_dict_list(self):
        """Test parsing list of dict citations."""
        raw = [
            {"path": "src/main.py", "side": "additions", "startLine": 5, "endLine": 10, "reason": "bug here"},
        ]
        citations = _parse_citations(raw)
        
        assert len(citations) == 1
        assert citations[0].path == "src/main.py"
        assert citations[0].side == "additions"
        assert citations[0].start_line == 5
        assert citations[0].end_line == 10
        assert citations[0].reason == "bug here"


class TestParseAnswerBlocks:
    """Tests for _parse_answer_blocks function."""

    def test_markdown_only(self):
        """Test parsing pure markdown content."""
        answer = "This is a **markdown** response."
        blocks = _parse_answer_blocks(answer)
        
        assert len(blocks) == 1
        assert blocks[0].type == "markdown"
        assert "markdown" in blocks[0].content

    def test_code_block(self):
        """Test parsing content with code block."""
        answer = """Here is the fix:

```python
def fixed_function():
    return True
```

That should work."""
        blocks = _parse_answer_blocks(answer)
        
        assert len(blocks) == 3
        assert blocks[0].type == "markdown"
        assert blocks[1].type == "code"
        assert blocks[1].language == "python"
        assert "def fixed_function" in blocks[1].content
        assert blocks[2].type == "markdown"

