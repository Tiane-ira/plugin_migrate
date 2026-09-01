#!/bin/bash
for file in *.vsix; do
  code --install-extension "$file"
done
echo "安装完成！"
