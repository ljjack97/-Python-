"""导出器抽象基类"""

from abc import ABC, abstractmethod


class BaseExporter(ABC):
    """所有导出模式的抽象基类"""

    @abstractmethod
    def export(self, scr_text: str) -> bool:
        """执行导出

        Args:
            scr_text: 完整的 .scr 脚本文本

        Returns:
            导出是否成功
        """
        ...

    @abstractmethod
    def name(self) -> str:
        """导出模式的人类可读名称"""
        ...

    @abstractmethod
    def description(self) -> str:
        """导出模式的说明"""
        ...
