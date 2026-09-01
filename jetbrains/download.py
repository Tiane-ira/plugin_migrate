"""
JetBrains 插件批量下载工具

从 JetBrains Marketplace 批量下载插件 zip 文件。
读取 jetbrains-plugins.txt 中的插件列表，逐个下载。
支持数字 ID（推荐）和 xmlId 两种格式。
"""

import requests
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_FILE = os.path.join(SCRIPT_DIR, "jetbrains-plugins.txt")
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "plugin-downloads")
API_BASE = "https://plugins.jetbrains.com/api"


def read_plugin_list():
    """读取插件列表，跳过注释和空行"""
    with open(PLUGINS_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    return lines


def resolve_xmlid_to_id(xml_id):
    """通过 Marketplace API 将 xmlId 解析为数字 ID

    使用 GET /api/plugins?xmlId={xmlId}&family=INTELLIJ 端点。
    """
    try:
        resp = requests.get(
            f"{API_BASE}/plugins",
            params={"xmlId": xml_id, "family": "INTELLIJ"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "id" in data:
            return data["id"]
    except Exception as e:
        print(f"  [警告] 解析 xmlId '{xml_id}' 失败: {e}")
    return None


def download_plugin(plugin_id_str):
    """下载单个插件，返回 (成功与否, 插件名称, 错误信息)"""
    # 判断是数字 ID 还是 xmlId
    if plugin_id_str.isdigit():
        numeric_id = int(plugin_id_str)
        display_name = plugin_id_str
    else:
        # xmlId 格式，需要先解析为数字 ID
        print(f"  解析 xmlId: {plugin_id_str} ...")
        numeric_id = resolve_xmlid_to_id(plugin_id_str)
        display_name = plugin_id_str
        if numeric_id is None:
            return False, display_name, "无法解析 xmlId，请改用数字 ID"
        # 获取插件名称用于显示
        try:
            info = requests.get(f"{API_BASE}/plugins/{numeric_id}", timeout=10).json()
            display_name = info.get("name", plugin_id_str)
        except Exception:
            pass

    # 获取最新版本信息
    try:
        updates_url = f"{API_BASE}/plugins/{numeric_id}/updates"
        resp = requests.get(updates_url, params={"channel": "", "size": 1}, timeout=15)
        resp.raise_for_status()
        updates = resp.json()
        if not updates:
            return False, display_name, "未找到可用版本"
        latest = updates[0]
        version = latest.get("version", "unknown")
        file_path_rel = latest.get("file", "")
    except Exception as e:
        return False, display_name, f"获取版本信息失败: {e}"

    # 下载插件 zip 文件
    # 优先使用 file 字段构建下载 URL，回退到 updateId 方式
    if file_path_rel:
        download_url = f"https://plugins.jetbrains.com/files/{file_path_rel}"
    else:
        download_url = f"https://plugins.jetbrains.com/plugin/download?rel=true&updateId={latest['id']}"
    safe_name = "".join(c if c.isalnum() or c in ".-_ " else "_" for c in display_name)
    file_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}_{version}.zip")

    print(f"  下载: {display_name} v{version} ...")
    try:
        resp = requests.get(download_url, timeout=120, allow_redirects=True)
        resp.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(resp.content)
        size_mb = len(resp.content) / (1024 * 1024)
        print(f"  已保存: {os.path.basename(file_path)} ({size_mb:.1f} MB)")
        return True, display_name, None
    except Exception as e:
        return False, display_name, str(e)


def main():
    if not os.path.exists(PLUGINS_FILE):
        print(f"错误：找不到插件列表文件 {PLUGINS_FILE}")
        print("请先创建该文件，每行一个插件 ID")
        sys.exit(1)

    plugins = read_plugin_list()
    if not plugins:
        print("插件列表为空，请在 jetbrains-plugins.txt 中添加插件 ID")
        sys.exit(0)

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    print(f"共 {len(plugins)} 个插件待下载\n")

    success = 0
    failed = []

    for i, plugin_id in enumerate(plugins, 1):
        print(f"[{i}/{len(plugins)}] 处理插件: {plugin_id}")
        ok, name, error = download_plugin(plugin_id)
        if ok:
            success += 1
        else:
            failed.append((plugin_id, error))
            print(f"  ✗ 失败: {error}")

        # 请求间隔，避免触发速率限制
        if i < len(plugins):
            time.sleep(1)

    # 汇总结果
    print(f"\n{'=' * 50}")
    print(f"下载完成！成功: {success}, 失败: {len(failed)}")
    if failed:
        print("\n失败的插件：")
        for pid, err in failed:
            print(f"  - {pid}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
