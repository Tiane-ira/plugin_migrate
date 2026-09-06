from __future__ import annotations

import subprocess
from pathlib import Path

import requests


def installed() -> list[str]:
    result = subprocess.run(["code", "--list-extensions"], check=True, text=True,
                            capture_output=True)
    return [x.strip() for x in result.stdout.splitlines() if x.strip()]


def search(query: str, limit: int = 20) -> list[dict[str, str]]:
    payload = {"filters": [{"criteria": [{"filterType": 10, "value": query}]}],
               "flags": 914, "pageSize": limit}
    response = requests.post(
        "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery",
        json=payload, headers={"Accept": "application/json;api-version=7.2-preview.1"},
        timeout=30)
    response.raise_for_status()
    extensions = response.json().get("results", [{}])[0].get("extensions", [])
    return [{"id": x["extensionId"], "name": x["displayName"]} for x in extensions]


def download(ids: list[str], destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    failed = []
    for extension_id in ids:
        try:
            publisher, name = extension_id.split(".", 1)
            url = ("https://marketplace.visualstudio.com/_apis/public/gallery/"
                   f"publishers/{publisher}/vsextensions/{name}/latest/vspackage")
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            (destination / f"{extension_id}.vsix").write_bytes(response.content)
            print(f"Downloaded {extension_id}")
        except (ValueError, requests.RequestException) as exc:
            print(f"Failed {extension_id}: {exc}")
            failed.append(extension_id)
    return failed
