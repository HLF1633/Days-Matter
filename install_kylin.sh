#!/bin/bash
# ====================================================
#  Days-Matter - 安装脚本（麒麟系统 / Linux）
#  兼容 Kylin OS / Ubuntu / Debian 等基于 apt 的系统
# ====================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="倒数日"
APP_NAME_EN="Days-Matter"
INSTALL_DIR="/opt/days-matter"
DESKTOP_FILE="/usr/share/applications/days-matter.desktop"
USER_DESKTOP="$HOME/.local/share/applications/days-matter.desktop"

echo "========================================="
echo "  Days-Matter - 麒麟系统安装"
echo "========================================="
echo ""

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] 未找到 python3，请先安装 Python3"
    echo "        sudo apt install python3 python3-pip"
    exit 1
fi

echo "[1/5] 安装系统依赖..."
sudo apt update
sudo apt install -y python3-pyqt5 python3-pyqt5.qtsvg 2>/dev/null || \
    pip3 install PyQt5

echo "[2/5] 安装 Python 依赖..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip3 install -r "$SCRIPT_DIR/requirements.txt" --user 2>/dev/null || \
        sudo pip3 install -r "$SCRIPT_DIR/requirements.txt"
fi

echo "[3/5] 复制应用文件到 $INSTALL_DIR ..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null || true
sudo chmod -R 755 "$INSTALL_DIR"

echo "[4/5] 创建桌面快捷方式和开始菜单入口..."
# 确保目录存在
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/桌面"

# 查找图标
ICON_PATH=""
if [ -f "$INSTALL_DIR/resources/icon.png" ]; then
    ICON_PATH="$INSTALL_DIR/resources/icon.png"
fi

PYTHON_PATH=$(which python3)

# 创建 .desktop 文件
cat > "$HOME/.local/share/applications/days-matter.desktop" << EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Name[zh_CN]=$APP_NAME
Name[en]=$APP_NAME_EN
Comment=桌面倒数日工具 - 支持倒计时和正计时
Comment[zh_CN]=桌面倒数日工具 - 支持倒计时和正计时
Exec=$PYTHON_PATH $INSTALL_DIR/main.py
Icon=$ICON_PATH
Categories=Utility;
Keywords=countdown;timer;date;倒数;计时;日期;
Terminal=false
StartupNotify=true
StartupWMClass=days-matter
EOF

chmod +x "$HOME/.local/share/applications/days-matter.desktop"

# 桌面快捷方式
cp "$HOME/.local/share/applications/days-matter.desktop" "$HOME/桌面/days-matter.desktop" 2>/dev/null || \
    cp "$HOME/.local/share/applications/days-matter.desktop" "$HOME/Desktop/days-matter.desktop" 2>/dev/null || true
chmod +x "$HOME/桌面/days-matter.desktop" 2>/dev/null || \
    chmod +x "$HOME/Desktop/days-matter.desktop" 2>/dev/null || true

# 系统级菜单（需要 sudo）
sudo cp "$HOME/.local/share/applications/days-matter.desktop" "$DESKTOP_FILE" 2>/dev/null || true

echo "[5/5] 更新桌面数据库..."
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""
echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "启动方式："
echo "  1. 开始菜单搜索「倒数日」"
echo "  2. 桌面双击「倒数日」图标"
echo "  3. 终端运行: python3 $INSTALL_DIR/main.py"
echo ""
echo "卸载方式："
echo "  运行: bash $INSTALL_DIR/uninstall_kylin.sh"
echo ""