"""Background worker threads for detection and code generation."""

import threading
from PyQt5.QtCore import QThread, pyqtSignal
from config.app_config import AppConfig
from core.vectorizer import Vectorizer
from core.dual_ai import DualAI
from cad.code_generator import CodeGenerator
from cad.scr_builder import ScrBuilder


class DetectionWorker(QThread):
    """Runs image detection in background thread."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(object, float)
    finished_scr = pyqtSignal(str)  # Direct SCR from DualAI
    error = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, img, config: AppConfig):
        super().__init__()
        self.img = img
        self.config = config
        self._interrupted = False

    def cancel(self):
        self._interrupted = True
        self.requestInterruption()

    def run(self):
        try:
            # === Dual AI Mode (Vision + Text) ===
            if self.config.use_ai and self.config.ai_api_key:
                self.progress.emit("AI#1 视觉识别中...")
                dual = DualAI(self.config.ai_api_key)
                scr = dual.detect_and_generate(self.img)
                if scr and not self._interrupted:
                    self.progress.emit(
                        f"AI#2 代码生成完成: {scr.count(chr(10))} 行 SCR")
                    self.finished_scr.emit(scr)
                    return

            # === Fallback: OpenCV Vectorizer ===
            self.progress.emit("OpenCV 矢量化中...")
            vectorizer = Vectorizer()
            result = vectorizer.detect(self.img)
            if self._interrupted:
                self.cancelled.emit(); return
            self.progress.emit(
                f"检测: {len(result)}元素")
            self.finished.emit(result, 10.0)

        except Exception as e:
            import traceback
            self.error.emit(f"检测失败: {e}\n{traceback.format_exc()}")


class CodegenWorker(QThread):
    """Runs SCR code generation in background thread."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, geometry_list, scale_factor: float):
        super().__init__()
        self.geometry_list = geometry_list
        self.scale_factor = scale_factor

    def run(self):
        try:
            self.progress.emit("正在生成 CAD 代码...")
            code_generator = CodeGenerator()
            scr_builder = ScrBuilder(None, code_generator)
            scr_text = scr_builder.build(self.geometry_list, self.scale_factor)
            self.progress.emit(f"代码生成完成: {scr_text.count(chr(10))} 行")
            self.finished.emit(scr_text)
        except Exception as e:
            import traceback
            self.error.emit(f"代码生成失败: {e}\n{traceback.format_exc()}")
