"""端到端流水线测试"""

import cv2
import numpy as np
import pytest

from config.app_config import AppConfig
from core.preprocessor import Preprocessor
from core.line_detector import LineDetector
from core.circle_detector import CircleDetector
from core.contour_detector import ContourDetector
from core.scale_estimator import ScaleEstimator
from core.wall_detector import WallDetector
from core.door_window_detector import DoorWindowDetector
from core.landscape_detector import LandscapeDetector
from cad.code_generator import CodeGenerator
from cad.scr_builder import ScrBuilder
from cad.cad_commands import cmd_line, cmd_circle, cmd_rect, cmd_pline


class TestPreprocessor:
    """预处理测试"""

    def test_basic_preprocessing(self):
        config = AppConfig()
        preprocessor = Preprocessor(config)

        img = np.zeros((200, 300, 3), dtype=np.uint8)
        cv2.rectangle(img, (50, 50), (250, 150), (255, 255, 255), 2)

        binary, gray = preprocessor.process(img)
        assert binary is not None
        assert gray is not None
        assert binary.shape[:2] == (200, 300)
        assert len(binary.shape) == 2  # 二值图应为2维


class TestLineDetector:
    """直线检测测试"""

    def test_detect_lines(self):
        config = AppConfig()
        config.hough_line_threshold = 20
        config.hough_line_min_length = 10

        preprocessor = Preprocessor(config)
        detector = LineDetector(config)

        img = np.zeros((200, 300, 3), dtype=np.uint8)
        cv2.line(img, (50, 100), (250, 100), (255, 255, 255), 2)
        cv2.line(img, (100, 50), (100, 150), (255, 255, 255), 2)

        binary, _ = preprocessor.process(img)
        lines = detector.detect(binary)

        assert len(lines) > 0


class TestCircleDetector:
    """圆检测测试"""

    def test_detect_circles(self):
        config = AppConfig()
        config.hough_circle_min_radius = 20
        config.hough_circle_max_radius = 100

        preprocessor = Preprocessor(config)
        detector = CircleDetector(config)

        img = np.zeros((200, 300, 3), dtype=np.uint8)
        cv2.circle(img, (150, 100), 40, (255, 255, 255), 2)

        binary, gray = preprocessor.process(img)
        circles, arcs = detector.detect(binary, gray)

        assert len(circles) >= 1


class TestCADCommands:
    """CAD 命令生成测试"""

    def test_cmd_line(self):
        result = cmd_line(0, 0, 100, 200)
        assert "LINE" in result
        assert "0.00,0.00" in result
        assert "100.00,200.00" in result

    def test_cmd_circle(self):
        result = cmd_circle(50, 60, 30)
        assert "CIRCLE" in result
        assert "50.00,60.00" in result
        assert "30.00" in result

    def test_cmd_pline(self):
        points = [(0, 0), (100, 0), (100, 100), (0, 100)]
        result = cmd_pline(points, width=240, closed=True)
        assert "PLINE" in result
        assert "C" in result or "100.00,100.00" in result


class TestScrBuilder:
    """SCR 构建器测试"""

    def test_build_scr(self):
        config = AppConfig()
        preprocessor = Preprocessor(config)
        line_detector = LineDetector(config)
        circle_detector = CircleDetector(config)

        img = np.zeros((200, 300, 3), dtype=np.uint8)
        cv2.rectangle(img, (50, 50), (250, 150), (255, 255, 255), 2)
        cv2.circle(img, (150, 100), 30, (255, 255, 255), 2)

        binary, gray = preprocessor.process(img)
        lines = line_detector.detect(binary)
        circles, arcs = circle_detector.detect(binary, gray)

        geometry_list = list(lines) + list(circles) + list(arcs)

        cg = CodeGenerator()
        builder = ScrBuilder(None, cg)

        scr_text = builder.build(geometry_list, scale_factor=5.0)

        assert len(scr_text) > 0
        assert "ZOOM\nE\n" in scr_text
        # Verify newline format (no -LAYER, no spaces)
        assert "-LAYER" not in scr_text  # No layer commands
        assert "\nLINE\n" in scr_text or "\nCIRCLE\n" in scr_text
        # Verify ASCII-only
        for line in scr_text.split('\n'):
            for ch in line:
                assert ord(ch) < 128, f"Non-ASCII char in SCR: {repr(line)}"
