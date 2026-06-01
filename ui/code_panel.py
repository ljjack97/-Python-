"""代码显示面板 — 显示生成的 SCR 代码，带语法高亮"""

from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont,
    QFontDatabase
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QLabel, QPushButton
)

from ui.theme import (
    CODE_BG, ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ON_ACCENT
)


class ScrHighlighter(QSyntaxHighlighter):
    """SCR 脚本语法高亮器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_formats()
        self._init_rules()

    def _init_formats(self):
        """初始化各种格式"""
        # 注释 (以 ; 开头)
        self.fmt_comment = QTextCharFormat()
        self.fmt_comment.setForeground(QColor("#6A9955"))
        self.fmt_comment.setFontItalic(True)

        # AutoCAD 命令
        self.fmt_command = QTextCharFormat()
        self.fmt_command.setForeground(QColor("#0000FF"))
        self.fmt_command.setFontWeight(QFont.Bold)

        # 坐标
        self.fmt_coord = QTextCharFormat()
        self.fmt_coord.setForeground(QColor("#098658"))

        # 数字
        self.fmt_number = QTextCharFormat()
        self.fmt_number.setForeground(QColor("#098658"))

        # 图层名
        self.fmt_layer = QTextCharFormat()
        self.fmt_layer.setForeground(QColor("#A31515"))

        # 引号内字符串
        self.fmt_string = QTextCharFormat()
        self.fmt_string.setForeground(QColor("#A31515"))

    def _init_rules(self):
        """初始化高亮规则"""
        self.rules = []

        # AutoCAD 命令（大写单词，常见命令）
        commands = [
            "LINE", "CIRCLE", "ARC", "PLINE", "RECTANG", "RECTANGLE",
            "HATCH", "-HATCH", "LAYER", "-LAYER", "INSERT", "-INSERT",
            "TEXT", "-TEXT", "DIMLINEAR", "DIMALIGNED",
            "ZOOM", "PAN", "SCRIPT", "SETVAR", "OSNAPCOORD",
            "OSMODE", "ORTHOMODE", "CMDECHO",
            "W", "C", "S", "N", "E", "P", "L", "A", "D",
        ]
        for cmd in commands:
            pattern = f"\\b{cmd}\\b"
            self.rules.append((QRegExp(pattern), self.fmt_command))

    def highlightBlock(self, text: str):
        """高亮文本块"""
        # 检查是否为注释
        stripped = text.strip()
        if stripped.startswith(";"):
            self.setFormat(0, len(text), self.fmt_comment)
            return

        # 应用命令高亮规则
        for pattern, fmt in self.rules:
            index = pattern.indexIn(text, 0)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)

        # 高亮坐标 (x,y 格式)
        coord_pattern = QRegExp(r"\b\d+\.?\d*,\d+\.?\d*\b")
        index = coord_pattern.indexIn(text, 0)
        while index >= 0:
            length = coord_pattern.matchedLength()
            self.setFormat(index, length, self.fmt_coord)
            index = coord_pattern.indexIn(text, index + length)

        # 高亮引号内文本
        in_quote = False
        quote_start = 0
        for i, ch in enumerate(text):
            if ch == '"':
                if in_quote:
                    self.setFormat(quote_start, i - quote_start + 1, self.fmt_string)
                    in_quote = False
                else:
                    quote_start = i
                    in_quote = True
        if in_quote:
            self.setFormat(quote_start, len(text) - quote_start, self.fmt_string)


class CodePanel(QWidget):
    """代码显示面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Title bar
        title_bar = QHBoxLayout()
        self._title = QLabel("生成代码")
        self._title.setStyleSheet(
            f"color: {ACCENT}; font-weight: bold; font-size: 14px; padding: 4px 8px;"
            f"background-color: #E3F2FD; border-bottom: 1px solid #BBDEFB;"
        )
        title_bar.addWidget(self._title)
        title_bar.addStretch()

        # Copy code button
        self._btn_copy = QPushButton("复制代码")
        self._btn_copy.setToolTip("复制代码内容到剪贴板（注意：不能直接粘贴到AutoCAD命令行，需保存为.scr文件后通过SCRIPT命令加载）")
        self._btn_copy.setFixedHeight(26)
        self._btn_copy.clicked.connect(self._on_copy_code)
        self._btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #616161; }}
        """)
        self._btn_copy.setEnabled(False)
        title_bar.addWidget(self._btn_copy)
        layout.addLayout(title_bar)

        # Code editor
        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setFont(QFont("Consolas", 10))
        self._editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {CODE_BG};
                border: 1px solid #BBDEFB;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', 'Source Code Pro', monospace;
                font-size: 12px;
                padding: 8px;
            }}
        """)
        self._highlighter = ScrHighlighter(self._editor.document())
        self._editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(self._editor, 1)

        # Bottom bar: stats + warning
        bottom_bar = QHBoxLayout()
        self._stats = QLabel("")
        self._stats.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; padding: 2px 8px;"
        )
        bottom_bar.addWidget(self._stats)
        bottom_bar.addStretch()

        self._warning = QLabel(
            "请使用 [导出] 保存为 .scr 文件，在 AutoCAD 中用 SCRIPT 命令加载"
        )
        self._warning.setStyleSheet(
            "color: #E65100; font-size: 10px; padding: 2px 8px; font-style: italic;"
        )
        bottom_bar.addWidget(self._warning)
        layout.addLayout(bottom_bar)

    def set_code(self, scr_text: str):
        self._editor.setPlainText(scr_text)
        line_count = scr_text.count('\n') + 1
        self._stats.setText(f"共 {line_count} 行")
        self._btn_copy.setEnabled(True)

    def get_code(self) -> str:
        return self._editor.toPlainText()

    def clear(self):
        self._editor.clear()
        self._stats.setText("")
        self._btn_copy.setEnabled(False)

    def _on_copy_code(self):
        """Copy code content to clipboard with a warning."""
        self._editor.selectAll()
        self._editor.copy()
        cursor = self._editor.textCursor()
        cursor.clearSelection()
        self._editor.setTextCursor(cursor)
        self._stats.setText("已复制到剪贴板（注意：需保存为.scr文件，通过SCRIPT命令加载，不能直接粘贴到AutoCAD命令行！）")
