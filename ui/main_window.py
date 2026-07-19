"""
主设置窗口 - 事件管理和全局设置
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QCheckBox, QMessageBox, QFrame, QMenu, QAction,
    QApplication,
)
from PyQt5.QtGui import QIcon, QFont, QColor

from core.storage import Storage
from ui.event_dialog import EventDialog


class MainWindow(QMainWindow):
    """主设置窗口"""

    def __init__(self, storage: Storage, on_event_changed=None):
        super().__init__()

        self.storage = storage
        self.on_event_changed = on_event_changed
        self.desktop_widgets = {}  # event_id -> DesktopWidget

        self.setWindowTitle("倒数日 - 事件管理")
        self.setMinimumSize(640, 480)
        self.resize(700, 550)

        # 居中显示
        self._center_on_screen()

        self._init_ui()
        self._refresh_list()

    def _center_on_screen(self):
        """将窗口居中"""
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _init_ui(self):
        """初始化界面"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # ---- 标题栏 ----
        title_layout = QHBoxLayout()
        title_label = QLabel("📅 我的倒数日")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        add_btn = QPushButton("+ 添加倒数日")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_btn.clicked.connect(self._on_add_event)
        title_layout.addWidget(add_btn)
        main_layout.addLayout(title_layout)

        # ---- 事件列表 ----
        list_frame = QFrame()
        list_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(4, 4, 4, 4)

        list_header = QLabel("事件列表（双击编辑，右键菜单操作）")
        list_header.setStyleSheet("color: #888; font-size: 12px;")
        list_layout.addWidget(list_header)

        self.event_list = QListWidget()
        self.event_list.setAlternatingRowColors(True)
        self.event_list.setSpacing(2)
        self.event_list.itemDoubleClicked.connect(self._on_edit_event)
        self.event_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.event_list.customContextMenuRequested.connect(self._show_list_context_menu)
        self.event_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fafafa;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f5e9;
            }
        """)
        list_layout.addWidget(self.event_list)
        main_layout.addWidget(list_frame, 1)

        # ---- 全局设置 ----
        settings_group = QGroupBox("全局设置")
        settings_layout = QVBoxLayout(settings_group)

        self.auto_start_check = QCheckBox("开机自动启动")
        self.auto_start_check.setChecked(self.storage.get_setting("auto_start", False))
        self.auto_start_check.toggled.connect(self._on_auto_start_toggled)
        settings_layout.addWidget(self.auto_start_check)

        self.show_all_check = QCheckBox("显示所有悬浮窗口")
        self.show_all_check.setChecked(True)
        self.show_all_check.toggled.connect(self._on_show_all_toggled)
        settings_layout.addWidget(self.show_all_check)

        main_layout.addWidget(settings_group)

        # ---- 底部按钮 ----
        bottom_layout = QHBoxLayout()

        help_btn = QPushButton("使用说明")
        help_btn.clicked.connect(self._on_help)
        bottom_layout.addWidget(help_btn)

        bottom_layout.addStretch()

        quit_btn = QPushButton("退出程序")
        quit_btn.setStyleSheet("color: #d32f2f;")
        quit_btn.clicked.connect(self._on_quit)
        bottom_layout.addWidget(quit_btn)

        main_layout.addLayout(bottom_layout)

    # ==================== 事件列表 ====================

    def _refresh_list(self):
        """刷新事件列表"""
        self.event_list.clear()
        events = self.storage.get_events()

        for event in events:
            title = event.get("title", "未命名")
            target_date = event.get("target_date", "")
            count_mode = event.get("count_mode", "countdown")
            mode_label = "倒数" if count_mode == "countdown" else "正计"

            item_text = f"{title}  ·  {target_date}  ·  {mode_label}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, event["id"])
            item.setToolTip(f"目标日期: {target_date}\n模式: {mode_label}")
            self.event_list.addItem(item)

        # 空状态提示
        if not events:
            empty_item = QListWidgetItem("还没有倒数日事件，点击右上角「添加倒数日」开始吧！")
            empty_item.setFlags(Qt.NoItemFlags)  # 不可选中
            empty_item.setForeground(QColor("#999"))
            self.event_list.addItem(empty_item)

    # ==================== 事件操作 ====================

    def _on_add_event(self):
        """添加事件"""
        dialog = EventDialog(self)
        if dialog.exec_() == EventDialog.Accepted:
            data = dialog.get_result()
            event_id = self.storage.add_event(data)
            self._refresh_list()
            self._notify_change("added", event_id)

    def _on_edit_event(self, item: QListWidgetItem):
        """编辑事件"""
        event_id = item.data(Qt.UserRole)
        if not event_id:
            return

        event = self.storage.get_event(event_id)
        if not event:
            return

        dialog = EventDialog(self, event_data=event)
        if dialog.exec_() == EventDialog.Accepted:
            data = dialog.get_result()
            self.storage.update_event(event_id, data)
            self._refresh_list()
            self._notify_change("updated", event_id)

    def _show_list_context_menu(self, pos):
        """列表右键菜单"""
        item = self.event_list.itemAt(pos)
        if not item:
            return

        event_id = item.data(Qt.UserRole)
        if not event_id:
            return

        menu = QMenu(self)

        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(lambda: self._on_edit_event(item))
        menu.addAction(edit_action)

        menu.addSeparator()

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._on_delete_event(event_id))
        menu.addAction(delete_action)

        menu.exec_(self.event_list.mapToGlobal(pos))

    def _on_delete_event(self, event_id: str):
        """删除事件"""
        event = self.storage.get_event(event_id)
        title = event.get("title", "未知") if event else "未知"

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除「{title}」吗？\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.storage.delete_event(event_id)
            self._refresh_list()
            self._notify_change("deleted", event_id)

    # ==================== 全局设置 ====================

    def _on_auto_start_toggled(self, checked):
        """开机自启切换"""
        self.storage.set_setting("auto_start", checked)
        # 实际的 autostart 文件由 integration 模块处理
        if self.on_event_changed:
            self.on_event_changed("autostart", None)

    def _on_show_all_toggled(self, checked):
        """显示/隐藏所有悬浮窗口"""
        if self.on_event_changed:
            self.on_event_changed("show_all" if checked else "hide_all", None)

    def _on_help(self):
        """显示帮助"""
        QMessageBox.information(
            self, "使用说明",
            "📅 倒数日 - 使用说明\n\n"
            "添加事件：\n"
            "  点击右上角「+ 添加倒数日」按钮\n\n"
            "编辑事件：\n"
            "  双击事件列表中的项目，或右键选择「编辑」\n\n"
            "桌面悬浮窗：\n"
            "  - 拖动：左键按住拖动\n"
            "  - 缩放：鼠标悬停右下角拖动或使用滚轮\n"
            "  - 右键菜单：编辑、锁定位置、置顶切换\n\n"
            "开机自启：\n"
            "  勾选「开机自动启动」后，系统将在登录时自动运行\n\n"
            "关闭程序：\n"
            "  点击「退出程序」按钮，或通过系统托盘退出",
        )

    def _on_quit(self):
        """退出程序"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出倒数日吗？\n所有悬浮窗口将被关闭。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            QApplication.quit()

    # ==================== 通知 ====================

    def _notify_change(self, action: str, event_id: str):
        """通知外部事件变更"""
        if self.on_event_changed:
            self.on_event_changed(action, event_id)

    def closeEvent(self, event):
        """关闭窗口时最小化到托盘而非退出"""
        event.ignore()
        self.hide()