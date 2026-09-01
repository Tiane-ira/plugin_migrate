"""
JetBrains 插件列表导出工具

扫描本地 JetBrains IDE 的已安装插件目录，提取插件 xmlId，
输出到 jetbrains-plugins.txt 文件，供迁移使用。

支持 Windows / macOS / Linux，支持主流 JetBrains IDE。
"""

import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import platform

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "jetbrains-plugins.txt")

# JetBrains IDE 配置: 键 = 配置目录名模式, 值 = 显示名称
# 新版 (>2020.x) 使用 {Name}{Version} 格式，如 PyCharm2026.2
# 旧版使用 {Name}{Major}.{Minor} 格式，如 PyCharm2019.3
IDE_CONFIGS = {
    "PyCharm": "PyCharm",
    "IntelliJIdea": "IntelliJ IDEA",
    "WebStorm": "WebStorm",
    "GoLand": "GoLand",
    "CLion": "CLion",
    "Rider": "Rider",
    "PhpStorm": "PhpStorm",
    "RubyMine": "RubyMine",
    "DataGrip": "DataGrip",
    "DataSpell": "DataSpell",
    "Writerside": "Writerside",
    "RustRover": "RustRover",
    "Aqua": "Aqua",
}


def get_config_bases():
    """获取所有可能的 JetBrains 配置根目录列表"""
    system = platform.system()
    bases = []
    if system == "Windows":
        # Windows 上 IDE 目录可能分布在 APPDATA 和 LOCALAPPDATA 两处
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if appdata:
            bases.append(os.path.join(appdata, "JetBrains"))
        if localappdata and localappdata != appdata:
            bases.append(os.path.join(localappdata, "JetBrains"))
    elif system == "Darwin":
        home = os.path.expanduser("~")
        bases.append(os.path.join(home, "Library", "Application Support", "JetBrains"))
    else:
        home = os.path.expanduser("~")
        bases.append(os.path.join(home, ".config", "JetBrains"))
        bases.append(os.path.join(home, ".local", "share", "JetBrains"))
    return bases


# 已知的 JetBrains 捆绑/内置插件 xmlId 前缀或精确匹配，导出时自动过滤
BUNDLED_PLUGIN_PREFIXES = (
    "com.intellij.",
    "org.jetbrains.",
    "Docker",
    "com.android.tools",
)
BUNDLED_PLUGIN_IDS = {
    "hg4idea", "PerforceDirectPlugin", "Subversion", "Git4Idea",
    "github", "org.jetbrains.plugins.terminal",
}


def is_bundled_plugin(plugin_id, plugin_name):
    """判断是否为捆绑/内置插件"""
    if plugin_id in BUNDLED_PLUGIN_IDS:
        return True
    for prefix in BUNDLED_PLUGIN_PREFIXES:
        if (plugin_id and plugin_id.startswith(prefix)) or \
           (plugin_name and plugin_name.startswith(prefix)):
            return True
    return False


def find_ide_directories():
    """查找本地已安装的 JetBrains IDE 目录"""
    config_bases = get_config_bases()
    found = []
    seen_ide_keys = {}  # entry_name -> index in found, 用于按 IDE 名称+版本去重

    for config_base in config_bases:
        if not os.path.isdir(config_base):
            continue

        for entry in sorted(os.listdir(config_base)):
            full_path = os.path.join(config_base, entry)
            if not os.path.isdir(full_path):
                continue

            matched_name = None
            for prefix, display_name in IDE_CONFIGS.items():
                if entry.startswith(prefix) and (len(entry) == len(prefix) or entry[len(prefix)].isdigit()):
                    matched_name = display_name
                    break

            if not matched_name:
                continue

            # 计算版本号
            version = ""
            for prefix in IDE_CONFIGS:
                if entry.startswith(prefix):
                    version = entry[len(prefix):]
                    break

            # 确定插件目录路径：优先检查同目录下的 plugins，再检查其他配置根
            plugins_dir = os.path.join(full_path, "plugins")
            if not os.path.isdir(plugins_dir):
                for other_base in config_bases:
                    if other_base == config_base:
                        continue
                    alt = os.path.join(other_base, entry, "plugins")
                    if os.path.isdir(alt):
                        plugins_dir = alt
                        break

            ide_entry = {
                "config_dir": full_path,
                "plugins_dir": plugins_dir,
                "name": matched_name,
                "version": version,
                "dir_name": entry,
            }

            # 按目录名去重：同一 IDE 版本可能在 APPDATA 和 LOCALAPPDATA 都有
            if entry in seen_ide_keys:
                existing_idx = seen_ide_keys[entry]
                existing = found[existing_idx]
                # 优先保留有实际插件目录的条目
                if not os.path.isdir(existing["plugins_dir"]) and os.path.isdir(plugins_dir):
                    found[existing_idx] = ide_entry
            else:
                seen_ide_keys[entry] = len(found)
                found.append(ide_entry)

    return found


def extract_xmlid_from_jar(jar_path):
    """从 JAR 文件中的 plugin.xml 提取 xmlId"""
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            if "META-INF/plugin.xml" in zf.namelist():
                content = zf.read("META-INF/plugin.xml")
                return parse_plugin_xml(content)
    except Exception:
        pass
    return None


def parse_plugin_xml(content):
    """解析 plugin.xml 内容，提取插件信息"""
    try:
        # 处理可能的 BOM
        if content.startswith(b"\xef\xbb\xbf"):
            content = content[3:]
        root = ET.fromstring(content)
        plugin_id_elem = root.find("id")
        name_elem = root.find("name")
        return {
            "id": plugin_id_elem.text.strip() if plugin_id_elem is not None and plugin_id_elem.text else None,
            "name": name_elem.text.strip() if name_elem is not None and name_elem.text else None,
        }
    except ET.ParseError:
        return None


def scan_plugins_directory(plugins_dir):
    """扫描插件目录，提取所有已安装插件的信息"""
    plugins = {}

    if not os.path.isdir(plugins_dir):
        return plugins

    for item in os.listdir(plugins_dir):
        item_path = os.path.join(plugins_dir, item)
        if not os.path.isdir(item_path):
            continue

        plugin_info = None

        # 方式1：目录结构 plugin_name/lib/*.jar（新版格式）
        lib_dir = os.path.join(item_path, "lib")
        if os.path.isdir(lib_dir):
            for jar_file in os.listdir(lib_dir):
                if jar_file.endswith(".jar") and "searchableOptions" not in jar_file:
                    jar_path = os.path.join(lib_dir, jar_file)
                    result = extract_xmlid_from_jar(jar_path)
                    if result and (result.get("id") or result.get("name")):
                        plugin_info = result
                        break

        # 方式2：直接包含 META-INF/plugin.xml
        if plugin_info is None:
            meta_xml = os.path.join(item_path, "META-INF", "plugin.xml")
            if os.path.isfile(meta_xml):
                try:
                    with open(meta_xml, "rb") as f:
                        plugin_info = parse_plugin_xml(f.read())
                except Exception:
                    pass

        # 方式3：目录本身就是 jar 文件（旧版格式）
        if plugin_info is None:
            for jar_file in os.listdir(item_path):
                if jar_file.endswith(".jar"):
                    result = extract_xmlid_from_jar(os.path.join(item_path, jar_file))
                    if result and (result.get("id") or result.get("name")):
                        plugin_info = result
                        break

        if plugin_info:
            key = plugin_info.get("id") or plugin_info.get("name") or item
            if key not in plugins:
                plugins[key] = plugin_info

    return plugins


def main():
    print("正在扫描 JetBrains IDE 已安装插件...\n")

    ide_list = find_ide_directories()
    if not ide_list:
        print("未找到任何 JetBrains IDE 安装")
        for base in get_config_bases():
            print(f"已检查目录: {base}")
        sys.exit(1)

    all_plugins = {}

    for ide in ide_list:
        label = f"{ide['name']} {ide['version']}" if ide["version"] else ide["name"]
        print(f"扫描: {label}")
        print(f"  插件目录: {ide['plugins_dir']}")

        if not os.path.isdir(ide["plugins_dir"]):
            print("  (插件目录不存在，跳过)\n")
            continue

        plugins = scan_plugins_directory(ide["plugins_dir"])

        # 过滤捆绑插件
        third_party = {
            pid: info for pid, info in plugins.items()
            if not is_bundled_plugin(pid, info.get("name", ""))
        }
        bundled_count = len(plugins) - len(third_party)

        print(f"  发现 {len(third_party)} 个第三方插件", end="")
        if bundled_count > 0:
            print(f"（已过滤 {bundled_count} 个捆绑插件）")
        else:
            print()
        for pid, info in sorted(third_party.items()):
            display = info.get("name", pid)
            id_str = info.get("id", "")
            if id_str and id_str != display:
                print(f"    - {display} ({id_str})")
            else:
                print(f"    - {display}")
        print()

        all_plugins.update(third_party)

    if not all_plugins:
        print("未发现任何第三方插件")
        sys.exit(0)

    # 写入输出文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# JetBrains IDE 已导出插件列表\n")
        f.write(f"# 导出时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 共 {len(all_plugins)} 个插件\n")
        f.write("#\n")
        f.write("# 注意：部分内置/捆绑插件可能不在 Marketplace 上，下载时会跳过\n")
        f.write("# 建议检查列表，移除不需要的插件\n\n")
        for pid in sorted(all_plugins.keys()):
            f.write(f"{pid}\n")

    print(f"已导出 {len(all_plugins)} 个插件到: {OUTPUT_FILE}")
    print("请检查列表，移除不需要的插件后，使用 download.py 下载")


if __name__ == "__main__":
    main()
