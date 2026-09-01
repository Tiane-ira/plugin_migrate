# JetBrains IDE 插件迁移工具

将一台机器上的 JetBrains IDE 插件批量迁移到另一台机器，适用于换电脑、重装系统、离线环境等场景。
支持 PyCharm、IntelliJ IDEA、WebStorm、GoLand、CLion、Rider 等全系列 IDE。

## 整体流程

```
源机器（导出）          迁移介质              目标机器（安装）
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 导出插件列表  │───▶│ 下载 .zip    │───▶│ 批量安装插件  │
│ .txt 文件    │    │ 文件拷贝      │    │ .bat / .sh   │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 使用步骤

### 1. 在源机器上导出插件列表（自动）

运行导出脚本，自动扫描本地已安装的 JetBrains IDE 插件：

```bash
python jetbrains/export_plugins.py
```

脚本会扫描所有已安装的 JetBrains IDE（PyCharm、IntelliJ IDEA 等），提取插件 ID，输出到 `jetbrains-plugins.txt`。

> **注意**：导出结果中可能包含部分内置/捆绑插件，建议手动检查并移除不需要的条目。

### 1b. 手动创建插件列表（可选）

如果不使用自动导出，也可以手动创建 `jetbrains-plugins.txt`。

每行一个插件 ID，支持两种格式：

**格式1（推荐）：数字 ID** — 从 JetBrains Marketplace URL 中获取

```
https://plugins.jetbrains.com/plugin/10080-gittoolbox
                                    ^^^^
                                    数字 ID: 10080
```

**格式2：xmlId** — 插件内部标识符

```
izhangzhihao.rainbow.brackets
```

示例 `jetbrains-plugins.txt`：

```
10080
10044
7125
izhangzhihao.rainbow.brackets
```

### 2. 下载插件 zip 文件

确保已安装依赖：

```bash
pip install requests
```

运行下载脚本：

```bash
python jetbrains/download.py
```

脚本会读取 `jetbrains-plugins.txt`，从 JetBrains Marketplace 逐个下载插件 zip 文件，保存到 `plugin-downloads/` 目录。

### 3. 将 zip 文件拷贝到目标机器

将整个 `plugin-downloads/` 目录通过 U 盘、网盘或其他方式拷贝到目标机器。

### 4. 在目标机器上批量安装

**Windows：**

```bash
jetbrains\install.bat
```

**Linux / macOS：**

```bash
chmod +x jetbrains/install.sh
./jetbrains/install.sh
```

脚本会自动检测本地安装的 JetBrains IDE，列出供选择，然后将插件解压到对应的 plugins 目录。

安装完成后重启 IDE 即可加载新插件。

## 文件说明

| 文件 | 说明 |
|---|---|
| `export_plugins.py` | 自动扫描本地 IDE 已安装插件，导出到 txt 文件 |
| `download.py` | 核心脚本，读取插件列表并从 Marketplace 下载 zip 文件 |
| `jetbrains-plugins.txt` | 插件 ID 列表（自动导出或手动创建） |
| `install.bat` | Windows 批量安装脚本 |
| `install.sh` | Linux / macOS 批量安装脚本 |
| `plugin-downloads/` | 下载的 zip 文件存放目录（运行 download.py 后自动生成） |

## 与 VS Code 方案的对比

| 特性 | VS Code | JetBrains |
|---|---|---|
| 导出插件列表 | `code --list-extensions` 一行命令 | 需要 `export_plugins.py` 扫描目录 |
| 插件标识格式 | `publisher.name` | 数字 ID 或 xmlId |
| 下载格式 | `.vsix` | `.zip` |
| 安装方式 | `code --install-extension` CLI | 解压到 plugins 目录 |
| 跨 IDE 支持 | 仅 VS Code | 支持全系列 JetBrains IDE |

## 注意事项

- 下载需要网络连接，访问的是 JetBrains Marketplace 官方地址。
- 目标机器需要已安装对应的 JetBrains IDE。
- 如果某个插件下载失败（网络问题或插件已下架），脚本不会中断，继续处理后续插件。
- 部分插件可能有 IDE 版本兼容性要求，安装后请在 IDE 中检查是否正常工作。
- 导出脚本通过解析本地插件 JAR 文件获取 xmlId，极少数插件可能无法正确识别。
- 使用 xmlId 格式时，下载脚本需要通过 Marketplace API 解析为数字 ID，可能存在解析失败的情况，建议优先使用数字 ID。
- 安装前请确保 IDE 已关闭，避免文件冲突。
