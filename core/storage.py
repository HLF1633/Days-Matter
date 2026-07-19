"""
数据持久化管理 - 使用 JSON 文件存储事件和设置
"""
import json
import os
import uuid
from datetime import date
from typing import Optional


class Storage:
    """数据存储管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            # 默认使用 ~/.days_matter 目录
            config_dir = os.path.join(os.path.expanduser("~"), ".days_matter")

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")
        self._ensure_dir()
        self._data = self._load()

    def _ensure_dir(self):
        """确保配置目录存在"""
        os.makedirs(self.config_dir, exist_ok=True)

    def _load(self) -> dict:
        """从文件加载数据"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # 返回默认配置
        return {
            "events": [],
            "settings": {
                "language": "zh_CN",
                "auto_start": False,
                "first_run": True,
                "theme": "default",
            },
        }

    def save(self):
        """保存数据到文件"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # ---- 事件管理 ----

    def get_events(self) -> list:
        """获取所有事件"""
        return self._data.get("events", [])

    def get_event(self, event_id: str) -> Optional[dict]:
        """根据 ID 获取事件"""
        for event in self._data.get("events", []):
            if event["id"] == event_id:
                return event
        return None

    def add_event(self, event: dict) -> str:
        """添加事件，返回事件 ID"""
        if "id" not in event or not event["id"]:
            event["id"] = str(uuid.uuid4())[:8]
        if "style" not in event:
            event["style"] = self._default_style()
        if "created_at" not in event:
            event["created_at"] = date.today().isoformat()
        self._data.setdefault("events", []).append(event)
        self.save()
        return event["id"]

    def update_event(self, event_id: str, updates: dict) -> bool:
        """更新事件（深度合并，保留未修改的嵌套键）"""
        for i, event in enumerate(self._data.get("events", [])):
            if event["id"] == event_id:
                self._deep_merge(self._data["events"][i], updates)
                self.save()
                return True
        return False

    @staticmethod
    def _deep_merge(base: dict, updates: dict):
        """递归深度合并字典，嵌套字典合并而非替换"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Storage._deep_merge(base[key], value)
            else:
                base[key] = value

    def delete_event(self, event_id: str) -> bool:
        """删除事件"""
        events = self._data.get("events", [])
        for i, event in enumerate(events):
            if event["id"] == event_id:
                del events[i]
                self.save()
                return True
        return False

    def reorder_events(self, event_ids: list):
        """按给定顺序重排事件"""
        event_map = {e["id"]: e for e in self._data.get("events", [])}
        self._data["events"] = [event_map[eid] for eid in event_ids if eid in event_map]
        self.save()

    # ---- 设置管理 ----

    def get_settings(self) -> dict:
        """获取所有设置"""
        return self._data.get("settings", {})

    def get_setting(self, key: str, default=None):
        """获取单个设置"""
        return self._data.get("settings", {}).get(key, default)

    def set_setting(self, key: str, value):
        """设置单个设置"""
        self._data.setdefault("settings", {})[key] = value
        self.save()

    def set_settings(self, settings: dict):
        """批量设置"""
        self._data.setdefault("settings", {}).update(settings)
        self.save()

    # ---- 样式默认值 ----

    @staticmethod
    def _default_style() -> dict:
        """默认样式"""
        return {
            "font_family": "Sans Serif",
            "title_font_size": 14,
            "days_font_size": 48,
            "time_font_size": 18,
            "title_color": "#888888",
            "days_color": "#FF6B6B",
            "time_color": "#FFFFFF",
            "background_color": "rgba(0, 0, 0, 0.6)",
            "background_opacity": 1.0,
            "border_radius": 12,
            "border_width": 0,
            "border_color": "#555555",
            "shadow_enabled": True,
            "shadow_color": "rgba(0, 0, 0, 0.5)",
            "shadow_radius": 15,
            "shadow_offset_x": 0,
            "shadow_offset_y": 4,
            "padding_horizontal": 24,
            "padding_vertical": 16,
            "position_x": 100,
            "position_y": 100,
            "always_on_top": True,
            "show_on_all_desktops": True,
            "lock_position": False,
        }