"""
桌面集成管理 - 创建 .desktop 文件用于开始菜单和桌面快捷方式
兼容麒麟系统 (UKUI/Kylin OS) 和 Windows
"""
import os
import sys


class DesktopEntryManager:
    """Linux .desktop 文件管理器"""

    # 应用信息
    APP_NAME = "倒数日"
    APP_NAME_EN = "Countdown"
    APP_COMMENT = "桌面倒数日工具 - 支持倒计时和正计时"
    APP_CATEGORIES = "Utility;"
    APP_KEYWORDS = "countdown;timer;date;倒数;计时;日期;"

    def __init__(self, app_path: str = None, icon_path: str = None):
        """
        Args:
            app_path: 应用入口脚本路径（如 /opt/days-matter/main.py 或可执行文件）
            icon_path: 图标文件路径
        """
        self.app_path = app_path or sys.executable
        self.icon_path = icon_path or ""

        # Linux 标准路径
        self.home = os.path.expanduser("~")
        self.applications_dir = os.path.join(self.home, ".local", "share", "applications")
        self.desktop_dir = os.path.join(self.home, "桌面")
        self.autostart_dir = os.path.join(self.home, ".config", "autostart")

    # ==================== 开始菜单入口 ====================

    def create_menu_entry(self) -> bool:
        """
        创建开始菜单 .desktop 文件
        路径: ~/.local/share/applications/days-matter.desktop
        """
        os.makedirs(self.applications_dir, exist_ok=True)
        desktop_file = os.path.join(self.applications_dir, "days-matter.desktop")
        return self._write_desktop_file(desktop_file)

    def remove_menu_entry(self) -> bool:
        """移除开始菜单入口"""
        desktop_file = os.path.join(self.applications_dir, "days-matter.desktop")
        try:
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
            return True
        except OSError:
            return False

    # ==================== 桌面快捷方式 ====================

    def create_desktop_shortcut(self) -> bool:
        """
        创建桌面快捷方式
        路径: ~/桌面/days-matter.desktop
        """
        # 麒麟系统桌面路径可能是 桌面 或 Desktop
        desktop_path = self.desktop_dir
        if not os.path.exists(desktop_path):
            desktop_path = os.path.join(self.home, "Desktop")

        os.makedirs(desktop_path, exist_ok=True)
        shortcut_file = os.path.join(desktop_path, "days-matter.desktop")
        return self._write_desktop_file(shortcut_file)

    def remove_desktop_shortcut(self) -> bool:
        """移除桌面快捷方式"""
        for name in ["桌面", "Desktop"]:
            shortcut_file = os.path.join(self.home, name, "days-matter.desktop")
            try:
                if os.path.exists(shortcut_file):
                    os.remove(shortcut_file)
            except OSError:
                pass
        return True

    # ==================== 开机自启 ====================

    def enable_autostart(self) -> bool:
        """
        启用开机自启
        路径: ~/.config/autostart/days-matter.desktop
        """
        os.makedirs(self.autostart_dir, exist_ok=True)
        autostart_file = os.path.join(self.autostart_dir, "days-matter.desktop")
        return self._write_desktop_file(autostart_file, autostart=True)

    def disable_autostart(self) -> bool:
        """禁用开机自启"""
        autostart_file = os.path.join(self.autostart_dir, "days-matter.desktop")
        try:
            if os.path.exists(autostart_file):
                os.remove(autostart_file)
            return True
        except OSError:
            return False

    def is_autostart_enabled(self) -> bool:
        """检查开机自启是否已启用"""
        autostart_file = os.path.join(self.autostart_dir, "days-matter.desktop")
        return os.path.exists(autostart_file)

    # ==================== 核心方法 ====================

    def _write_desktop_file(self, filepath: str, autostart: bool = False) -> bool:
        """
        写入 .desktop 文件

        Args:
            filepath: 目标文件路径
            autostart: 是否为开机自启文件（会添加 X-GNOME-Autostart-enabled=true）
        """
        # 构建 Exec 命令
        if self.app_path.endswith(".py"):
            exec_cmd = f"{sys.executable} {self.app_path}"
        else:
            exec_cmd = self.app_path

        # 麒麟系统中 Python 路径可能不同，使用更稳健的方式
        python_path = self._find_python()
        if python_path:
            exec_cmd = f"{python_path} {self.app_path}" if self.app_path.endswith(".py") else exec_cmd

        content = f"""[Desktop Entry]
Type=Application
Name={self.APP_NAME}
Name[zh_CN]={self.APP_NAME}
Comment={self.APP_COMMENT}
Comment[zh_CN]={self.APP_COMMENT}
Exec={exec_cmd}
Icon={self.icon_path}
Categories={self.APP_CATEGORIES}
Keywords={self.APP_KEYWORDS}
Terminal=false
StartupNotify=true
StartupWMClass=days-matter
"""

        if autostart:
            content += "X-GNOME-Autostart-enabled=true\n"
            content += "X-GNOME-Autostart-Delay=2\n"  # 延迟2秒启动，等待桌面就绪
            content += "X-KDE-autostart-phase=1\n"  # KDE 兼容

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            # 设置可执行权限
            os.chmod(filepath, 0o755)
            return True
        except OSError as e:
            print(f"[DesktopEntry] 写入失败: {e}")
            return False

    @staticmethod
    def _find_python() -> str:
        """查找系统中的 Python 解释器"""
        # 优先使用 python3
        python_paths = [
            "/usr/bin/python3",
            "/usr/bin/python",
            "/usr/local/bin/python3",
            "/usr/local/bin/python",
        ]
        for path in python_paths:
            if os.path.exists(path):
                return path
        return sys.executable