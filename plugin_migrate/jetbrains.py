from __future__ import annotations

import os
import platform
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

PRODUCTS = {"idea": "IntelliJ IDEA", "pycharm": "PyCharm", "webstorm": "WebStorm",
            "goland": "GoLand", "clion": "CLion", "rider": "Rider", "phpstorm": "PhpStorm",
            "rubymine": "RubyMine", "datagrip": "DataGrip", "dataspell": "DataSpell",
            "rustrover": "RustRover", "writerside": "Writerside", "aqua": "Aqua"}
PRODUCT_PREFIXES = {"idea": "IntelliJIdea", **{key: value for key, value in PRODUCTS.items() if key != "idea"}}
BUNDLED_PREFIXES = ("com.intellij.", "org.jetbrains.", "Docker", "com.android.tools")


def _bases() -> list[Path]:
    system = platform.system()
    if system == "Windows":
        return [Path(x) / "JetBrains" for x in
                (os.getenv("APPDATA", ""), os.getenv("LOCALAPPDATA", "")) if x]
    if system == "Darwin":
        return [Path.home() / "Library/Application Support/JetBrains"]
    return [Path.home() / ".config/JetBrains", Path.home() / ".local/share/JetBrains"]


def _plugin_info(path: Path) -> dict[str, str] | None:
    jars = list((path / "lib").glob("*.jar")) + list(path.glob("*.jar"))
    xml = path / "META-INF/plugin.xml"
    try:
        if xml.exists():
            content = xml.read_bytes()
        else:
            jar = next((x for x in jars if "searchableOptions" not in x.name), None)
            if not jar:
                return None
            with zipfile.ZipFile(jar) as archive:
                content = archive.read("META-INF/plugin.xml")
        root = ET.fromstring(content.lstrip(b"\xef\xbb\xbf"))
        return {"id": (root.findtext("id") or root.findtext("name") or path.name).strip(),
                "name": (root.findtext("name") or path.name).strip()}
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile):
        return None


def installed(products: str = "idea,pycharm") -> list[str]:
    wanted = None if products.lower() == "all" else {PRODUCTS.get(x.strip().lower(), x.strip())
                                                       for x in products.split(",")}
    values = set()
    for base in _bases():
        if not base.is_dir():
            continue
        for ide in base.iterdir():
            if not ide.is_dir() or not any(ide.name.startswith(key) for key in PRODUCT_PREFIXES.values()):
                continue
            product = next((PRODUCTS[key] for key, prefix in PRODUCT_PREFIXES.items()
                            if ide.name.startswith(prefix)), "")
            if wanted is not None and product not in wanted:
                continue
            plugins = ide / "plugins"
            for entry in plugins.iterdir() if plugins.is_dir() else []:
                info = _plugin_info(entry)
                if info and not any(info["id"].startswith(prefix) for prefix in BUNDLED_PREFIXES):
                    values.add(info["id"])
    return sorted(values)


def search(query: str, limit: int = 20) -> list[dict[str, str]]:
    response = requests.get("https://plugins.jetbrains.com/api/searchPlugins",
                            params={"search": query, "max": limit}, timeout=30)
    response.raise_for_status()
    data = response.json()
    items = data if isinstance(data, list) else data.get("plugins", data.get("data", []))
    return [{"id": str(x.get("id", x.get("xmlId", ""))),
             "name": x.get("name", x.get("pluginName", ""))} for x in items
            if x.get("id") or x.get("xmlId")]


def download(ids: list[str], destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    failed = []
    for plugin_id in ids:
        try:
            if not plugin_id.isdigit():
                result = requests.get("https://plugins.jetbrains.com/api/plugins",
                                      params={"xmlId": plugin_id, "family": "INTELLIJ"}, timeout=30)
                result.raise_for_status()
                plugin_id = str(result.json()["id"])
            updates = requests.get(f"https://plugins.jetbrains.com/api/plugins/{plugin_id}/updates",
                                   params={"channel": "", "size": 1}, timeout=30)
            updates.raise_for_status()
            latest = updates.json()[0]
            url = (f"https://plugins.jetbrains.com/files/{latest['file']}" if latest.get("file")
                   else f"https://plugins.jetbrains.com/plugin/download?rel=true&updateId={latest['id']}")
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            (destination / f"{plugin_id}_{latest.get('version', 'latest')}.zip").write_bytes(response.content)
            print(f"Downloaded {plugin_id}")
        except (KeyError, IndexError, requests.RequestException, ValueError) as exc:
            print(f"Failed {plugin_id}: {exc}")
            failed.append(plugin_id)
    return failed
