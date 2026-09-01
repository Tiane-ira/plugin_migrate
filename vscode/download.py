import requests
import os

# 读取插件列表
with open("vscode-extensions.txt", "r") as f:
    extensions = [line.strip() for line in f if line.strip()]

os.makedirs("vsix-downloads", exist_ok=True)

for ext_id in extensions:
    publisher, name = ext_id.split(".")
    # 构建官方下载链接
    url = f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisher}/vsextensions/{name}/latest/vspackage"
    print(f"Downloading {ext_id}...")

    resp = requests.get(url)
    with open(f"vsix-downloads/{ext_id}.vsix", "wb") as f:
        f.write(resp.content)
