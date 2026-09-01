@echo off
for %%f in (*.vsix) do (
    code --install-extension "%%f"
)
echo 安装完成！
pause
