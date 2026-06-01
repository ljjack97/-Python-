"""设置对话框 — 检测参数 / 导出设置 / AutoCAD 版本"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QComboBox, QDialogButtonBox, QWidget,
    QLineEdit
)

from config.app_config import AppConfig
from i18n.zh_CN import STRINGS


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        self.setWindowTitle(STRINGS["dlg_settings_title"])
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # 标签页
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # === 检测参数页 ===
        self._tab_detection = QWidget()
        self._setup_detection_tab()
        self._tabs.addTab(self._tab_detection, STRINGS["settings_tab_detection"])

        # === 导出设置页 ===
        self._tab_export = QWidget()
        self._setup_export_tab()
        self._tabs.addTab(self._tab_export, STRINGS["settings_tab_export"])

        # === AutoCAD 版本页 ===
        self._tab_autocad = QWidget()
        self._setup_autocad_tab()
        self._tabs.addTab(self._tab_autocad, STRINGS["settings_tab_autocad"])

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _setup_detection_tab(self):
        """设置检测参数标签页"""
        layout = QVBoxLayout(self._tab_detection)

        # Canny 参数
        group_canny = QGroupBox(STRINGS["settings_canny_label"])
        form_canny = QFormLayout()
        self.spin_canny_low = QSpinBox()
        self.spin_canny_low.setRange(10, 200)
        form_canny.addRow(STRINGS["settings_canny_low"], self.spin_canny_low)
        self.spin_canny_high = QSpinBox()
        self.spin_canny_high.setRange(50, 500)
        form_canny.addRow(STRINGS["settings_canny_high"], self.spin_canny_high)
        group_canny.setLayout(form_canny)
        layout.addWidget(group_canny)

        # 霍夫直线参数
        group_hough = QGroupBox(STRINGS["settings_hough_line_label"])
        form_hough = QFormLayout()
        self.spin_hough_thresh = QSpinBox()
        self.spin_hough_thresh.setRange(10, 200)
        form_hough.addRow(STRINGS["settings_hough_threshold"], self.spin_hough_thresh)
        self.spin_hough_min_len = QSpinBox()
        self.spin_hough_min_len.setRange(5, 200)
        form_hough.addRow(STRINGS["settings_hough_min_length"], self.spin_hough_min_len)
        self.spin_hough_max_gap = QSpinBox()
        self.spin_hough_max_gap.setRange(2, 50)
        form_hough.addRow(STRINGS["settings_hough_max_gap"], self.spin_hough_max_gap)
        group_hough.setLayout(form_hough)
        layout.addWidget(group_hough)

        # LSD 参数
        group_lsd = QGroupBox("LSD 线段检测")
        form_lsd = QFormLayout()
        self.spin_lsd_len = QSpinBox()
        self.spin_lsd_len.setRange(5, 100)
        self.spin_lsd_len.setToolTip("小于此长度的线段被丢弃（值越大噪点越少）")
        form_lsd.addRow("最小线段长度 (px)", self.spin_lsd_len)
        group_lsd.setLayout(form_lsd)
        layout.addWidget(group_lsd)

        # 墙体参数
        group_wall = QGroupBox(STRINGS["settings_wall_label"])
        form_wall = QFormLayout()
        self.spin_wall_min = QDoubleSpinBox()
        self.spin_wall_min.setRange(50, 300)
        self.spin_wall_min.setSuffix(" mm")
        form_wall.addRow(STRINGS["settings_wall_thickness_min"], self.spin_wall_min)
        self.spin_wall_max = QDoubleSpinBox()
        self.spin_wall_max.setRange(200, 1000)
        self.spin_wall_max.setSuffix(" mm")
        form_wall.addRow(STRINGS["settings_wall_thickness_max"], self.spin_wall_max)
        group_wall.setLayout(form_wall)
        layout.addWidget(group_wall)

        layout.addStretch()

    def _setup_export_tab(self):
        """设置导出参数标签页"""
        layout = QVBoxLayout(self._tab_export)

        # AI settings
        group_ai = QGroupBox("AI 视觉识别")
        form_ai = QFormLayout()

        self.cmb_ai_provider = QComboBox()
        self.cmb_ai_provider.addItem("Step-3.5-Flash (阶跃，推荐)", "step")
        self.cmb_ai_provider.addItem("Qwen-VL-Max (通义千问)", "qwen")
        form_ai.addRow("模型:", self.cmb_ai_provider)

        self.edit_api_key = QLineEdit()
        self.edit_api_key.setPlaceholderText("输入 API Key (从对应平台获取)")
        self.edit_api_key.setEchoMode(QLineEdit.Password)
        form_ai.addRow("API Key:", self.edit_api_key)

        hint_ai = QLabel(
            "Step-2V: platform.stepfun.com → API Keys\n"
            "Qwen: dashscope.aliyun.com → API Key管理\n"
            "留空则使用OpenCV检测")
        hint_ai.setWordWrap(True)
        hint_ai.setStyleSheet("color: #757575; font-size: 11px;")
        form_ai.addRow(hint_ai)
        group_ai.setLayout(form_ai)
        layout.addWidget(group_ai)

        group_scale = QGroupBox(STRINGS["settings_scale_label"])
        form_scale = QFormLayout()
        self.spin_default_scale = QDoubleSpinBox()
        self.spin_default_scale.setRange(0.1, 100.0)
        self.spin_default_scale.setDecimals(2)
        self.spin_default_scale.setSuffix(" mm/像素")
        form_scale.addRow(STRINGS["settings_default_scale"], self.spin_default_scale)

        hint = QLabel(STRINGS["settings_scale_hint"])
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #757575; font-size: 11px;")
        form_scale.addRow(hint)
        group_scale.setLayout(form_scale)
        layout.addWidget(group_scale)

        layout.addStretch()

    def _setup_autocad_tab(self):
        """设置 AutoCAD 版本标签页"""
        layout = QVBoxLayout(self._tab_autocad)

        group_ver = QGroupBox(STRINGS["settings_autocad_version"])
        form_ver = QFormLayout()
        self.cmb_acad_ver = QComboBox()
        self.cmb_acad_ver.addItems(["2020", "2021", "2022", "2023", "2024", "2025"])
        form_ver.addRow(STRINGS["settings_autocad_version"], self.cmb_acad_ver)
        group_ver.setLayout(form_ver)
        layout.addWidget(group_ver)

        layout.addStretch()

    def _load_settings(self):
        """从配置对象加载当前设置到控件"""
        self.spin_canny_low.setValue(self.config.canny_low)
        self.spin_canny_high.setValue(self.config.canny_high)
        self.spin_hough_thresh.setValue(self.config.hough_line_threshold)
        self.spin_hough_min_len.setValue(self.config.hough_line_min_length)
        self.spin_hough_max_gap.setValue(self.config.hough_line_max_gap)
        self.spin_wall_min.setValue(self.config.wall_thickness_min_mm)
        self.spin_wall_max.setValue(self.config.wall_thickness_max_mm)
        self.spin_default_scale.setValue(self.config.default_scale_mm_per_px)
        self.spin_lsd_len.setValue(self.config.lsd_length_threshold)
        self.edit_api_key.setText(self.config.ai_api_key)
        i = self.cmb_ai_provider.findData(self.config.ai_provider)
        if i >= 0: self.cmb_ai_provider.setCurrentIndex(i)

        idx = self.cmb_acad_ver.findText(self.config.autocad_version)
        if idx >= 0:
            self.cmb_acad_ver.setCurrentIndex(idx)

    def _on_accept(self):
        """用户点击确定，保存设置到配置对象"""
        self.config.canny_low = self.spin_canny_low.value()
        self.config.canny_high = self.spin_canny_high.value()
        self.config.hough_line_threshold = self.spin_hough_thresh.value()
        self.config.hough_line_min_length = self.spin_hough_min_len.value()
        self.config.hough_line_max_gap = self.spin_hough_max_gap.value()
        self.config.wall_thickness_min_mm = self.spin_wall_min.value()
        self.config.wall_thickness_max_mm = self.spin_wall_max.value()
        self.config.default_scale_mm_per_px = self.spin_default_scale.value()
        self.config.lsd_length_threshold = self.spin_lsd_len.value()
        self.config.ai_api_key = self.edit_api_key.text().strip()
        self.config.ai_provider = self.cmb_ai_provider.currentData()
        self.config.autocad_version = self.cmb_acad_ver.currentText()
        self.accept()
