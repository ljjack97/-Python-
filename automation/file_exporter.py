"""文件导出模式 — 保存 .scr 文件到磁盘"""

import os
from pathlib import Path

from automation.base_exporter import BaseExporter


class FileExporter(BaseExporter):
    """将 SCR 脚本保存为文件"""

    def __init__(self):
        self._last_path: str | None = None

    @property
    def last_path(self) -> str | None:
        return self._last_path

    def name(self) -> str:
        return "保存为 SCR 文件"

    def description(self) -> str:
        return "将生成的脚本保存为 .scr 文件，在 AutoCAD 中用 SCRIPT 命令加载"

    def export(self, scr_text: str, file_path: str | None = None) -> bool:
        """保存 SCR 文本到文件

        Args:
            scr_text: SCR 脚本文本
            file_path: 目标文件路径（为空则需要在调用前通过 UI 选择）

        Returns:
            是否保存成功
        """
        if file_path is None:
            return False

        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # 确保扩展名为 .scr
            if path.suffix.lower() != ".scr":
                path = path.with_suffix(".scr")

            # Binary mode: write \\n as-is without Windows CRLF conversion.
            # AutoCAD SCR treats both \\r and \\n as Enter — CRLF causes double-Enter
            # which breaks multi-option commands like -LAYER.
            with open(path, "wb") as f:
                f.write(scr_text.encode("ascii"))

            self._last_path = str(path)
            return True

        except (IOError, PermissionError) as e:
            raise IOError(f"无法保存文件: {e}")

    def export_to_temp(self, scr_text: str) -> str:
        """保存到临时文件并返回路径"""
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix=".scr", prefix="cad_script_")
        # Binary mode: no CRLF conversion
        with os.fdopen(fd, 'wb') as f:
            f.write(scr_text.encode("ascii"))
        self._last_path = temp_path
        return temp_path
