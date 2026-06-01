"""Clipboard export — save .scr to temp file, copy file PATH to clipboard."""

from pathlib import Path

from automation.base_exporter import BaseExporter
from automation.file_exporter import FileExporter


class ClipboardExporter(BaseExporter):
    """Export via clipboard.

    Strategy: save .scr to a temp file, then copy ONLY the file path
    to the clipboard.  The user pastes (Ctrl+V) into AutoCAD's file
    dialog after typing SCRIPT.
    """

    def __init__(self, temp_dir: str):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._file_exporter = FileExporter()
        self._last_path: str = ""

    def name(self) -> str:
        return "复制到剪贴板"

    def description(self) -> str:
        return "保存到临时文件，复制文件路径到剪贴板，在 AutoCAD 文件对话框中粘贴"

    def export(self, scr_text: str) -> bool:
        """Save to temp file, copy file PATH to clipboard.

        IMPORTANT: only the FILE PATH is copied, NOT the script content.
        This is because AutoCAD's SCRIPT command opens a file dialog
        where you need to paste a file path.
        """
        try:
            # Save SCR to a temp file
            temp_path = self._file_exporter.export_to_temp(scr_text)
            self._last_path = temp_path

            # Copy ONLY the file path to clipboard
            try:
                import pyperclip
                pyperclip.copy(temp_path)
            except Exception:
                # Fallback: try using Qt clipboard
                try:
                    from PyQt5.QtWidgets import QApplication
                    clipboard = QApplication.clipboard()
                    if clipboard:
                        clipboard.setText(temp_path)
                except Exception:
                    return False

            return True

        except Exception:
            return False

    def get_instructions(self) -> str:
        return (
            "===== 导出成功 =====\n\n"
            "文件路径已复制到剪贴板。\n\n"
            "【在 AutoCAD 中执行】\n"
            "1. 打开 AutoCAD\n"
            "2. 在命令行输入: SCRIPT 然后按回车\n"
            "3. 在弹出的文件对话框中按 Ctrl+V 粘贴文件路径\n"
            "4. 点击 [打开] 按钮\n"
            "5. AutoCAD 将自动执行所有绘图命令\n\n"
            f"文件路径: {self._last_path}\n\n"
            "====================="
        )

    @property
    def last_path(self) -> str:
        return self._last_path
