"""Layout Tests"""

import ast
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


def test_module_docstrings_are_one_line() -> None:
    """Test that every module of the package and scripts has a one-line docstring."""
    long = [
        path.relative_to(ROOT).as_posix()
        for directory in ("financedatabase", "scripts")
        for path in (ROOT / directory).rglob("*.py")
        if "\n" in (ast.get_docstring(ast.parse(path.read_text("utf-8"))) or "")
    ]
    assert not long, f"Modules with a docstring of more than one line: {long}"


def test_scripts_folders_have_one_controller() -> None:
    """Test that each scripts folder runs its models through exactly one controller."""
    folders = [p for p in (ROOT / "scripts").iterdir() if (p / "__init__.py").exists()]
    missing = [p.name for p in folders if len(list(p.glob("*_controller.py"))) != 1]
    assert not missing, f"Scripts folders without exactly one controller: {missing}"


def test_entry_scripts_only_launch_a_controller() -> None:
    """Test that the entry points in scripts/ define nothing and call a controller."""
    for path in (ROOT / "scripts").glob("*.py"):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text("utf-8"))
        definitions = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        ]
        assert not definitions, f"{path.name} defines {definitions}"
        imports = [
            node.module
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module
        ]
        assert any(m.endswith("_controller") for m in imports), path.name
