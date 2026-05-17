from __future__ import annotations

import os
from pathlib import Path

from mdcheck.constants import DEFAULT_IGNORED_DIRS, MARKDOWN_SUFFIXES


def discover_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []

    for current_dir, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in DEFAULT_IGNORED_DIRS]
        current = Path(current_dir)
        for filename in filenames:
            path = current / filename
            if path.suffix.lower() in MARKDOWN_SUFFIXES:
                files.append(path.resolve())

    return sorted(files, key=lambda path: str(path))
