"""
桌面悬浮倒数日组件 - 透明、可拖动、无边框、置顶窗口
兼容 Linux (麒麟/UKUI) 和 Windows
"""
import platform
from datetime import date

from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush,
    QMouseEvent, QPaintEvent, QEnterEvent,
    QFontDatabase,
)
from PyQt5.QtWidgets import QWidget, QApplication, QMenu, QAction

# 边缘标识常量
EDGE_NONE = 0
EDGE_LEFT = 1
EDGE_RIGHT = 2
EDGE_TOP = 4
EDGE_BOTTOM = 8

from core.countdown_engine import CountdownEngine

# 平台检测
IS_LINUX = platform.system() == "Linux"
IS_WINDOWS = platform.system() == "Windows"


class DesktopWidget(QWidget):
    """桌面悬浮倒数日显示组件"""

    # 阴影绘制边距（为自绘阴影留空间）
    SHADOW_MARGIN = 20

    def __init__(self, event_data: dict, storage, on_settings=None, on_delete=None):
        super().__init__(None)  # 显式指定无父窗口

        self.event_data = event_data
        self.storage = storage
        self.on_settings = on_settings
        self.on_delete = on_delete
        self.engine = CountdownEngine()

        # 拖动相关
        self._dragging = False
        self._drag_pos = QPoint()
        self._resizing = False
        self._resize_edge = EDGE_NONE
        self._resize_margin = 10

        # 计算结果缓存
        self._result = None
        self._display_text = ""

        # 是否已完全初始化并显示
        self._ready = False

        # 初始化 UI
        self._init_ui()
        self._apply_style()
        self._update_display()

        # 定时器 - 每秒更新
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_display)
        self._timer.start(1000)

    # ==================== 窗口初始化 ====================

    def _init_ui(self):
        """初始化窗口属性"""
        # 构建窗口标志
        flags = Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        if IS_LINUX:
            flags |= Qt.X11BypassWindowManagerHint

        self.setWindowFlags(flags)

        # 透明背景
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        # 启用鼠标追踪（用于 hover 效果和 resize cursor）
        self.setMouseTracking(True)

        # 使用 SHADOW_MARGIN 作为窗口边距，给自绘阴影留空间
        margin = self.SHADOW_MARGIN
        self.setContentsMargins(margin, margin, margin, margin)

        # 设置默认大小（内容区 + 阴影边距）
        self.resize(280 + margin * 2, 140 + margin * 2)
        self.setMinimumSize(120 + margin * 2, 60 + margin * 2)

        # 右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def showEvent(self, event):
        """窗口显示时标记为就绪"""
        super().showEvent(event)
        if not self._ready:
            self._ready = True

    # ==================== 样式应用 ====================

    def apply_style_from_event(self, event_data: dict):
        """从事件数据更新样式并重新渲染（由外部调用）"""
        self.event_data = event_data
        self._apply_style()
        self._update_display()
        self._ensure_visible()

    def _apply_style(self):
        """应用样式配置（位置、大小、置顶等）"""
        style = self.event_data.get("style", {})
        margin = self.SHADOW_MARGIN

        # 恢复保存的大小（如果存在）
        saved_w = style.get("widget_width")
        saved_h = style.get("widget_height")
        if saved_w and saved_h:
            self.resize(saved_w + margin * 2, saved_h + margin * 2)

        # 位置
        px = style.get("position_x", 100)
        py = style.get("position_y", 100)
        self.move(px, py)

        # 置顶切换
        self._sync_topmost(style)

        self.update()

    def _sync_topmost(self, style: dict):
        """同步置顶状态"""
        want_top = style.get("always_on_top", True)
        current_flags = self.windowFlags()
        is_top = bool(current_flags & Qt.WindowStaysOnTopHint)

        if want_top != is_top:
            # 构建新 flags
            new_flags = Qt.FramelessWindowHint | Qt.Tool
            if IS_LINUX:
                new_flags |= Qt.X11BypassWindowManagerHint
            if want_top:
                new_flags |= Qt.WindowStaysOnTopHint

            self.setWindowFlags(new_flags)
            # setWindowFlags 会隐藏窗口，需要重新显示
            self._ensure_visible()

    def _ensure_visible(self):
        """确保窗口可见（处理 setWindowFlags 后的隐藏状态）"""
        if not self.isVisible():
            self.show()
        # 在某些系统上，setWindowFlags 后窗口可能被移到屏幕外或 Z 序改变
        # 确保置顶窗口在前
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.raise_()

    # ==================== 内容更新 ====================

    def _update_display(self):
        """更新显示内容"""
        target_date_str = self.event_data.get("target_date", "")
        count_mode = self.event_data.get("count_mode", "countdown")

        try:
            target_date = date.fromisoformat(target_date_str)
        except (ValueError, TypeError):
            self._result = None
            self._display_text = "---"
            self.update()
            return

        self._result = self.engine.calculate(target_date, count_mode)
        self._display_text = self.engine.get_display_text(
            self._result, count_mode, show_seconds=True
        )
        self.update()

    # ==================== 绘制 ====================

    def _content_rect(self) -> QRectF:
        """返回内容区域矩形（相对于 widget 坐标系）"""
        m = self.SHADOW_MARGIN
        return QRectF(m, m, self.width() - m * 2, self.height() - m * 2)

    def paintEvent(self, event: QPaintEvent):
        """自定义绘制"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        style = self.event_data.get("style", {})

        m = self.SHADOW_MARGIN
        content_w = self.width() - m * 2
        content_h = self.height() - m * 2

        # 内容区域矩形（在 widget 坐标系中，留出阴影边距）
        content_rect = QRectF(m, m, content_w, content_h)
        border_radius = style.get("border_radius", 12)

        # ---- 绘制阴影（自绘，跨平台兼容） ----
        shadow_enabled = style.get("shadow_enabled", True)
        if shadow_enabled:
            shadow_color = self._parse_rgba(style.get("shadow_color", "rgba(0, 0, 0, 0.5)"))
            shadow_blur = style.get("shadow_radius", 15)
            offset_x = style.get("shadow_offset_x", 0)
            offset_y = style.get("shadow_offset_y", 4)

            # 分层绘制模糊阴影
            steps = max(1, shadow_blur // 2)
            for i in range(steps, 0, -1):
                expand = (shadow_blur - i * 2) * 0.5
                alpha_factor = i / steps * 0.3  # 外层 alpha 递减
                c = QColor(shadow_color)
                c.setAlpha(int(shadow_color.alpha() * alpha_factor))

                shadow_rect = QRectF(
                    content_rect.x() + offset_x - expand,
                    content_rect.y() + offset_y - expand,
                    content_rect.width() + expand * 2,
                    content_rect.height() + expand * 2,
                )
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(c))
                painter.drawRoundedRect(shadow_rect, border_radius + expand, border_radius + expand)

        # ---- 背景 ----
        bg_color = self._parse_rgba(style.get("background_color", "rgba(0, 0, 0, 0.6)"))
        bg_opacity = style.get("background_opacity", 0.85)

        # 如果用户选择了透明背景（alpha=0），使用默认半透明深色背景保证文字可读
        user_wants_transparent = bg_color.alpha() == 0
        if user_wants_transparent:
            bg_color = QColor(0, 0, 0, 153)  # rgba(0, 0, 0, 0.6)
            bg_opacity = 1.0
        elif bg_opacity == 0.0:
            # 用户选了颜色但透明度滑到了0%，使用默认85%不透明度
            bg_opacity = 0.85

        if bg_color.alpha() > 0:
            final_alpha = int(bg_color.alpha() * bg_opacity)
            if final_alpha <= 0:
                final_alpha = 1  # 至少保留1点alpha，确保有可见背景
            bg_color.setAlpha(final_alpha)
            painter.setBrush(QBrush(bg_color))

            border_width = style.get("border_width", 0)
            if border_width > 0:
                border_color = self._parse_rgba(style.get("border_color", "#555555"))
                painter.setPen(QPen(border_color, border_width))
            else:
                painter.setPen(Qt.NoPen)

            painter.drawRoundedRect(content_rect, border_radius, border_radius)

        # ---- 标题 ----
        pad_h = style.get("padding_horizontal", 24)
        pad_v = style.get("padding_vertical", 16)

        title = self.event_data.get("title", "倒数日")
        title_size = style.get("title_font_size", 14)
        title_font = self._create_font(style, title_size, QFont.Normal)
        painter.setFont(title_font)
        painter.setPen(QColor(style.get("title_color", "#888888")))

        title_x = m + pad_h
        title_y = m + pad_v
        title_rect = QRectF(title_x, title_y, content_w - pad_h * 2, title_size + 10)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

        # ---- 倒计时天数 ----
        days_size = style.get("days_font_size", 48)
        days_font = self._create_font(style, days_size, QFont.Bold)
        painter.setFont(days_font)
        painter.setPen(QColor(style.get("days_color", "#FF6B6B")))

        if self._result:
            days_text = str(self._result["days"])
        else:
            days_text = "--"

        days_y = title_y + title_size + 12
        days_rect = QRectF(title_x, days_y, content_w - pad_h * 2, days_size + 12)
        painter.drawText(days_rect, Qt.AlignLeft | Qt.AlignVCenter, days_text)

        # 在切换字体前，用 days_font 测量天数文字宽度
        days_text_width = painter.fontMetrics().width(days_text) + 8

        # "天" 单位文字
        unit_size = max(10, days_size // 3)
        unit_font = self._create_font(style, unit_size, QFont.Normal)
        painter.setFont(unit_font)
        painter.setPen(QColor(style.get("title_color", "#888888")))

        unit_x = title_x + days_text_width
        unit_rect = QRectF(unit_x, days_y, 60, days_size + 12)
        painter.drawText(unit_rect, Qt.AlignLeft | Qt.AlignVCenter, "天")

        # ---- 时分秒 ----
        if self._result:
            time_text = f"{self._result['hours']:02d}:{self._result['minutes']:02d}:{self._result['seconds']:02d}"
        else:
            time_text = "--:--:--"

        time_size = style.get("time_font_size", 18)
        time_font = self._create_font(style, time_size, QFont.Normal)
        painter.setFont(time_font)
        painter.setPen(QColor(style.get("time_color", "#FFFFFF")))

        time_y = days_y + days_size + 10
        time_rect = QRectF(title_x, time_y, content_w - pad_h * 2, time_size + 8)
        painter.drawText(time_rect, Qt.AlignLeft | Qt.AlignVCenter, time_text)

        painter.end()

    def _create_font(self, style: dict, size: int, weight: int) -> QFont:
        """创建字体，如果指定字体不可用则回退到系统默认字体"""
        family = style.get("font_family", "Sans Serif")

        # 检查字体是否可用
        available = QFontDatabase().families()
        if family not in available:
            # 回退到跨平台可用的中文字体
            fallbacks = ["Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC",
                         "WenQuanYi Micro Hei", "Arial", "Sans Serif"]
            for fb in fallbacks:
                if fb in available:
                    family = fb
                    break
            else:
                family = QFont().defaultFamily()

        font = QFont(family, size)
        font.setWeight(weight)
        return font

    # ==================== 鼠标交互 ====================

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        style = self.event_data.get("style", {})
        if style.get("lock_position", False):
            return

        if event.button() == Qt.LeftButton:
            edge = self._detect_edge(event.pos())
            if edge != EDGE_NONE:
                self._resizing = True
                self._resize_edge = edge
                self._drag_pos = event.globalPos()
                self._resize_geometry = self.geometry()
            else:
                self._dragging = True
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动"""
        if self._dragging:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        elif self._resizing:
            self._do_resize(event.globalPos())
            event.accept()
        else:
            self._update_cursor(event.pos())

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        if self._dragging:
            self._dragging = False
            pos = self.pos()
            self._save_position(pos.x(), pos.y())
        if self._resizing:
            self._resizing = False
            self._resize_edge = EDGE_NONE
            # 保存位置和大小
            pos = self.pos()
            self._save_position(pos.x(), pos.y())
            self._save_size(self.width(), self.height())
        self.setCursor(Qt.ArrowCursor)

    def enterEvent(self, event: QEnterEvent):
        """鼠标进入"""
        self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        """滚轮调整大小"""
        style = self.event_data.get("style", {})
        if style.get("lock_position", False):
            return

        delta = event.angleDelta().y() / 120
        margin = self.SHADOW_MARGIN
        new_w = max(120 + margin * 2, self.width() + int(delta * 10))
        new_h = max(60 + margin * 2, self.height() + int(delta * 5))
        self.resize(new_w, new_h)
        self._save_size(new_w, new_h)

    def _detect_edge(self, pos: QPoint) -> int:
        """检测鼠标所在边缘/角，返回边缘标识组合"""
        m = self._resize_margin
        w, h = self.width(), self.height()
        edge = EDGE_NONE

        if pos.x() <= m:
            edge |= EDGE_LEFT
        elif pos.x() >= w - m:
            edge |= EDGE_RIGHT

        if pos.y() <= m:
            edge |= EDGE_TOP
        elif pos.y() >= h - m:
            edge |= EDGE_BOTTOM

        return edge

    def _update_cursor(self, pos: QPoint):
        """根据鼠标位置更新光标形状"""
        edge = self._detect_edge(pos)

        if edge == EDGE_LEFT or edge == EDGE_RIGHT:
            self.setCursor(Qt.SizeHorCursor)
        elif edge == EDGE_TOP or edge == EDGE_BOTTOM:
            self.setCursor(Qt.SizeVerCursor)
        elif edge == (EDGE_LEFT | EDGE_TOP) or edge == (EDGE_RIGHT | EDGE_BOTTOM):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge == (EDGE_RIGHT | EDGE_TOP) or edge == (EDGE_LEFT | EDGE_BOTTOM):
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def _do_resize(self, global_pos: QPoint):
        """根据拖动的边缘/角计算并应用新尺寸和位置"""
        delta = global_pos - self._drag_pos
        margin = self.SHADOW_MARGIN
        edge = self._resize_edge
        geo = self._resize_geometry

        min_w = 120 + margin * 2
        min_h = 60 + margin * 2

        new_x = geo.x()
        new_y = geo.y()
        new_w = geo.width()
        new_h = geo.height()

        if edge & EDGE_LEFT:
            proposed_w = geo.width() - delta.x()
            if proposed_w >= min_w:
                new_x = geo.x() + delta.x()
                new_w = proposed_w
            else:
                new_w = min_w
                new_x = geo.x() + geo.width() - min_w

        if edge & EDGE_RIGHT:
            new_w = max(min_w, geo.width() + delta.x())

        if edge & EDGE_TOP:
            proposed_h = geo.height() - delta.y()
            if proposed_h >= min_h:
                new_y = geo.y() + delta.y()
                new_h = proposed_h
            else:
                new_h = min_h
                new_y = geo.y() + geo.height() - min_h

        if edge & EDGE_BOTTOM:
            new_h = max(min_h, geo.height() + delta.y())

        self.setGeometry(new_x, new_y, new_w, new_h)

    def _save_position(self, x: int, y: int):
        """保存位置到存储"""
        style = self.event_data.get("style", {}).copy()
        style["position_x"] = x
        style["position_y"] = y
        self.storage.update_event(self.event_data["id"], {"style": style})

    def _save_size(self, width: int, height: int):
        """保存窗口大小到存储"""
        style = self.event_data.get("style", {}).copy()
        margin = self.SHADOW_MARGIN
        style["widget_width"] = width - margin * 2
        style["widget_height"] = height - margin * 2
        self.storage.update_event(self.event_data["id"], {"style": style})

    # ==================== 右键菜单 ====================

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)

        edit_action = QAction("编辑事件...", self)
        edit_action.triggered.connect(self._on_edit)
        menu.addAction(edit_action)

        style = self.event_data.get("style", {})
        locked = style.get("lock_position", False)
        lock_action = QAction("解锁位置" if locked else "锁定位置", self)
        lock_action.triggered.connect(self._toggle_lock)
        menu.addAction(lock_action)

        on_top = style.get("always_on_top", True)
        top_action = QAction("取消置顶" if on_top else "窗口置顶", self)
        top_action.triggered.connect(self._toggle_on_top)
        menu.addAction(top_action)

        menu.addSeparator()

        settings_action = QAction("全局设置...", self)
        settings_action.triggered.connect(lambda: self.on_settings and self.on_settings())
        menu.addAction(settings_action)

        menu.addSeparator()
        delete_action = QAction("删除此事件", self)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)

        menu.exec_(self.mapToGlobal(pos))

    def _on_edit(self):
        """编辑事件回调"""
        if self.on_settings:
            self.on_settings(self.event_data.get("id"))

    def _toggle_lock(self):
        """切换锁定"""
        style = self.event_data.get("style", {}).copy()
        style["lock_position"] = not style.get("lock_position", False)
        self.storage.update_event(self.event_data["id"], {"style": style})
        self.event_data["style"] = style
        self._ensure_visible()

    def _toggle_on_top(self):
        """切换置顶"""
        style = self.event_data.get("style", {}).copy()
        style["always_on_top"] = not style.get("always_on_top", True)
        self.storage.update_event(self.event_data["id"], {"style": style})
        self.event_data["style"] = style
        self._apply_style()
        self._ensure_visible()

    def _on_delete(self):
        """删除事件"""
        if self.on_delete:
            self.on_delete(self.event_data.get("id"))

    # ==================== 工具方法 ====================

    @staticmethod
    def _parse_rgba(color_str: str) -> QColor:
        """解析 RGBA 颜色字符串"""
        color_str = color_str.strip().lower()

        if color_str == "transparent":
            return QColor(0, 0, 0, 0)

        if color_str.startswith("rgba("):
            color_str = color_str[5:-1]
            parts = [x.strip() for x in color_str.split(",")]
            if len(parts) == 4:
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                a = int(float(parts[3]) * 255)
                return QColor(r, g, b, a)

        if color_str.startswith("#"):
            color_str = color_str[1:]
            if len(color_str) == 6:
                r, g, b = int(color_str[0:2], 16), int(color_str[2:4], 16), int(color_str[4:6], 16)
                return QColor(r, g, b)
            elif len(color_str) == 8:
                r, g, b = int(color_str[0:2], 16), int(color_str[2:4], 16), int(color_str[4:6], 16)
                a = int(color_str[6:8], 16)
                return QColor(r, g, b, a)

        return QColor(color_str)