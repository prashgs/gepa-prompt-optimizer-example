"""Shared file tools for workers that need to read/write artifacts and SPA files."""

from __future__ import annotations

from strands import tool

from sdlc_agents import artifacts as art
from sdlc_agents.config import Settings


def make_file_tools(settings: Settings):
    """Return Strands tools bound to the current settings paths."""

    @tool
    def write_artifact_file(filename: str, content: str) -> str:
        """Write a Markdown artifact under the artifacts directory.

        Args:
            filename: Artifact file name, e.g. prd.md, design.md, test_report.md, review.md
            content: Full file contents
        """
        path = art.write_artifact(settings, filename, content)
        return f"Wrote artifact: {path}"

    @tool
    def read_artifact_file(filename: str) -> str:
        """Read an artifact file from the artifacts directory.

        Args:
            filename: Artifact file name, e.g. prd.md
        """
        content = art.read_artifact(settings, filename)
        if not content:
            return f"(empty or missing: {filename})"
        return content

    @tool
    def write_spa_file(filename: str, content: str) -> str:
        """Write a SPA source file under the output directory.

        Args:
            filename: File name such as index.html, styles.css, or app.js
            content: Full file contents
        """
        path = art.write_spa_file(settings, filename, content)
        return f"Wrote SPA file: {path}"

    @tool
    def read_spa_file(filename: str) -> str:
        """Read a SPA source file from the output directory.

        Args:
            filename: File name such as index.html, styles.css, or app.js
        """
        content = art.read_spa_file(settings, filename)
        if not content:
            return f"(empty or missing: {filename})"
        return content

    @tool
    def list_spa_files() -> str:
        """List files currently in the SPA output directory."""
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(p.name for p in settings.output_dir.iterdir() if p.is_file())
        return ", ".join(files) if files else "(no files yet)"

    return {
        "write_artifact_file": write_artifact_file,
        "read_artifact_file": read_artifact_file,
        "write_spa_file": write_spa_file,
        "read_spa_file": read_spa_file,
        "list_spa_files": list_spa_files,
    }
