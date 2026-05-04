#!/bin/bash
# Nav2 Launch Studio 打包脚本
# 用法: ./build.sh

set -e

echo "=== Nav2 Launch Studio 打包 ==="

# 检查 PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "安装 PyInstaller..."
    pip install pyinstaller
fi

# 清理旧构建
rm -rf build/ dist/

# 打包
echo "开始打包..."
pyinstaller nav2_launch_studio.spec --clean

echo ""
echo "=== 打包完成 ==="
echo "可执行文件: dist/Nav2LaunchStudio/Nav2LaunchStudio"
echo "运行: ./dist/Nav2LaunchStudio/Nav2LaunchStudio"
