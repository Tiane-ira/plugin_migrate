# Repository Guidelines

## Project Structure & Module Organization

This repository contains independent migration utilities:

- `plugin_migrate/` contains the unified CLI, platform discovery/search/download modules, and offline installer.
- `vscode/` and `jetbrains/` contain editable plugin lists and generated archive directories (`vsix-downloads/` and `plugin-downloads/`).
- `docs/ARCHITECTURE.md` describes the online/offline boundary and extension points.

Downloaded archives and IDE metadata are ignored by Git. Do not commit generated packages or local `.idea`/`.vscode` directories.

## Build, Test, and Development Commands

There is no automated test suite. Install dependencies and build a local binary with:

```bash
pip install requests
./build.ps1 -Version dev
```

Run commands from the repository root:

```bash
python -m plugin_migrate vscode discover
python -m plugin_migrate vscode download
python -m plugin_migrate jetbrains discover --products idea,pycharm
python -m plugin_migrate jetbrains download
```

The release workflow builds one-file binaries with PyInstaller; use `vYYYY.MM.DD` tags for releases.

On a target machine, use `python -m plugin_migrate vscode install vscode/vsix-downloads` or `python -m plugin_migrate jetbrains install jetbrains/plugin-downloads --target <IDE>/plugins`. Ensure `code` is on `PATH`, and close JetBrains IDEs before installation.

## Coding Style & Naming Conventions

Use Python 3, four-space indentation, descriptive `snake_case` names, and standard-library imports grouped before third-party imports such as `requests`. Keep platform-specific behavior explicit and preserve UTF-8 file handling. Shell scripts should remain POSIX-compatible where possible; batch scripts should use quoted paths and `@echo off`. Use clear, lowercase filenames with underscores for new Python modules.

## Testing Guidelines

No framework or coverage threshold is configured. Before submitting changes, run modified Python scripts against representative lists, including empty lists and one invalid/unavailable plugin ID, and verify generated archives are written to the expected ignored directory. For installer changes, perform a safe dry run or test with a disposable IDE/plugin directory when possible.

## Commit & Pull Request Guidelines

The history currently contains only `init`, so no project-specific commit format is established. Use concise imperative messages (for example, `Fix JetBrains plugin ID resolution`) and keep unrelated changes separate. Pull requests should explain the affected workflow, list manual verification commands and operating systems tested, identify any Marketplace/API assumptions, and include screenshots or terminal output when changing interactive installer behavior.
