"""淡蓝色主题色板和 QSS 样式表"""

# === 色板定义 ===
PRIMARY = "#E3F2FD"          # 淡蓝色 - 主背景
PRIMARY_DARK = "#90CAF9"     # 中蓝 - 面板标题 / 分割条
ACCENT = "#1976D2"           # 蓝色 - 按钮 / 活动元素
ACCENT_HOVER = "#1565C0"     # 深蓝 - 按钮悬停
ACCENT_LIGHT = "#42A5F5"     # 亮蓝 - 次要强调
TEXT_PRIMARY = "#212121"     # 深灰 - 主文字
TEXT_SECONDARY = "#757575"   # 中灰 - 次要文字
TEXT_ON_ACCENT = "#FFFFFF"   # 白色 - 按钮文字
BORDER = "#BBDEFB"           # 浅蓝边框
PANEL_BG = "#FAFAFA"         # 近白 - 面板背景
STATUS_BAR_BG = "#BBDEFB"    # 状态栏背景
CODE_BG = "#F5F5F5"          # 代码区背景
OVERLAY_RED = "#FF1744"      # 叠加层 - 红色（墙体）
OVERLAY_BLUE = "#2979FF"     # 叠加层 - 蓝色（窗户）
OVERLAY_GREEN = "#00E676"    # 叠加层 - 绿色（树/圆）
OVERLAY_CYAN = "#00E5FF"     # 叠加层 - 青色（弧/水体）
OVERLAY_YELLOW = "#FFEA00"   # 叠加层 - 黄色（道路）

# === QSS 样式表 ===
STYLESHEET = f"""
/* 全局 */
QMainWindow {{
    background-color: {PANEL_BG};
}}

QWidget {{
    font-family: "Microsoft YaHei", "SimHei", "Segoe UI", sans-serif;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}

/* 工具栏 */
QToolBar {{
    background-color: {PRIMARY};
    border-bottom: 1px solid {BORDER};
    padding: 4px 8px;
    spacing: 6px;
}}

QToolBar QLabel {{
    color: {TEXT_PRIMARY};
    padding: 0 4px;
}}

/* 按钮 */
QPushButton {{
    background-color: {ACCENT};
    color: {TEXT_ON_ACCENT};
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton:pressed {{
    background-color: #0D47A1;
}}

QPushButton:disabled {{
    background-color: #BDBDBD;
    color: #757575;
}}

/* 下拉框 */
QComboBox {{
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 4px 8px;
    background-color: white;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {ACCENT};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid {BORDER};
}}

/* 分割器 */
QSplitter::handle {{
    background-color: {BORDER};
    width: 2px;
}}

QSplitter::handle:hover {{
    background-color: {ACCENT};
}}

/* 状态栏 */
QStatusBar {{
    background-color: {STATUS_BAR_BG};
    color: {TEXT_PRIMARY};
    border-top: 1px solid {BORDER};
    padding: 2px 8px;
}}

/* 滚动条 */
QScrollBar:vertical {{
    background-color: {PANEL_BG};
    width: 10px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {PRIMARY_DARK};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {ACCENT};
}}

QScrollBar:horizontal {{
    background-color: {PANEL_BG};
    height: 10px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {PRIMARY_DARK};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0px;
}}

/* 纯文本编辑区 */
QPlainTextEdit {{
    background-color: {CODE_BG};
    border: 1px solid {BORDER};
    border-radius: 3px;
    font-family: "Consolas", "Courier New", "Source Code Pro", monospace;
    font-size: 12px;
    padding: 8px;
    selection-background-color: {ACCENT};
    selection-color: white;
}}

/* 图形视图 */
QGraphicsView {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 3px;
}}

/* 标签页 */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 3px;
    background-color: {PANEL_BG};
}}

QTabBar::tab {{
    background-color: {PRIMARY};
    border: 1px solid {BORDER};
    border-bottom: none;
    padding: 6px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}

QTabBar::tab:selected {{
    background-color: white;
    border-bottom: 2px solid {ACCENT};
}}

QTabBar::tab:hover {{
    background-color: {PRIMARY_DARK};
}}

/* 滑条 */
QSlider::groove:horizontal {{
    height: 6px;
    background-color: {BORDER};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {ACCENT};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {ACCENT_HOVER};
}}

/* 菜单 */
QMenuBar {{
    background-color: {PRIMARY};
    border-bottom: 1px solid {BORDER};
    padding: 2px;
}}

QMenuBar::item:selected {{
    background-color: {ACCENT};
    color: white;
    border-radius: 3px;
}}

QMenu {{
    background-color: white;
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 0;
}}

QMenu::item {{
    padding: 6px 24px;
}}

QMenu::item:selected {{
    background-color: {PRIMARY};
}}

/* 对话框 */
QDialog {{
    background-color: {PANEL_BG};
}}

QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: {ACCENT};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}}
"""
