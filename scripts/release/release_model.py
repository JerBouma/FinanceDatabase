"""Release Model"""

__docformat__ = "google"

import json
import os
import re
import subprocess
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

BRANCH = re.compile(r"feature/v(\d+\.\d+\.\d+)")
BUNDLE = Path("financedatabase") / "mcp_server" / "mcpb"
PIN = "financedatabase[mcp]=="


def get_file_versions(root: Path) -> dict[str, str]:
    """
    Get the version from every file that carries it.

    Args:
        root (Path): The repository root.

    Returns:
        dict[str, str]: The version per file (and place in it).
    """
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    server = json.loads((root / "server.json").read_text())
    bundle = tomllib.loads((root / BUNDLE / "pyproject.toml").read_text())["project"]
    lock = tomllib.loads((root / "uv.lock").read_text())

    versions = {
        "pyproject.toml": project["version"],
        "uv.lock": next(
            package["version"]
            for package in lock["package"]
            if package["name"] == "financedatabase"
        ),
        "server.json version": server["version"],
        "mcpb/manifest.json": json.loads((root / BUNDLE / "manifest.json").read_text())[
            "version"
        ],
        "mcpb/pyproject.toml version": bundle["version"],
        "mcpb/pyproject.toml financedatabase[mcp] pin": next(
            (dep[len(PIN) :] for dep in bundle["dependencies"] if dep.startswith(PIN)),
            "missing",
        ),
    }
    for index, package in enumerate(server["packages"]):
        versions[f"server.json packages[{index}]"] = package["version"]

    return versions


def get_tag_commit(root: Path, version: str) -> str:
    """
    Get the commit an existing tag points to.

    Args:
        root (Path): The repository root.
        version (str): The tag, e.g. "2.5.2".

    Returns:
        str: The commit, or an empty string when the tag doesn't exist.
    """
    command = ["git", "rev-parse", "-q", "--verify", f"refs/tags/{version}^{{commit}}"]
    return subprocess.run(  # noqa: S603
        command, capture_output=True, text=True, cwd=root, check=False
    ).stdout.strip()


def check_environment() -> str | None:
    """
    Check that the "release" environment waits for an approval. GitHub creates an
    environment a job names without protection, which would publish without one.

    Returns:
        str | None: The problem, or None when the environment is protected.
    """
    request = urllib.request.Request(
        f"{os.environ['GITHUB_API_URL']}/repos/{os.environ['GITHUB_REPOSITORY']}"
        "/environments/release",
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:  # noqa: S310
            environment = json.load(response)
    except urllib.error.HTTPError as error:
        return (
            f'the "release" environment could not be read (HTTP {error.code}); '
            "create it with a required reviewer"
        )

    if not any(
        rule["type"] == "required_reviewers"
        for rule in environment.get("protection_rules", [])
    ):
        return 'the "release" environment has no required reviewer'
    if environment.get("can_admins_bypass", True):
        return (
            'the "release" environment lets administrators skip the approval '
            '(turn off "Allow administrators to bypass")'
        )
    return None


def create_release_notes(body: str) -> str:
    """
    Create the release text from the PR description: an introduction, then "## Package".

    Args:
        body (str): The PR description.

    Returns:
        str: The release text.

    Raises:
        ValueError: When the introduction or the "## Package" section is missing.
    """
    body = body.replace("\r\n", "\n").strip()
    intro = body.split("\n## ", 1)[0].strip()
    if not intro or intro.startswith("## "):
        raise ValueError(
            "The PR description needs a short introduction before its first header."
        )
    if not re.search(r"(?m)^## Package\s*$", body):
        raise ValueError('The PR description needs a "## Package" section.')
    return body + "\n"
