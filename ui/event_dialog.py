"""
添加/编辑事件对话框
"""
from datetime import date

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDateEdit, QComboBox, QPushButton, QGroupBox, QFormLayout,
    QSpinBox, QCheckBox, QColorDialog, QFontComboBox,
    QSlider, QMessageBox,
)
from PyQt5.QtGui import QColor


class EventDialog(QDialog):
    """添加/编辑倒数日事件对话框"""

    def __init__(self, parent=None, event_data: dict = None):
        super().__init__(parent)

        self.event_data = event_data or {}
        self._is_edit = bool(event_data)
        self._result_data = None

        self.setWindowTitle("编辑倒数日" if self._is_edit else "添加倒数日")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._init_ui()
        self._load_data()

    # ==================== UI 初始化 ====================

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # ---- 基本信息组 ----
        basic_group = QGroupBox("基本信息")
        basic_form = QFormLayout(basic_group)
        basic_form.setSpacing(8)

        # 标题
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("例如：春节、生日、考试倒计时...")
        basic_form.addRow("标题：", self.title_edit)

        # 目标日期
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(date.today())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        basic_form.addRow("目标日期：", self.date_edit)

        # 计数模式
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("倒计时（目标日期前）", "countdown")
        self.mode_combo.addItem("正计时（目标日期后）", "countup")
        basic_form.addRow("模式：", self.mode_combo)

        layout.addWidget(basic_group)

        # ---- 样式组 ----
        style_group = QGroupBox("显示样式")
        style_form = QFormLayout(style_group)
        style_form.setSpacing(8)

        # 字体
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFontComboBox().font())
        style_form.addRow("字体：", self.font_combo)

        # 标题字号
        self.title_size_spin = QSpinBox()
        self.title_size_spin.setRange(8, 72)
        self.title_size_spin.setValue(14)
        style_form.addRow("标题字号：", self.title_size_spin)

        # 天数字号
        self.days_size_spin = QSpinBox()
        self.days_size_spin.setRange(12, 200)
        self.days_size_spin.setValue(48)
        style_form.addRow("天数字号：", self.days_size_spin)

        # 时间字号
        self.time_size_spin = QSpinBox()
        self.time_size_spin.setRange(8, 72)
        self.time_size_spin.setValue(18)
        style_form.addRow("时间字号：", self.time_size_spin)

        # ---- 颜色选择 ----
        color_layout = QHBoxLayout()

        # 标题颜色
        self.title_color_btn = self._make_color_button("#888888", "标题颜色")
        color_layout.addWidget(QLabel("标题："))
        color_layout.addWidget(self.title_color_btn)

        # 天数颜色
        self.days_color_btn = self._make_color_button("#FF6B6B", "天数颜色")
        color_layout.addWidget(QLabel("天数："))
        color_layout.addWidget(self.days_color_btn)

        # 时间颜色
        self.time_color_btn = self._make_color_button("#FFFFFF", "时间颜色")
        color_layout.addWidget(QLabel("时间："))
        color_layout.addWidget(self.time_color_btn)

        color_layout.addStretch()
        style_form.addRow("颜色：", color_layout)

        # 背景颜色
        bg_layout = QHBoxLayout()
        self.bg_color_btn = self._make_color_button("transparent", "背景颜色")
        self.bg_opacity_slider = QSlider(Qt.Horizontal)
        self.bg_opacity_slider.setRange(0, 100)
        self.bg_opacity_slider.setValue(85)
        self.bg_opacity_label = QLabel("85%")
        self.bg_opacity_slider.valueChanged.connect(
            lambda v: self.bg_opacity_label.setText(f"{v}%")
        )

        bg_layout.addWidget(self.bg_color_btn)
        bg_layout.addWidget(QLabel("透明度："))
        bg_layout.addWidget(self.bg_opacity_slider)
        bg_layout.addWidget(self.bg_opacity_label)
        style_form.addRow("背景：", bg_layout)

        # 圆角
        self.border_radius_spin = QSpinBox()
        self.border_radius_spin.setRange(0, 50)
        self.border_radius_spin.setValue(12)
        style_form.addRow("圆角半径：", self.border_radius_spin)

        # 阴影
        shadow_layout = QHBoxLayout()
        self.shadow_check = QCheckBox("启用阴影")
        self.shadow_check.setChecked(True)
        self.shadow_check.toggled.connect(self._on_shadow_toggled)

        self.shadow_color_btn = self._make_color_button("rgba(0, 0, 0, 0.5)", "阴影颜色")
        shadow_layout.addWidget(self.shadow_check)
        shadow_layout.addWidget(self.shadow_color_btn)
        shadow_layout.addStretch()
        style_form.addRow("阴影：", shadow_layout)

        layout.addWidget(style_group)

        # ---- 高级选项 ----
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QVBoxLayout(advanced_group)

        self.always_on_top_check = QCheckBox("窗口置顶（始终显示在桌面前端）")
        self.always_on_top_check.setChecked(True)
        advanced_layout.addWidget(self.always_on_top_check)

        self.lock_check = QCheckBox("锁定位置（禁用拖动）")
        self.lock_check.setChecked(False)
        advanced_layout.addWidget(self.lock_check)

        layout.addWidget(advanced_group)

        # ---- 按钮 ----
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    # ==================== 数据加载 ====================

    def _load_data(self):
        """从现有事件数据加载到表单"""
        if not self._is_edit:
            return

        # 基本信息
        self.title_edit.setText(self.event_data.get("title", ""))

        target_date_str = self.event_data.get("target_date", "")
        if target_date_str:
            try:
                self.date_edit.setDate(date.fromisoformat(target_date_str))
            except ValueError:
                pass

        count_mode = self.event_data.get("count_mode", "countdown")
        self.mode_combo.setCurrentIndex(1 if count_mode == "countup" else 0)

        # 样式
        style = self.event_data.get("style", {})

        font_family = style.get("font_family", "Sans Serif")
        self.font_combo.setCurrentFont(QFontComboBox().font())
        # Fix font setting
        idx = self.font_combo.findText(font_family)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)

        self.title_size_spin.setValue(style.get("title_font_size", 14))
        self.days_size_spin.setValue(style.get("days_font_size", 48))
        self.time_size_spin.setValue(style.get("time_font_size", 18))

        self._set_color_button(self.title_color_btn, style.get("title_color", "#888888"))
        self._set_color_button(self.days_color_btn, style.get("days_color", "#FF6B6B"))
        self._set_color_button(self.time_color_btn, style.get("time_color", "#FFFFFF"))
        self._set_color_button(self.bg_color_btn, style.get("background_color", "transparent"))

        self.bg_opacity_slider.setValue(int(style.get("background_opacity", 0.85) * 100))
        self.border_radius_spin.setValue(style.get("border_radius", 12))

        self.shadow_check.setChecked(style.get("shadow_enabled", True))
        self._set_color_button(self.shadow_color_btn, style.get("shadow_color", "rgba(0, 0, 0, 0.5)"))

        self.always_on_top_check.setChecked(style.get("always_on_top", True))
        self.lock_check.setChecked(style.get("lock_position", False))

    # ==================== 事件处理 ====================

    def _on_shadow_toggled(self, checked):
        """阴影开关"""
        self.shadow_color_btn.setEnabled(checked)

    def _on_save(self):
        """保存事件"""
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "提示", "请输入事件标题")
            self.title_edit.setFocus()
            return

        target_date = self.date_edit.date().toPyDate()
        count_mode = self.mode_combo.currentData()

        self._result_data = {
            "title": title,
            "target_date": target_date.isoformat(),
            "count_mode": count_mode,
            "style": {
                "font_family": self.font_combo.currentFont().family(),
                "title_font_size": self.title_size_spin.value(),
                "days_font_size": self.days_size_spin.value(),
                "time_font_size": self.time_size_spin.value(),
                "title_color": self._get_color_button_text(self.title_color_btn),
                "days_color": self._get_color_button_text(self.days_color_btn),
                "time_color": self._get_color_button_text(self.time_color_btn),
                "background_color": self._get_color_button_text(self.bg_color_btn),
                "background_opacity": self.bg_opacity_slider.value() / 100.0,
                "border_radius": self.border_radius_spin.value(),
                "shadow_enabled": self.shadow_check.isChecked(),
                "shadow_color": self._get_color_button_text(self.shadow_color_btn),
                "shadow_radius": 15,
                "shadow_offset_x": 0,
                "shadow_offset_y": 4,
                "padding_horizontal": 24,
                "padding_vertical": 16,
                "always_on_top": self.always_on_top_check.isChecked(),
                "lock_position": self.lock_check.isChecked(),
            },
        }

        # 如果是编辑，保留原有位置信息
        if self._is_edit and "style" in self.event_data:
            old_style = self.event_data["style"]
            self._result_data["style"]["position_x"] = old_style.get("position_x", 100)
            self._result_data["style"]["position_y"] = old_style.get("position_y", 100)

        self.accept()

    def get_result(self) -> dict:
        """获取对话框结果"""
        return self._result_data

    # ==================== 颜色按钮辅助 ====================

    def _make_color_button(self, color: str, tooltip: str = "") -> QPushButton:
        """创建颜色选择按钮"""
        btn = QPushButton()
        btn.setFixedSize(30, 30)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._pick_color(btn))
        self._set_color_button(btn, color)
        return btn

    def _set_color_button(self, btn: QPushButton, color: str):
        """设置按钮颜色显示"""
        btn.setProperty("color", color)
        css_color = color
        if color == "transparent":
            css_color = "transparent"
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {css_color}; "
            f"border: 2px solid #666; border-radius: 4px; }}"
        )

    def _get_color_button_text(self, btn: QPushButton) -> str:
        """获取按钮代表的颜色字符串"""
        return btn.property("color") or "#FFFFFF"

    def _pick_color(self, btn: QPushButton):
        """打开取色器"""
        current = self._get_color_button_text(btn)
        if current == "transparent":
            # 使用全不透明黑色作为初始值，否则 QColorDialog 的 alpha 默认为 0，
            # 导致用户选了颜色但 alpha 仍为 0 → 被存回 "transparent" → 按钮/背景不更新
            initial = QColor(0, 0, 0, 255)
        else:
            initial = QColor(current)

        color = QColorDialog.getColor(
            initial, self, "选择颜色",
            QColorDialog.ShowAlphaChannel
        )

        if color.isValid():
            alpha = color.alpha()
            if alpha == 0:
                self._set_color_button(btn, "transparent")
            elif alpha < 255:
                a = alpha / 255.0
                self._set_color_button(
                    btn,
                    f"rgba({color.red()}, {color.green()}, {color.blue()}, {a:.2f})"
                )
            else:
                self._set_color_button(btn, color.name())
