"""CAD 图像转代码工具 — 程序入口

用法:
    python main.py

依赖安装:
    pip install -r requirements.txt
"""

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from config.app_config import AppConfig
from ui.main_window import MainWindow


def main():
    """主函数"""
    # 高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("CAD Image to Code")
    app.setOrganizationName("CADTools")

    # 加载配置
    config = AppConfig()
    config.ensure_dirs()
    config.load()

    # 创建主窗口
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
