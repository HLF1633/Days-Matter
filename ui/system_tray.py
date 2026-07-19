"""
系统托盘图标管理
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen


class SystemTray(QSystemTrayIcon):
    """系统托盘管理器"""

    def __init__(self, on_show_main=None, on_quit=None):
        super().__init__()

        self.on_show_main = on_show_main
        self.on_quit = on_quit

        # 创建一个简单的托盘图标
        icon = self._create_icon()
        self.setIcon(icon)
        self.setToolTip("倒数日")

        # 构建菜单
        self._build_menu()

        # 信号连接
        self.activated.connect(self._on_activated)

    def _create_icon(self) -> QIcon:
        """创建托盘图标（程序化生成 64x64 日历图标）"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景圆角矩形
        painter.setBrush(QColor("#4CAF50"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(2, 2, 60, 60, 10, 10)

        # 顶部红色条
        painter.setBrush(QColor("#F44336"))
        painter.drawRoundedRect(2, 2, 60, 18, 10, 10)
        painter.drawRect(2, 12, 60, 8)  # 覆盖底部圆角

        # 日期数字
        painter.setPen(QPen(QColor("white")))
        font = QFont("Sans Serif", 22, QFont.Bold)
        painter.setFont(font)
        painter.drawText(2, 22, 60, 40, Qt.AlignCenter, "31")

        painter.end()
        return QIcon(pixmap)

    def _build_menu(self):
        """构建右键菜单"""
        menu = QMenu()

        # 打开主窗口
        show_action = QAction("打开管理界面", None)
        show_action.triggered.connect(self._on_show_main)
        menu.addAction(show_action)

        menu.addSeparator()

        # 退出
        quit_action = QAction("退出", None)
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        """托盘图标点击"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._on_show_main()
        elif reason == QSystemTrayIcon.Trigger:
            # 单击也打开（麒麟系统习惯）
            self._on_show_main()

    def _on_show_main(self):
        """显示主窗口"""
        if self.on_show_main:
            self.on_show_main()

    def _on_quit(self):
        """退出程序"""
        if self.on_quit:
            self.on_quit()