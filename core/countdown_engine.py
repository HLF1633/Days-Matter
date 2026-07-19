"""
倒数日计算引擎 - 支持倒计时和正计时
"""
from datetime import datetime, date
from typing import Tuple, Optional


class CountdownEngine:
    """倒数日核心计算引擎"""

    @staticmethod
    def calculate(target_date: date, count_mode: str = "countdown") -> dict:
        """
        计算目标日期的时间差

        Args:
            target_date: 目标日期
            count_mode: 计数模式 - "countdown"(倒计时) 或 "countup"(正计时)

        Returns:
            包含天、时、分、秒及总数值的字典
        """
        now = datetime.now()
        target_datetime = datetime.combine(target_date, datetime.min.time())

        if count_mode == "countdown":
            # 倒计时：目标时间 - 当前时间
            delta = target_datetime - now
        else:
            # 正计时：当前时间 - 目标时间
            delta = now - target_datetime

        total_seconds = delta.total_seconds()
        is_past = total_seconds < 0

        # 取绝对值进行计算
        abs_seconds = abs(int(total_seconds))
        days = abs_seconds // 86400
        hours = (abs_seconds % 86400) // 3600
        minutes = (abs_seconds % 3600) // 60
        seconds = abs_seconds % 60

        return {
            "delta": delta,
            "total_seconds": int(total_seconds),
            "abs_total_seconds": abs_seconds,
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "is_past": is_past,
            "is_today": days == 0 and not is_past and abs_seconds < 86400,
        }

    @staticmethod
    def get_display_text(result: dict, count_mode: str, show_seconds: bool = False) -> str:
        """
        根据计算结果生成显示文本

        Args:
            result: calculate() 返回的结果字典
            count_mode: 计数模式
            show_seconds: 是否显示秒数

        Returns:
            格式化后的显示文本
        """
        if result["is_today"] and count_mode == "countdown":
            return "今天"

        if show_seconds:
            return f"{result['days']}天 {result['hours']:02d}:{result['minutes']:02d}:{result['seconds']:02d}"
        else:
            return f"{result['days']}天 {result['hours']:02d}:{result['minutes']:02d}"

    @staticmethod
    def get_compact_text(result: dict, count_mode: str) -> str:
        """获取紧凑格式的显示文本（适合桌面小组件）"""
        if result["is_today"] and count_mode == "countdown":
            return "今天"

        prefix = "还有" if count_mode == "countdown" else "已经"
        suffix = "天" if count_mode == "countdown" else "天"

        if result["days"] > 0:
            return f"{prefix} {result['days']} {suffix.strip()}"
        elif result["days"] == 0:
            return f"{result['hours']:02d}:{result['minutes']:02d}:{result['seconds']:02d}"
        else:
            return "已完成" if count_mode == "countdown" else ""