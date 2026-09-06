from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, jetbrains, vscode

ROOT = Path(__file__).resolve().parent.parent


def write_list(path: Path, values: list[str]) -> None:
    path.write_text("\n".join(sorted(set(values))) + "\n", encoding="utf-8")
    print(f"Wrote {len(set(values))} plugins to {path}")


def choose(items: list[dict[str, str]]) -> list[str]:
    for number, item in enumerate(items, 1):
        print(f"{number:>3}. {item['name']} ({item['id']})")
    if not items:
        return []
    answer = input("Select numbers (comma-separated) or all: ").strip().lower()
    if answer == "all":
        return [x["id"] for x in items]
    return [items[int(x) - 1]["id"] for x in answer.split(",")
            if x.strip().isdigit() and 1 <= int(x) <= len(items)]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="plugin-migrate", description="离线插件迁移工具")
    root.add_argument("--version", action="version", version=__version__)
    platforms = root.add_subparsers(dest="platform", required=True)
    for name in ("vscode", "jetbrains"):
        platform_parser = platforms.add_parser(name)
        actions = platform_parser.add_subparsers(dest="action", required=True)
        discover = actions.add_parser("discover", help="discover installed plugins")
        search = actions.add_parser("search", help="search Marketplace and select plugins")
        search.add_argument("query")
        search.add_argument("--limit", type=int, default=20)
        download = actions.add_parser("download", help="download a list on an online machine")
        download.add_argument("--file", type=Path)
        download.add_argument("--plugin", action="append", default=[])
        download.add_argument("--output", type=Path)
        for command in (discover, search):
            command.add_argument("--products", default="idea,pycharm")
            command.add_argument("--output", type=Path)
        download.add_argument("--products", default="idea,pycharm")
        install = actions.add_parser("install", help="install local archives on an offline machine")
        install.add_argument("archive_dir", type=Path)
        install.add_argument("--target", type=Path, help="JetBrains plugins directory")
    return root


def interactive() -> list[str]:
    print("\nPlugin Migrate - 插件迁移工具")
    platform = input("平台 [1] VS Code  [2] JetBrains: ").strip()
    platform = "vscode" if platform == "1" else "jetbrains"
    action = input("操作 [1] 自动发现  [2] 搜索选择  [3] 下载  [4] 离线安装: ").strip()
    action = {"1": "discover", "2": "search", "3": "download", "4": "install"}.get(action, "")
    if not action:
        raise SystemExit("无效操作")
    command = [platform, action]
    if action == "search":
        command.append(input("插件名称: ").strip())
        output = input("保存列表路径（直接回车不保存）: ").strip()
        if output:
            command += ["--output", output]
    elif action in ("discover", "download") and platform == "jetbrains":
        products = input("JetBrains 产品（默认 idea,pycharm，all 表示全部）: ").strip()
        command += ["--products", products or "idea,pycharm"]
    if action == "install":
        command.append(input("归档目录: ").strip())
        if platform == "jetbrains":
            command += ["--target", input("目标 IDE plugins 目录: ").strip()]
    return command


def read_ids(path: Path) -> list[str]:
    return [x.strip() for x in path.read_text(encoding="utf-8").splitlines()
            if x.strip() and not x.lstrip().startswith("#")]


def main() -> int:
    if len(sys.argv) == 1:
        sys.argv[1:] = interactive()
    args = parser().parse_args()
    base = ROOT / args.platform
    if args.platform == "vscode":
        if args.action == "discover":
            write_list(args.output or base / "vscode-extensions.txt", vscode.installed())
        elif args.action == "search":
            values = choose(vscode.search(args.query, args.limit))
            if args.output and values:
                write_list(args.output, values)
        elif args.action == "download":
            ids = args.plugin or read_ids(args.file or base / "vscode-extensions.txt")
            vscode.download(ids, args.output or base / "vsix-downloads")
        else:
            from .install import vscode as install_vscode
            install_vscode(args.archive_dir)
    else:
        if args.action == "discover":
            write_list(args.output or base / "jetbrains-plugins.txt", jetbrains.installed(args.products))
        elif args.action == "search":
            values = choose(jetbrains.search(args.query, args.limit))
            if args.output and values:
                write_list(args.output, values)
        elif args.action == "download":
            ids = args.plugin or read_ids(args.file or base / "jetbrains-plugins.txt")
            jetbrains.download(ids, args.output or base / "plugin-downloads")
        else:
            if not args.target:
                raise SystemExit("JetBrains install requires --target <IDE plugins directory>")
            from .install import jetbrains as install_jetbrains
            install_jetbrains(args.archive_dir, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
