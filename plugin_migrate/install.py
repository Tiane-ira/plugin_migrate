from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path


def vscode(archive_dir: Path) -> None:
    for archive in sorted(archive_dir.glob("*.vsix")):
        subprocess.run(["code", "--install-extension", str(archive)], check=False)


def jetbrains(archive_dir: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for archive in sorted(archive_dir.glob("*.zip")):
        with zipfile.ZipFile(archive) as package:
            package.extractall(target)
        print(f"Installed {archive.name} -> {target}")
