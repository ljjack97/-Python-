"""工具栏 — 操作按钮和导出模式选择"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QToolBar, QAction, QLabel, QComboBox, QWidget,
    QHBoxLayout, QPushButton
)

from i18n.zh_CN import STRINGS
from ui.theme import ACCENT, ACCENT_HOVER


class MainToolbar(QToolBar):
    """主工具栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self._setup_actions()

    def _setup_actions(self):
        """设置工具栏按钮"""
        # 打开图像
        self.btn_open = QPushButton(STRINGS["btn_open_image"])
        self.btn_open.setShortcut("Ctrl+O")
        self.btn_open.setToolTip("打开图像 (Ctrl+O)")
        self.addWidget(self.btn_open)

        self.addSeparator()

        # 检测/取消（合并按钮）
        self.btn_detect = QPushButton(STRINGS["btn_detect"])
        self.btn_detect.setShortcut("Ctrl+D")
        self.btn_detect.setToolTip("检测特征 (Ctrl+D)")
        self.btn_detect.setEnabled(False)
        self.addWidget(self.btn_detect)

        # 预处理预览
        self.btn_preview = QPushButton("预处理预览")
        self.btn_preview.setToolTip("查看图像预处理后的二值化效果，帮助判断检测参数是否合适")
        self.btn_preview.setEnabled(False)
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #FF8F00;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #EF6C00; }
        """)
        self.addWidget(self.btn_preview)

        self.addSeparator()

        # 生成代码
        self.btn_generate = QPushButton(STRINGS["btn_generate"])
        self.btn_generate.setShortcut("Ctrl+G")
        self.btn_generate.setToolTip("生成代码 (Ctrl+G)")
        self.btn_generate.setEnabled(False)
        self.addWidget(self.btn_generate)

        self.addSeparator()

        # 导出模式 — 带明显下拉箭头
        self.addWidget(QLabel(STRINGS["lbl_export_mode"]))
        self.cmb_export_mode = QComboBox()
        self.cmb_export_mode.addItem("▼  " + STRINGS["mode_com"])
        self.cmb_export_mode.addItem("▼  " + STRINGS["mode_clipboard"])
        self.cmb_export_mode.addItem("▼  " + STRINGS["mode_file"])
        self.cmb_export_mode.setToolTip("选择导出方式")
        self.cmb_export_mode.setStyleSheet("""
            QComboBox {
                border: 2px solid #90CAF9;
                border-radius: 4px;
                padding: 4px 12px;
                background-color: white;
                min-width: 160px;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #1976D2;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #BBDEFB;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: #E3F2FD;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #BBDEFB;
                padding: 4px;
                selection-background-color: #E3F2FD;
                selection-color: #212121;
            }
        """)
        self.addWidget(self.cmb_export_mode)

        # 导出按钮
        self.btn_export = QPushButton(STRINGS["btn_export"])
        self.btn_export.setShortcut("Ctrl+E")
        self.btn_export.setToolTip("导出 (Ctrl+E)")
        self.btn_export.setEnabled(False)
        self.addWidget(self.btn_export)

        self.addSeparator()

        # 设置按钮
        self.btn_settings = QPushButton(STRINGS["btn_settings"])
        self.btn_settings.setShortcut("Ctrl+,")
        self.btn_settings.setToolTip("设置 (Ctrl+,)")
        self.addWidget(self.btn_settings)

        self.addSeparator()

        # 使用帮助按钮
        self.btn_help = QPushButton("使用说明")
        self.btn_help.setShortcut("F1")
        self.btn_help.setToolTip("查看详细使用说明书 (F1)")
        self.btn_help.setStyleSheet("""
            QPushButton {
                background-color: #43A047;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2E7D32;
            }
        """)
        self.addWidget(self.btn_help)

    def get_export_mode(self) -> int:
        """获取当前选择的导出模式索引

        Returns:
            0 = COM, 1 = Clipboard, 2 = File
        """
        return self.cmb_export_mode.currentIndex()
