#!/bin/bash
# ====================================================
#  Days-Matter - Linux (.deb) 打包脚本
#  生成标准 Debian 安装包，兼容麒麟/Ubuntu/Debian
# ====================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="days-matter"
APP_DISPLAY_NAME="倒数日"
VERSION="1.0.0"
ARCH="all"
MAINTAINER="Days-Matter Team"
DESCRIPTION="桌面倒数日工具 - 支持倒计时和正计时，提供高度客制化的桌面悬浮组件"

BUILD_DIR="$SCRIPT_DIR/build_deb"
DEBIAN_DIR="$BUILD_DIR/DEBIAN"
INSTALL_DIR="$BUILD_DIR/opt/$APP_NAME"
DESKTOP_DIR="$BUILD_DIR/usr/share/applications"
ICON_DIR="$BUILD_DIR/usr/share/icons/hicolor"

echo "========================================="
echo "  Days-Matter - .deb 打包脚本"
echo "========================================="
echo ""

# 检查依赖
if ! command -v dpkg-deb &> /dev/null; then
    echo "[ERROR] 未找到 dpkg-deb，请安装: sudo apt install dpkg-dev"
    exit 1
fi

# 清理旧的构建目录
echo "[1/5] 清理旧的构建文件..."
rm -rf "$BUILD_DIR"

# 创建目录结构
echo "[2/5] 创建 deb 包目录结构..."
mkdir -p "$DEBIAN_DIR"
mkdir -p "$INSTALL_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR/48x48/apps"
mkdir -p "$ICON_DIR/128x128/apps"
mkdir -p "$ICON_DIR/256x256/apps"

# 复制应用文件
echo "[3/5] 复制应用文件..."
cp -r "$SCRIPT_DIR"/*.py "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/core" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/ui" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/integration" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/resources" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/LICENSE" "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/" 2>/dev/null || true

# 清理 __pycache__ 和 pyc 文件
find "$INSTALL_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$INSTALL_DIR" -name "*.pyc" -delete 2>/dev/null || true

# 设置权限
find "$INSTALL_DIR" -type f -name "*.py" -exec chmod 644 {} \;
find "$INSTALL_DIR" -type d -exec chmod 755 {} \;

# 如果存在图标则复制，否则创建占位图标
if [ -f "$SCRIPT_DIR/resources/icon.png" ]; then
    cp "$SCRIPT_DIR/resources/icon.png" "$ICON_DIR/256x256/apps/$APP_NAME.png"
    # 使用 convert 缩放图标（如果可用）
    if command -v convert &> /dev/null; then
        convert "$SCRIPT_DIR/resources/icon.png" -resize 48x48 "$ICON_DIR/48x48/apps/$APP_NAME.png" 2>/dev/null || true
        convert "$SCRIPT_DIR/resources/icon.png" -resize 128x128 "$ICON_DIR/128x128/apps/$APP_NAME.png" 2>/dev/null || true
    else
        # 直接复制，让桌面环境自己缩放
        cp "$SCRIPT_DIR/resources/icon.png" "$ICON_DIR/48x48/apps/$APP_NAME.png"
        cp "$SCRIPT_DIR/resources/icon.png" "$ICON_DIR/128x128/apps/$APP_NAME.png"
    fi
fi

# 创建 .desktop 文件
echo "[4/5] 创建 .desktop 文件..."
cat > "$DESKTOP_DIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Type=Application
Name=$APP_DISPLAY_NAME
Name[zh_CN]=$APP_DISPLAY_NAME
Name[en]=Days-Matter
Comment=桌面倒数日工具 - 支持倒计时和正计时
Comment[zh_CN]=桌面倒数日工具 - 支持倒计时和正计时
Exec=/opt/$APP_NAME/main.py
Icon=$APP_NAME
Categories=Utility;
Keywords=countdown;timer;date;倒数;计时;日期;
Terminal=false
StartupNotify=true
StartupWMClass=days-matter
EOF
chmod 644 "$DESKTOP_DIR/$APP_NAME.desktop"

# 创建 postinst 脚本（安装后配置）
echo "[5/5] 创建安装配置脚本..."
cat > "$DEBIAN_DIR/postinst" << 'POSTINST'
#!/bin/bash
set -e

APP_NAME="days-matter"
APP_DISPLAY_NAME="倒数日"
INSTALL_DIR="/opt/$APP_NAME"

echo ""
echo "========================================="
echo "  $APP_DISPLAY_NAME 安装完成！"
echo "========================================="
echo ""

# 安装 Python 依赖
if command -v pip3 &> /dev/null; then
    echo "[INFO] 安装 Python 依赖..."
    pip3 install -r "$INSTALL_DIR/requirements.txt" --user 2>/dev/null || \
        pip3 install -r "$INSTALL_DIR/requirements.txt" 2>/dev/null || true
fi

# 确保 python3 可用
if command -v python3 &> /dev/null; then
    # 检查 PyQt5 是否可用
    python3 -c "from PyQt5 import QtWidgets" 2>/dev/null || {
        echo "[INFO] 安装 PyQt5..."
        apt-get install -y python3-pyqt5 2>/dev/null || \
            pip3 install PyQt5 2>/dev/null || true
    }

    # 修复 shebang 和权限
    chmod +x "$INSTALL_DIR/main.py"
    chmod -R 755 "$INSTALL_DIR"
    find "$INSTALL_DIR" -type f -name "*.py" -exec chmod 644 {} \;
fi

# 更新桌面数据库
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

echo ""
echo "启动方式："
echo "  1. 开始菜单搜索「$APP_DISPLAY_NAME」"
echo "  2. 终端运行: python3 $INSTALL_DIR/main.py"
echo ""
POSTINST
chmod 755 "$DEBIAN_DIR/postinst"

# 创建 prerm 脚本（卸载前清理）
cat > "$DEBIAN_DIR/prerm" << 'PRERM'
#!/bin/bash
set -e

APP_NAME="days-matter"
INSTALL_DIR="/opt/$APP_NAME"

# 停止应用（如果正在运行则杀死进程）
if command -v pkill &> /dev/null; then
    pkill -f "$INSTALL_DIR/main.py" 2>/dev/null || true
fi

# 删除用户级 autostart（如果存在）
for home_dir in /home/* /root; do
    if [ -d "$home_dir" ]; then
        rm -f "$home_dir/.config/autostart/$APP_NAME.desktop" 2>/dev/null || true
        rm -f "$home_dir/.local/share/applications/$APP_NAME.desktop" 2>/dev/null || true
    fi
done

echo "[INFO] 正在卸载 $APP_NAME ..."
PRERM
chmod 755 "$DEBIAN_DIR/prerm"

# 创建 control 文件
cat > "$DEBIAN_DIR/control" << EOF
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Depends: python3 (>= 3.6), python3-pyqt5 (>= 5.15)
Recommends: python3-pip
Description: $DESCRIPTION
 一个跨平台的桌面倒数日应用，支持 Windows 和麒麟系统（Kylin OS），
 提供高度客制化的桌面悬浮组件。
 .
 特性：
  - 桌面悬浮组件，透明、无边框、可拖动缩放
  - 支持倒计时和正计时双模式
  - 字体、颜色、背景等视觉元素完全自定义
  - 多事件管理，系统托盘常驻
  - 开机自启支持
EOF

# 构建 .deb 包
echo ""
echo "正在构建 .deb 包..."
DEB_FILE="$SCRIPT_DIR/${APP_NAME}_${VERSION}_${ARCH}.deb"
dpkg-deb --build "$BUILD_DIR" "$DEB_FILE"

# 清理构建目录
rm -rf "$BUILD_DIR"

echo ""
echo "========================================="
echo "  .deb 包创建成功！"
echo "========================================="
echo ""
echo "文件: $DEB_FILE"
echo "大小: $(du -h "$DEB_FILE" | cut -f1)"
echo ""
echo "安装方法："
echo "  sudo dpkg -i $DEB_FILE"
echo "  sudo apt install -f  # 补全依赖"
echo ""
echo "卸载方法："
echo "  sudo dpkg -r $APP_NAME"
echo ""