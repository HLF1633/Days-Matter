#!/bin/bash
# ====================================================
#  Days-Matter - 麒麟系统卸载脚本
# ====================================================

set -e

INSTALL_DIR="/opt/days-matter"
DESKTOP_FILE="/usr/share/applications/days-matter.desktop"
USER_DESKTOP="$HOME/.local/share/applications/days-matter.desktop"
AUTOSTART_FILE="$HOME/.config/autostart/days-matter.desktop"

echo "========================================="
echo "  Days-Matter - 卸载"
echo "========================================="
echo ""

echo "[1/4] 移除安装目录..."
if [ -d "$INSTALL_DIR" ]; then
    sudo rm -rf "$INSTALL_DIR"
    echo "  已删除: $INSTALL_DIR"
else
    echo "  目录不存在，跳过"
fi

echo "[2/4] 移除开始菜单入口..."
if [ -f "$USER_DESKTOP" ]; then
    rm -f "$USER_DESKTOP"
    echo "  已删除: $USER_DESKTOP"
fi
if [ -f "$DESKTOP_FILE" ]; then
    sudo rm -f "$DESKTOP_FILE"
    echo "  已删除: $DESKTOP_FILE"
fi

echo "[3/4] 移除桌面快捷方式..."
rm -f "$HOME/桌面/days-matter.desktop" 2>/dev/null || true
rm -f "$HOME/Desktop/days-matter.desktop" 2>/dev/null || true

echo "[4/4] 移除开机自启..."
rm -f "$AUTOSTART_FILE"

echo "更新桌面数据库..."
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""
echo "========================================="
echo "  卸载完成！"
echo "========================================="
echo ""
echo "用户数据（配置和事件）保留在: ~/.days_matter/"
echo "如需完全清除，请手动删除该目录。"
echo ""