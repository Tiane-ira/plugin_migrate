# Plugin Migrate

在联网机器下载插件，在内网机器从离线介质批量安装 VS Code 和 JetBrains 插件。

## 二进制版本

发布版本提供 Windows、Linux、macOS 单文件二进制，不需要目标机器安装 Python 或 `requests`。直接运行不带参数的程序会进入交互菜单；熟悉命令行后可使用同样的子命令。版本 tag 使用日期格式，例如 `v2026.09.06`。

本地构建（需要联网安装 PyInstaller）：

```powershell
./build.ps1 -Version 2026.09.06
```

## 两阶段工作流

1. 联网机器安装 Python 3 和 `requests`：`pip install requests`。
2. 自动读取本机插件，或按名称搜索并选择：

   ```bash
   python -m plugin_migrate vscode discover
   python -m plugin_migrate vscode search python --output vscode/vscode-extensions.txt
   python -m plugin_migrate jetbrains discover --products idea,pycharm
   python -m plugin_migrate jetbrains search git --output jetbrains/jetbrains-plugins.txt
   ```

   JetBrains 默认只扫描 IntelliJ IDEA 和 PyCharm；可用 `--products idea,pycharm,webstorm` 指定产品，或用 `all` 扫描全部产品。

3. 下载到可携带目录：

   ```bash
   python -m plugin_migrate vscode download
   python -m plugin_migrate jetbrains download
   ```

   也可以用 `--file LIST.txt` 或重复使用 `--plugin ID` 指定列表。将生成的 `vsix-downloads/`、`plugin-downloads/` 复制到内网机器；压缩包不会提交到 Git。

4. 内网机器只需 Python 3（以及 VS Code 的 `code` 命令）：

   ```bash
   python -m plugin_migrate vscode install vscode/vsix-downloads
   python -m plugin_migrate jetbrains install jetbrains/plugin-downloads --target /path/to/IDE/plugins
   ```

   Windows 使用同样的 Python 命令；JetBrains 的 `--target` 指向目标 IDE 的 `plugins` 目录。

使用发布的二进制时，将命令中的 `python -m plugin_migrate` 替换为 `plugin-migrate-windows.exe`、`plugin-migrate-linux` 或 `plugin-migrate-macos`；二进制安装阶段不访问网络。

## 目录与文档

- `plugin_migrate/cli.py`：统一的发现、搜索和下载入口。
- `plugin_migrate/vscode.py`、`plugin_migrate/jetbrains.py`：平台发现、搜索和下载实现。
- `plugin_migrate/install.py`：完全离线的归档安装实现。
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)：数据流、边界和扩展约定。

下载失败会逐项报告；安装前请关闭 IDE，并确认目标 IDE 与插件版本兼容。
