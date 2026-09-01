# VSCode 插件迁移工具

将一台机器上的 VSCode 插件批量迁移到另一台机器，适用于换电脑、重装系统、离线环境等场景。

## 整体流程

```
源机器（导出）          迁移介质            目标机器（安装）
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 导出插件列表  │───▶│ 下载 .vsix   │───▶│ 批量安装插件  │
│ .txt 文件    │    │ 文件拷贝      │    │ .bat / .sh   │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 使用步骤

### 1. 在源机器上导出插件列表

```bash
code --list-extensions > vscode/vscode-extensions.txt
```

生成的 `vscode/vscode-extensions.txt` 每行一个插件 ID，格式为 `publisher.name`，例如：

```
ms-python.python
dbaeumer.vscode-eslint
esbenp.prettier-vscode
```

### 2. 下载插件 .vsix 文件

确保已安装依赖：

```bash
pip install requests
```

运行下载脚本：

```bash
python vscode/download.py
```

脚本会读取 `vscode-extensions.txt`，从 VS Code Marketplace 官方源逐个下载 `.vsix` 文件，保存到 `vsix-downloads/` 目录。

### 3. 将 .vsix 文件拷贝到目标机器

将整个 `vsix-downloads/` 目录通过 U 盘、网盘或其他方式拷贝到目标机器。

### 4. 在目标机器上批量安装

**Windows：**

```bash
cd vscode\vsix-downloads
install.bat
```

**Linux / macOS：**

```bash
cd vscode/vsix-downloads
chmod +x ../install.sh
../install.sh
```

脚本会遍历当前目录下所有 `.vsix` 文件，依次调用 `code --install-extension` 完成安装。

## 文件说明

| 文件 | 说明 |
|---|---|
| `download.py` | 核心脚本，读取插件列表并从 Marketplace 下载 .vsix 文件 |
| `vscode-extensions.txt` | 插件 ID 列表（需自行生成） |
| `install.bat` | Windows 批量安装脚本 |
| `install.sh` | Linux / macOS 批量安装脚本 |
| `vsix-downloads/` | 下载的 .vsix 文件存放目录（运行 download.py 后自动生成） |

## 注意事项

- 下载需要网络连接，访问的是 VS Code Marketplace 官方地址。
- 目标机器需要已安装 VSCode，且 `code` 命令已加入系统 PATH。
- 如果某个插件下载失败（网络问题或插件已下架），脚本不会中断，继续处理后续插件。
- 部分插件可能有版本兼容性要求，安装后请在 VSCode 中检查是否正常工作。
