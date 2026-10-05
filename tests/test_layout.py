"""Layout Tests"""

from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_folder_has_at_most_one_controller() -> None:
    """Test that no folder of the package or scripts has more than one controller."""
    folders = Counter(
        path.parent.relative_to(ROOT).as_posix()
        for directory in ("financedatabase", "scripts")
        for path in (ROOT / directory).rglob("*_controller.py")
    )
    crowded = {folder: count for folder, count in folders.items() if count > 1}
    assert not crowded, f"Folders with more than one controller: {crowded}"
