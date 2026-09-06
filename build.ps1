param([string]$Version = "dev")
$ErrorActionPreference = "Stop"
python -m pip install -r requirements.txt pyinstaller
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
Set-Content -LiteralPath plugin_migrate\_build_version.py -Value "VERSION = '$Version'" -Encoding utf8
python -m PyInstaller --clean --noconfirm --onefile --name "plugin-migrate-$Version" plugin_migrate/__main__.py
Remove-Item -LiteralPath plugin_migrate\_build_version.py -Force
Write-Host "Binary created in dist/"
