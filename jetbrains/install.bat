@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ============================================
echo   JetBrains IDE 插件批量安装工具
echo ============================================
echo.

REM 检查 plugin-downloads 目录
set "DOWNLOAD_DIR=%~dp0plugin-downloads"
if not exist "%DOWNLOAD_DIR%" (
    echo 错误：找不到 plugin-downloads 目录
    echo 请先运行 python jetbrains\download.py 下载插件
    echo.
    pause
    exit /b 1
)

REM 统计 zip 文件数量
set count=0
for %%f in ("%DOWNLOAD_DIR%\*.zip") do set /a count+=1
if %count%==0 (
    echo 错误：plugin-downloads 目录中没有 zip 文件
    echo 请先运行 python jetbrains\download.py 下载插件
    echo.
    pause
    exit /b 1
)

echo 找到 %count% 个插件包待安装
echo.

REM 自动检测 JetBrains IDE 插件目录（同时检查 APPDATA 和 LOCALAPPDATA）
echo 正在检测 JetBrains IDE 安装...
echo.

set "FOUND_IDE=0"
set "idx=0"

REM 扫描 APPDATA 下的 IDE
for /d %%d in ("%APPDATA%\JetBrains\*") do (
    call :detect_ide "%%d"
)
REM 扫描 LOCALAPPDATA 下的 IDE（去重）
if /i not "%LOCALAPPDATA%"=="%APPDATA%" (
    for /d %%d in ("%LOCALAPPDATA%\JetBrains\*") do (
        call :detect_ide "%%d"
    )
)

if !FOUND_IDE!==0 (
    echo 未检测到 JetBrains IDE
    echo.
    echo 请手动安装插件：
    echo   1. 打开 IDE
    echo   2. 进入 Settings ^> Plugins
    echo   3. 点击齿轮图标 ^> Install Plugin from Disk...
    echo   4. 选择 plugin-downloads 目录中的 zip 文件
    echo.
    pause
    exit /b 1
)

echo.
echo 请选择要安装到的目标 IDE（输入序号）：
echo.

REM 列出检测到的 IDE（重新遍历以生成列表）
set "idx=0"
for /d %%d in ("%APPDATA%\JetBrains\*") do (
    call :list_ide "%%d"
)
if /i not "%LOCALAPPDATA%"=="%APPDATA%" (
    for /d %%d in ("%LOCALAPPDATA%\JetBrains\*") do (
        call :list_ide "%%d"
    )
)

echo.
set /p choice="请输入序号 (1-%idx%): "

set "TARGET_DIR=!ide_%choice%!"
if "!TARGET_DIR!"=="" (
    echo 无效的选择
    pause
    exit /b 1
)

echo.
echo 将安装到: !TARGET_DIR!
echo.

REM 创建目标目录（如果不存在）
if not exist "!TARGET_DIR!" mkdir "!TARGET_DIR!"

REM 逐个解压插件（zip 内部已包含 plugin_name/lib/ 结构，直接解压到 plugins 目录即可）
set success=0
set fail=0

for %%f in ("%DOWNLOAD_DIR%\*.zip") do (
    set "filename=%%~nxf"
    echo 安装: !filename! ...

    REM 直接解压到 plugins 目录，zip 内部结构会自动创建正确的子目录
    powershell -Command "Expand-Archive -Path '%%f' -DestinationPath '!TARGET_DIR!' -Force" 2>nul
    if !errorlevel!==0 (
        set /a success+=1
    ) else (
        echo   [警告] 解压失败: !filename!
        set /a fail+=1
    )
)

echo.
echo ============================================
echo 安装完成！成功: %success%, 失败: %fail%
echo ============================================
echo.
echo 请重启 IDE 以加载新安装的插件。
echo.
pause
goto :eof

REM ========== 辅助函数 ==========

:detect_ide
set "dir_path=%~1"
set "dir_name=%~nx1"
echo !dir_name! | findstr /i "PyCharm IntelliJIdea WebStorm GoLand CLion Rider PhpStorm RubyMine DataGrip DataSpell RustRover" >nul
if !errorlevel!==0 (
    REM 去重：检查是否已添加（通过 dir_name 判断）
    if not defined "seen_!dir_name!" (
        set "seen_!dir_name!=1"
        set "plugins_dir=!dir_path!\plugins"
        echo   发现: !dir_name!
        echo   插件目录: !plugins_dir!
        set "FOUND_IDE=1"
    )
)
goto :eof

:list_ide
set "dir_path=%~1"
set "dir_name=%~nx1"
echo !dir_name! | findstr /i "PyCharm IntelliJIdea WebStorm GoLand CLion Rider PhpStorm RubyMine DataGrip DataSpell RustRover" >nul
if !errorlevel!==0 (
    if not defined "listed_!dir_name!" (
        set "listed_!dir_name!=1"
        set /a idx+=1
        echo   !idx^). !dir_name!  ^(!dir_path!\plugins^)
        set "ide_!idx!=!dir_path!\plugins"
    )
)
goto :eof
