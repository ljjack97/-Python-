"""Main window — assembles all UI components and coordinates modules."""

import os
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QSplitter, QStatusBar, QMessageBox,
    QFileDialog, QApplication
)

from config.app_config import AppConfig
from core.image_loader import ImageLoader
from i18n.zh_CN import STRINGS
from ui.theme import STYLESHEET
from ui.image_panel import ImagePanel
from ui.code_panel import CodePanel
from ui.toolbar import MainToolbar
from ui.settings_dialog import SettingsDialog
from ui.help_dialog import HelpDialog
from ui.workers import DetectionWorker, CodegenWorker
from automation.file_exporter import FileExporter
from automation.clipboard_exporter import ClipboardExporter
from automation.com_exporter import ComExporter


class MainWindow(QMainWindow):
    """CAD Image to Code — main application window."""

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.config.ensure_dirs()

        # Modules
        self._image_loader = ImageLoader(config)
        self._geometry_list = []
        self._scale_factor = config.default_scale_mm_per_px
        self._scr_text = ""

        # Exporters
        self._file_exporter = FileExporter()
        self._clipboard_exporter = ClipboardExporter(config.temp_dir)
        self._com_exporter = ComExporter(config)

        # Worker references
        self._detect_worker: Optional[DetectionWorker] = None
        self._codegen_worker: Optional[CodegenWorker] = None

        # Preview state
        self._saved_original_img = None  # Preserved original for preview return
        self._saved_selection = None      # Preserved selection across preview toggle
        self._preview_mode = False
        self._detecting = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setWindowTitle(STRINGS["app_title"])
        self.resize(1200, 800)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(STYLESHEET)

        # Toolbar
        self._toolbar = MainToolbar(self)
        self.addToolBar(self._toolbar)

        # Splitter: image (70%) | code (30%)
        self._splitter = QSplitter(Qt.Horizontal)
        self._image_panel = ImagePanel()
        self._code_panel = CodePanel()
        self._splitter.addWidget(self._image_panel)
        self._splitter.addWidget(self._code_panel)
        self._splitter.setStretchFactor(0, 7)
        self._splitter.setStretchFactor(1, 3)
        self.setCentralWidget(self._splitter)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage(STRINGS["status_ready"])

    def _connect_signals(self):
        self._toolbar.btn_open.clicked.connect(self._on_open_image)
        self._toolbar.btn_detect.clicked.connect(self._on_detect_click)
        self._toolbar.btn_preview.clicked.connect(self._on_preview)
        self._toolbar.btn_generate.clicked.connect(self._on_generate)
        self._toolbar.btn_export.clicked.connect(self._on_export)
        self._toolbar.btn_settings.clicked.connect(self._on_settings)
        self._toolbar.btn_help.clicked.connect(self._on_help)

    # === Toolbar actions ===

    def _on_open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, STRINGS["dlg_open_image"], "",
            STRINGS["dlg_image_filter"])

        if not file_path:
            return

        try:
            self._status_bar.showMessage(STRINGS["status_loading"])
            QApplication.processEvents()

            img, (w, h) = self._image_loader.load(file_path)
            self._image_panel.display_image(img)
            self._saved_original_img = img.copy()
            self._preview_mode = False

            self._toolbar.btn_detect.setEnabled(True)
            self._toolbar.btn_preview.setEnabled(True)
            self._update_preview_button()
            self._toolbar.btn_generate.setEnabled(False)
            self._toolbar.btn_export.setEnabled(False)

            self._geometry_list = []
            self._scr_text = ""
            self._code_panel.clear()

            self._status_bar.showMessage(
                f"已加载: {Path(file_path).name} ({w} x {h})")

        except FileNotFoundError:
            QMessageBox.critical(self, "错误", f"文件不存在: {file_path}")
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误",
                STRINGS["err_load_image"].format(error=str(e)))

    def _on_detect_click(self):
        """Handle detect button: start or cancel depending on state."""
        if self._detecting:
            if self._detect_worker and self._detect_worker.isRunning():
                self._detect_worker.cancel()
            return
        self._on_detect()

    def _on_detect(self):
        if not self._image_panel.has_image:
            QMessageBox.warning(self, "提示", STRINGS["err_no_image"])
            return

        img = self._saved_original_img
        if img is None:
            img = self._image_panel._original_img
        if img is None:
            return

        w_full, h_full = img.shape[1], img.shape[0]

        region = self._image_panel.get_selected_region() or (
            (int(self._image_panel._view._selection_scene.x()),
             int(self._image_panel._view._selection_scene.y()),
             int(self._image_panel._view._selection_scene.width()),
             int(self._image_panel._view._selection_scene.height()))
            if self._image_panel._view._selection_scene and
               self._image_panel._view._selection_scene.width() > 5 else None)

        if region is not None:
            x, y, w, h = region
            img = img[y:y+h, x:x+w]

        self._set_detecting_state(True)
        self._detect_worker = DetectionWorker(img, self.config)
        self._detect_worker.progress.connect(self._status_bar.showMessage)
        self._detect_worker.finished.connect(self._on_detect_finished)
        self._detect_worker.finished_scr.connect(self._on_detect_scr_ready)
        self._detect_worker.error.connect(self._on_detect_error)
        self._detect_worker.cancelled.connect(self._on_detect_cancelled)
        self._detect_worker.start()

    def _set_detecting_state(self, detecting: bool):
        self._detecting = detecting
        if detecting:
            self._toolbar.btn_detect.setText("取消检测")
            self._toolbar.btn_detect.setStyleSheet("""
                QPushButton { background-color: #D32F2F; color: white; border: none;
                border-radius: 4px; padding: 6px 16px; font-weight: bold; }
                QPushButton:hover { background-color: #B71C1C; }
            """)
        else:
            self._toolbar.btn_detect.setText(STRINGS["btn_detect"])
            self._toolbar.btn_detect.setStyleSheet("")
        self._toolbar.btn_open.setEnabled(not detecting)
        self._toolbar.btn_preview.setEnabled(not detecting)

    def _on_detect_cancelled(self):
        self._set_detecting_state(False)
        self._status_bar.showMessage("检测已取消", 3000)

    def _on_detect_scr_ready(self, scr_text: str):
        """DualAI returned direct SCR — skip code generation."""
        self._set_detecting_state(False)
        self._scr_text = scr_text
        self._code_panel.set_code(scr_text)
        self._toolbar.btn_open.setEnabled(True)
        self._toolbar.btn_export.setEnabled(True)
        self._status_bar.showMessage(
            f"DualAI 完成: {scr_text.count(chr(10))} 行 SCR 代码")

    def _on_detect_finished(self, geometry_list, scale_factor: float):
        self._set_detecting_state(False)
        self._geometry_list = geometry_list
        self._scale_factor = scale_factor
        self._image_panel.set_overlay(geometry_list)

        from core.geometry import Wall, Door, Window, TreeSymbol, Circle2D
        walls = sum(1 for g in geometry_list if isinstance(g, Wall))
        doors = sum(1 for g in geometry_list if isinstance(g, Door))
        windows = sum(1 for g in geometry_list if isinstance(g, Window))
        trees = sum(1 for g in geometry_list if isinstance(g, TreeSymbol))
        circles = sum(1 for g in geometry_list if isinstance(g, Circle2D))

        msg = STRINGS["status_done_detect"].format(
            walls=walls, doors=doors, windows=windows,
            trees=trees, circles=circles)
        self._status_bar.showMessage(msg)

        self._toolbar.btn_open.setEnabled(True)
        self._toolbar.btn_generate.setEnabled(True)
        self._toolbar.btn_export.setEnabled(False)

    def _on_detect_error(self, error_msg: str):
        self._set_detecting_state(False)
        QMessageBox.critical(self, "错误",
            STRINGS["err_detect_failed"].format(error=error_msg))
        self._toolbar.btn_open.setEnabled(True)

    def _on_preview(self):
        """Toggle AI preview / OpenCV preprocessing on/off."""
        if self._preview_mode:
            # Return to original
            saved_sel = self._saved_selection
            if self._saved_original_img is not None:
                self._image_panel.display_image(
                    self._saved_original_img, keep_selection=(saved_sel is not None))
                self._image_panel._original_img = self._saved_original_img.copy()
                if saved_sel is not None:
                    self._image_panel._selection_rect = saved_sel
                    self._image_panel._btn_reset_sel.setEnabled(True)
                    self._image_panel._redraw_with_selection()
            self._preview_mode = False
            self._status_bar.showMessage("已返回原图")
        else:
            if not self._image_panel.has_image:
                return
            img = self._image_panel._original_img
            if img is None:
                return
            if self._saved_original_img is None:
                self._saved_original_img = img.copy()
            self._saved_selection = self._image_panel.get_selected_region()

            if self.config.use_ai and self.config.ai_api_key:
                # Preview: only show cached detection, never call API
                if self._geometry_list:
                    self._image_panel.set_overlay(self._geometry_list)
                    self._preview_mode = True
                    from core.geometry import Wall, Door, Window, Circle2D
                    w = sum(1 for g in self._geometry_list if isinstance(g, Wall))
                    d = sum(1 for g in self._geometry_list if isinstance(g, Door))
                    wi = sum(1 for g in self._geometry_list if isinstance(g, Window))
                    c = sum(1 for g in self._geometry_list if isinstance(g, Circle2D))
                    self._status_bar.showMessage(
                        f"预览(缓存): {w}墙 {d}门 {wi}窗 {c}圆 | 再次点击返回", 0)
                else:
                    self._status_bar.showMessage(
                        "请先点击[检测]生成结果后再预览", 3000)
                    return
            else:
                self._show_opencv_preview(img)

        self._update_preview_button()

    def _show_opencv_preview(self, img):
        """Fallback: show OpenCV preprocessing preview."""
        from core.preprocessor import Preprocessor
        preprocessor = Preprocessor(self.config)
        preview_img = preprocessor.get_preview(img)
        self._image_panel.display_image(preview_img)
        self._preview_mode = True
        self._status_bar.showMessage(
            "OpenCV 预处理预览 | 再次点击按钮返回原图", 0)

    def _update_preview_button(self):
        """Update preview button text and color based on AI/mode."""
        is_ai = bool(self.config.use_ai and self.config.ai_api_key)
        if self._preview_mode:
            self._toolbar.btn_preview.setText("返回原图")
            self._toolbar.btn_preview.setStyleSheet("""
                QPushButton {
                    background-color: #43A047; color: white; border: none;
                    border-radius: 4px; padding: 6px 12px; font-weight: bold;
                }
                QPushButton:hover { background-color: #2E7D32; }
            """)
        elif is_ai:
            self._toolbar.btn_preview.setText("AI 预览")
            self._toolbar.btn_preview.setStyleSheet("""
                QPushButton {
                    background-color: #7B1FA2; color: white; border: none;
                    border-radius: 4px; padding: 6px 12px; font-weight: bold;
                }
                QPushButton:hover { background-color: #6A1B9A; }
            """)
        else:
            self._toolbar.btn_preview.setText("预处理预览")
            self._toolbar.btn_preview.setStyleSheet("""
                QPushButton {
                    background-color: #FF8F00; color: white; border: none;
                    border-radius: 4px; padding: 6px 12px; font-weight: bold;
                }
                QPushButton:hover { background-color: #EF6C00; }
            """)

    def _on_generate(self):
        if not self._geometry_list:
            QMessageBox.warning(self, "提示", STRINGS["err_no_geometry"])
            return

        self._toolbar.btn_generate.setEnabled(False)
        self._toolbar.btn_detect.setEnabled(False)
        self._status_bar.showMessage(STRINGS["status_generating"])

        self._codegen_worker = CodegenWorker(self._geometry_list, self._scale_factor)
        self._codegen_worker.progress.connect(self._status_bar.showMessage)
        self._codegen_worker.finished.connect(self._on_codegen_finished)
        self._codegen_worker.error.connect(self._on_codegen_error)
        self._codegen_worker.start()

    def _on_codegen_finished(self, scr_text: str):
        self._scr_text = scr_text
        self._code_panel.set_code(scr_text)

        line_count = scr_text.count('\n') + 1
        self._status_bar.showMessage(
            STRINGS["status_done_generate"].format(lines=line_count))

        self._toolbar.btn_generate.setEnabled(True)
        self._toolbar.btn_detect.setEnabled(True)
        self._toolbar.btn_export.setEnabled(True)

    def _on_codegen_error(self, error_msg: str):
        QMessageBox.critical(self, "错误",
            STRINGS["err_generate_failed"].format(error=error_msg))
        self._toolbar.btn_generate.setEnabled(True)
        self._toolbar.btn_detect.setEnabled(True)

    def _on_export(self):
        if not self._scr_text:
            QMessageBox.warning(self, "提示", STRINGS["err_no_code"])
            return

        mode = self._toolbar.get_export_mode()
        self._status_bar.showMessage(STRINGS["status_exporting"])
        QApplication.processEvents()

        try:
            if mode == 0:
                self._export_com()
            elif mode == 1:
                self._export_clipboard()
            elif mode == 2:
                self._export_file()
        except ImportError as e:
            QMessageBox.critical(self, "错误", str(e))

    def _export_com(self):
        if not self._com_exporter.is_autocad_available():
            reply = QMessageBox.question(
                self, "AutoCAD 未找到",
                STRINGS["err_com_not_found"] + "\n\n是否改用文件导出模式？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self._toolbar.cmb_export_mode.setCurrentIndex(2)
                self._export_file()
            return

        try:
            success = self._com_exporter.export(self._scr_text)
            if success:
                QMessageBox.information(self, "成功", STRINGS["msg_com_success"])
                self._status_bar.showMessage(STRINGS["msg_com_success"])
        except ConnectionError as e:
            QMessageBox.critical(self, "错误", str(e))

    def _export_clipboard(self):
        success = self._clipboard_exporter.export(self._scr_text)
        if success:
            QMessageBox.information(
                self, "导出成功 - 文件路径已复制",
                self._clipboard_exporter.get_instructions())
            self._status_bar.showMessage(
                f"已复制文件路径: {self._clipboard_exporter.last_path}")

    def _export_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, STRINGS["dlg_save_scr"],
            "cad_drawing.scr", STRINGS["dlg_scr_filter"])

        if not file_path:
            return

        try:
            success = self._file_exporter.export(self._scr_text, file_path)
            if success:
                QMessageBox.information(
                    self, "保存成功",
                    f"SCR 文件已保存到:\n{self._file_exporter.last_path}\n\n"
                    "【在 AutoCAD 中使用】\n"
                    "1. 打开 AutoCAD\n"
                    "2. 输入 SCRIPT 命令并回车\n"
                    "3. 在文件对话框中找到并选择此 .scr 文件\n"
                    "4. 点击打开，AutoCAD 将自动绘图\n\n"
                    "注意：请勿将代码内容直接粘贴到命令行！")
                self._status_bar.showMessage(
                    STRINGS["status_done_export"].format(
                        path=self._file_exporter.last_path))
        except IOError as e:
            QMessageBox.critical(self, "错误", str(e))

    def _on_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            self.config.save()
            self._update_preview_button()
            self._status_bar.showMessage("设置已保存", 3000)

    def _on_help(self):
        """Open the help/usage dialog."""
        dialog = HelpDialog(self)
        dialog.exec_()

    def closeEvent(self, event):
        if self._detect_worker and self._detect_worker.isRunning():
            self._detect_worker.quit()
            self._detect_worker.wait(2000)
        if self._codegen_worker and self._codegen_worker.isRunning():
            self._codegen_worker.quit()
            self._codegen_worker.wait(2000)
        event.accept()
