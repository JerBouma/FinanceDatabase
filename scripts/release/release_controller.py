"""Release Module"""

__docformat__ = "google"

import json
import os
import sys
from pathlib import Path

from scripts.release.release_model import (
    BRANCH,
    check_environment,
    create_release_notes,
    get_file_versions,
    get_tag_commit,
)

ROOT = Path(__file__).resolve().parents[2]


def write_outputs(**values: str) -> None:
    """
    Pass values to the next steps of the workflow.

    Args:
        **values (str): The outputs.
    """
    with open(
        os.environ.get("GITHUB_OUTPUT", os.devnull), "a", encoding="utf-8"
    ) as file:
        for key, value in values.items():
            file.write(f"{key}={value}\n")
            print(f"{key}={value}")


def run_release_check() -> None:
    """
    Check a release PR (feature/vX.Y.Z) and write its notes; other PRs are no release.
    """
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    pull_request = event["pull_request"]

    branch = BRANCH.fullmatch(pull_request["head"]["ref"])
    if not branch:
        print(f"::notice::{pull_request['head']['ref']} is not a release branch.")
        write_outputs(release="false")
        return

    version = branch.group(1)
    sha = (
        pull_request["merge_commit_sha"]
        if pull_request.get("merged")
        else os.environ["GITHUB_SHA"]
    )
    problems = [
        f"{name} has {found}"
        for name, found in get_file_versions(ROOT).items()
        if found != version
    ]

    tagged = get_tag_commit(ROOT, version)
    if tagged and tagged != sha:
        problems.append(
            f"the tag {version} already exists on {tagged[:7]}, not on {sha[:7]}"
        )

    if problem := check_environment():
        problems.append(problem)

    try:
        (ROOT / "release-notes.md").write_text(
            create_release_notes(pull_request.get("body") or ""), encoding="utf-8"
        )
    except ValueError as error:
        problems.append(str(error))

    if problems:
        for problem in problems:
            print(f"::error::{problem}")
        sys.exit(f"Release {version} is not ready: {len(problems)} problem(s).")

    print(f"{version} is ready to release from {sha}.")
    write_outputs(release="true", version=version, sha=sha)
