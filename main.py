#!/usr/bin/env python3
"""
Days-Matter - 桌面倒数日应用主入口
支持 Windows / 麒麟系统 (Kylin OS / UKUI)
"""
import os
import sys
import signal

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

# 确保能找到项目模块
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.storage import Storage
from ui.desktop_widget import DesktopWidget
from ui.main_window import MainWindow
from ui.system_tray import SystemTray
from integration.desktop_entry import DesktopEntryManager


class CountdownApp:
    """倒数日应用程序主控类"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Days-Matter")
        self.app.setQuitOnLastWindowClosed(False)  # 防止关闭所有窗口后退出

        # 设置应用属性
        self.app.setOrganizationName("Days-Matter")
        self.app.setApplicationDisplayName("倒数日")

        # 核心组件
        self.storage = Storage()
        self.desktop_widgets = {}  # event_id -> DesktopWidget
        self.main_window = None
        self.tray = None

        # 初始化
        self._init_integration()
        self._init_tray()
        self._init_main_window()
        self._init_desktop_widgets()

        # 首次运行引导
        if self.storage.get_setting("first_run", True):
            self._show_welcome()

        # 信号处理（优雅退出）
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    # ==================== 初始化 ====================

    def _init_integration(self):
        """初始化系统集成（桌面入口、开机自启）"""
        app_path = os.path.join(BASE_DIR, "main.py")
        icon_path = os.path.join(BASE_DIR, "resources", "icon.png")

        self.entry_manager = DesktopEntryManager(
            app_path=app_path,
            icon_path=icon_path if os.path.exists(icon_path) else "",
        )

        # 根据配置决定是否启用开机自启
        auto_start = self.storage.get_setting("auto_start", False)
        if auto_start:
            self.entry_manager.enable_autostart()
        else:
            self.entry_manager.disable_autostart()

    def _init_tray(self):
        """初始化系统托盘"""
        self.tray = SystemTray(
            on_show_main=self._show_main_window,
            on_quit=self._quit_app,
        )
        self.tray.show()

    def _init_main_window(self):
        """初始化主设置窗口"""
        self.main_window = MainWindow(
            storage=self.storage,
            on_event_changed=self._on_event_changed,
        )

    def _init_desktop_widgets(self):
        """初始化所有桌面悬浮组件"""
        events = self.storage.get_events()
        for event in events:
            self._create_widget(event)

    # ==================== 窗口管理 ====================

    def _show_main_window(self):
        """显示主窗口"""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _create_widget(self, event_data: dict):
        """创建一个桌面悬浮组件"""
        event_id = event_data["id"]

        # 如果已存在，先清理
        if event_id in self.desktop_widgets:
            self.desktop_widgets[event_id].close()
            self.desktop_widgets[event_id].deleteLater()

        widget = DesktopWidget(
            event_data=event_data,
            storage=self.storage,
            on_settings=lambda eid=event_id: self._edit_event(eid),
            on_delete=lambda eid=event_id: self._delete_event(eid),
        )
        widget.show()
        self.desktop_widgets[event_id] = widget

    def _refresh_all_widgets(self):
        """刷新所有桌面组件"""
        events = self.storage.get_events()
        current_ids = set(self.desktop_widgets.keys())
        stored_ids = {e["id"] for e in events}

        # 移除已删除的事件组件
        for eid in current_ids - stored_ids:
            if eid in self.desktop_widgets:
                self.desktop_widgets[eid].close()
                self.desktop_widgets[eid].deleteLater()
                del self.desktop_widgets[eid]

        # 更新或创建组件
        for event in events:
            eid = event["id"]
            if eid in self.desktop_widgets:
                # 更新已有组件
                self.desktop_widgets[eid].apply_style_from_event(event)
            else:
                # 创建新组件
                self._create_widget(event)

    def _show_all_widgets(self):
        """显示所有桌面组件"""
        for widget in self.desktop_widgets.values():
            widget.show()

    def _hide_all_widgets(self):
        """隐藏所有桌面组件"""
        for widget in self.desktop_widgets.values():
            widget.hide()

    # ==================== 事件回调 ====================

    def _on_event_changed(self, action: str, event_id: str):
        """
        事件变更回调

        Args:
            action: 操作类型 - "added", "updated", "deleted",
                    "show_all", "hide_all", "autostart"
            event_id: 事件 ID
        """
        if action in ("added", "updated", "deleted"):
            self._refresh_all_widgets()
        elif action == "show_all":
            self._show_all_widgets()
        elif action == "hide_all":
            self._hide_all_widgets()
        elif action == "autostart":
            auto_start = self.storage.get_setting("auto_start", False)
            if auto_start:
                self.entry_manager.enable_autostart()
            else:
                self.entry_manager.disable_autostart()

    def _edit_event(self, event_id: str):
        """通过悬浮窗右键编辑事件"""
        event = self.storage.get_event(event_id)
        if not event:
            return

        from ui.event_dialog import EventDialog
        dialog = EventDialog(None, event_data=event)
        if dialog.exec_() == EventDialog.Accepted:
            data = dialog.get_result()
            self.storage.update_event(event_id, data)
            self._refresh_all_widgets()
            if self.main_window:
                self.main_window._refresh_list()

    def _delete_event(self, event_id: str):
        """通过悬浮窗右键删除事件"""
        from PyQt5.QtWidgets import QMessageBox

        event = self.storage.get_event(event_id)
        title = event.get("title", "未知") if event else "未知"

        reply = QMessageBox.question(
            None, "确认删除",
            f"确定要删除「{title}」吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.storage.delete_event(event_id)
            self._refresh_all_widgets()
            if self.main_window:
                self.main_window._refresh_list()

    # ==================== 欢迎引导 ====================

    def _show_welcome(self):
        """首次启动欢迎引导"""
        from PyQt5.QtWidgets import QMessageBox

        # 创建桌面快捷方式
        self.entry_manager.create_desktop_shortcut()
        self.entry_manager.create_menu_entry()

        QMessageBox.information(
            None, "欢迎使用倒数日",
            "🎉 欢迎使用倒数日！\n\n"
            "已为您创建桌面快捷方式。\n"
            "点击系统托盘图标可以打开管理界面。\n\n"
            "现在您可以点击「确定」开始添加第一个倒数日事件！",
        )

        self.storage.set_setting("first_run", False)

        # 打开管理界面让用户添加事件
        self._show_main_window()

    # ==================== 退出 ====================

    def _quit_app(self):
        """退出应用"""
        # 清理桌面组件
        for widget in self.desktop_widgets.values():
            widget.close()
        self.desktop_widgets.clear()

        # 清理托盘
        if self.tray:
            self.tray.hide()

        self.app.quit()

    def _signal_handler(self, signum, frame):
        """信号处理"""
        print(f"[Days-Matter] 收到信号 {signum}，正在退出...")
        self._quit_app()

    # ==================== 运行 ====================

    def run(self):
        """运行应用"""
        # 默认显示所有悬浮组件，最小化管理窗口
        if self.storage.get_events():
            # 有事件时不自动弹出管理窗口
            pass
        else:
            # 没有事件时显示管理窗口
            self._show_main_window()

        sys.exit(self.app.exec_())


def main():
    """主入口函数"""
    app = CountdownApp()
    app.run()


if __name__ == "__main__":
    main()