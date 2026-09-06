# Architecture

## Boundary

The project deliberately separates the online download phase from the offline installation phase:

```text
installed IDE / `code`  ──discover──┐
Marketplace search ──select─────────┼─> plugin list (*.txt)
                                    └─> download archives
                         removable media
archives ──> VS Code CLI install / JetBrains plugins directory
```

The download phase owns Marketplace/API access and `requests`. The installation phase consumes only local `.vsix` or `.zip` files and the target application's local CLI or plugin directory.

## Components

- `plugin_migrate/cli.py` is the user-facing orchestration layer. It normalizes discovery, search selection, list writing, downloads, and offline installation.
- `plugin_migrate/vscode.py` contains VS Code discovery, Marketplace search, and archive behavior. Extension IDs use `publisher.name`.
- `plugin_migrate/jetbrains.py` contains JetBrains product filtering, plugin discovery, Marketplace resolution, and archive downloads. IDs may be numeric Marketplace IDs or `xmlId` values.
- `plugin_migrate/install.py` contains the offline-only installers; it must not make network requests.

JetBrains discovery filters products before scanning. The default allow-list is IntelliJ IDEA and PyCharm; adding a product must be an explicit `--products` choice. `all` is an intentional opt-in.

## Change Guidelines

Keep network calls out of installers. Make download operations retryable and report failures per plugin. Write lists as UTF-8, keep generated archives in ignored directories, and preserve the existing script entry points when changing the shared CLI. New platform support should provide discovery, search, download, and offline install adapters plus a short README section.
