#!/bin/bash

echo "============================================"
echo "  JetBrains IDE 插件批量安装工具"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOWNLOAD_DIR="$SCRIPT_DIR/plugin-downloads"

# 检查 plugin-downloads 目录
if [ ! -d "$DOWNLOAD_DIR" ]; then
    echo "错误：找不到 plugin-downloads 目录"
    echo "请先运行 python jetbrains/download.py 下载插件"
    exit 1
fi

# 统计 zip 文件数量
zip_count=$(find "$DOWNLOAD_DIR" -maxdepth 1 -name "*.zip" | wc -l)
if [ "$zip_count" -eq 0 ]; then
    echo "错误：plugin-downloads 目录中没有 zip 文件"
    echo "请先运行 python jetbrains/download.py 下载插件"
    exit 1
fi

echo "找到 $zip_count 个插件包待安装"
echo ""

# 检测操作系统，确定插件目录
detect_plugins_base() {
    case "$(uname -s)" in
        Darwin)
            echo "$HOME/Library/Application Support/JetBrains"
            ;;
        Linux)
            echo "$HOME/.local/share/JetBrains"
            ;;
        *)
            echo "$HOME/.local/share/JetBrains"
            ;;
    esac
}

PLUGINS_BASE=$(detect_plugins_base)

if [ ! -d "$PLUGINS_BASE" ]; then
    echo "未找到 JetBrains 配置目录: $PLUGINS_BASE"
    echo ""
    echo "请手动安装插件："
    echo "  1. 打开 IDE"
    echo "  2. 进入 Settings > Plugins"
    echo "  3. 点击齿轮图标 > Install Plugin from Disk..."
    echo "  4. 选择 plugin-downloads 目录中的 zip 文件"
    exit 1
fi

# 列出检测到的 IDE
echo "正在检测 JetBrains IDE 安装..."
echo ""

idx=0
declare -a IDE_DIRS
declare -a IDE_NAMES

for dir in "$PLUGINS_BASE"/*/; do
    dir_name=$(basename "$dir")
    if echo "$dir_name" | grep -qiE "^(PyCharm|IntelliJIdea|WebStorm|GoLand|CLion|Rider|PhpStorm|RubyMine|DataGrip|DataSpell|RustRover)"; then
        idx=$((idx + 1))
        IDE_DIRS[$idx]="$dir"
        IDE_NAMES[$idx]="$dir_name"
        echo "  $idx). $dir_name"
    fi
done

if [ "$idx" -eq 0 ]; then
    echo "未检测到 JetBrains IDE"
    echo "配置目录: $PLUGINS_BASE"
    exit 1
fi

echo ""
read -p "请选择要安装到的目标 IDE（输入序号 [1-$idx]）: " choice

if [ -z "$choice" ] || [ "$choice" -lt 1 ] || [ "$choice" -gt "$idx" ]; then
    echo "无效的选择"
    exit 1
fi

TARGET_DIR="${IDE_DIRS[$choice]}plugins"
echo ""
echo "将安装到: $TARGET_DIR"
echo ""

# 创建目标目录
mkdir -p "$TARGET_DIR"

# 逐个解压插件
success=0
fail=0

for zip_file in "$DOWNLOAD_DIR"/*.zip; do
    filename=$(basename "$zip_file")
    echo "安装: $filename ..."

# 直接解压到 plugins 目录，zip 内部已包含 plugin_name/lib/ 结构
    if unzip -q -o "$zip_file" -d "$TARGET_DIR" 2>/dev/null; then
        success=$((success + 1))
    else
        echo "  [警告] 解压失败: $filename"
        fail=$((fail + 1))
    fi
done

echo ""
echo "============================================"
echo "安装完成！成功: $success, 失败: $fail"
echo "============================================"
echo ""
echo "请重启 IDE 以加载新安装的插件。"
