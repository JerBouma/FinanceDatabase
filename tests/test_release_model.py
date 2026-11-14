"""Release Model Tests"""

from pathlib import Path

import pytest

from scripts.release.release_model import (
    BRANCH,
    create_release_notes,
    get_file_versions,
    get_tag_commit,
)

ROOT = Path(__file__).resolve().parents[1]


def test_every_version_file_carries_the_same_version() -> None:
    """Test that the package, lock, server.json and bundle all carry one version."""
    versions = get_file_versions(ROOT)
    assert len(versions) >= 7
    assert len(set(versions.values())) == 1, versions


def test_release_branches_name_a_version() -> None:
    """Test that only feature/vX.Y.Z is a release branch."""
    assert BRANCH.fullmatch("feature/v2.5.2").group(1) == "2.5.2"
    for branch in ("feature/v2.5", "feature/mcp-setup-paths", "v2.5.2"):
        assert BRANCH.fullmatch(branch) is None


def test_release_notes_need_an_intro_and_a_package_section() -> None:
    """Test that the PR description is kept verbatim and checked for its two parts."""
    body = "A short intro.\r\n\r\n## Package\r\n- A change."
    assert create_release_notes(body) == "A short intro.\n\n## Package\n- A change.\n"
    with pytest.raises(ValueError, match="introduction"):
        create_release_notes("## Package\n- A change.")
    with pytest.raises(ValueError, match="Package"):
        create_release_notes("A short intro.\n\n## Data\n- A fix.")


def test_a_missing_tag_has_no_commit() -> None:
    """Test that a tag that doesn't exist gives no commit."""
    assert get_tag_commit(ROOT, "0.0.0") == ""
