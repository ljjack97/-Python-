"""全局应用配置"""

import os
import json
import os
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class AppConfig:
    """应用配置数据类"""

    # === 路径 ===
    app_name: str = "CAD 图像转代码工具"
    data_dir: str = field(default_factory=lambda: os.path.join(os.path.expanduser("~"), ".cad_image_to_code"))
    temp_dir: str = field(default_factory=lambda: os.path.join(os.path.expanduser("~"), ".cad_image_to_code", "temp"))

    # === 支持的图片格式 ===
    supported_formats: Tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")

    # === 默认检测参数 ===
    # 预处理
    blur_kernel_size: int = 5           # 高斯模糊核大小（奇数）
    adaptive_thresh_block: int = 11     # 自适应阈值块大小（奇数）
    adaptive_thresh_c: int = 2          # 自适应阈值常数

    # Canny edge detection
    canny_low: int = 30
    canny_high: int = 100

    # HoughLinesP line detection
    hough_line_threshold: int = 30
    hough_line_min_length: int = 15
    hough_line_max_gap: int = 15

    # HoughCircles circle detection
    hough_circle_dp: float = 1.2
    hough_circle_min_dist: int = 20
    hough_circle_param1: int = 40
    hough_circle_param2: int = 20
    hough_circle_min_radius: int = 5    # 最小半径（像素）
    hough_circle_max_radius: int = 200  # 最大半径（像素）

    # LSD (Line Segment Detector)
    use_lsd: bool = True                     # 是否使用LSD检测器
    lsd_length_threshold: int = 20           # 最小线段长度，越大过滤越多噪点 (must be int)
    lsd_distance_threshold: float = 5.0      # 线段合并距离阈值
    lsd_merge: bool = True                   # 是否合并相近线段

    # AI Vision
    use_ai: bool = True                      # 优先使用AI视觉检测
    ai_provider: str = "step"               # "step" (阶跃) or "qwen" (通义)
    ai_api_key: str = ""                     # API Key

    # 轮廓检测
    contour_min_area: int = 50          # 最小轮廓面积（像素²）

    # 墙体检测
    wall_thickness_min_mm: float = 80   # 最小墙体厚度（mm）
    wall_thickness_max_mm: float = 500  # 最大墙体厚度（mm）
    wall_overlap_ratio: float = 0.7     # 平行线投影重叠最小比例
    wall_angle_tolerance: float = 15.0  # 水平/垂直角度容差（度）

    # 门窗检测
    door_width_min_mm: float = 600      # 最小门宽（mm）
    door_width_max_mm: float = 1200     # 最大门宽（mm）
    window_thickness_mm: float = 200    # 窗厚度（mm）
    window_thickness_max_mm: float = 400

    # 景观检测
    tree_radius_min_mm: float = 2       # 树符号最小半径（mm）
    tree_radius_max_mm: float = 30      # 树符号最大半径（mm）
    water_area_min_px: int = 1000       # 水体最小面积（像素²）
    path_curvature_threshold: float = 0.3  # 道路曲率阈值

    # 比例尺
    default_scale_mm_per_px: float = 5.0  # 默认比例（mm/像素）

    # === AutoCAD 版本 ===
    autocad_version: str = "2020"
    # ProgID 后缀映射
    autocad_progid_map: Dict[str, str] = field(default_factory=lambda: {
        "2020": "AutoCAD.Application.24",
        "2021": "AutoCAD.Application.24.1",
        "2022": "AutoCAD.Application.24.2",
        "2023": "AutoCAD.Application.24.3",
        "2024": "AutoCAD.Application.24.4",
        "2025": "AutoCAD.Application.25",
    })

    # === 日志 ===
    log_level: str = "INFO"
    log_file: str = field(default_factory=lambda: os.path.join(os.path.expanduser("~"), ".cad_image_to_code", "app.log"))

    def ensure_dirs(self):
        """确保必要的目录存在"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    @property
    def _config_path(self) -> str:
        return os.path.join(self.data_dir, "config.json")

    def load(self):
        """Load settings from disk."""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, value in data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
        except Exception:
            pass

    def save(self):
        """Save settings to disk."""
        try:
            keys = [
                "canny_low", "canny_high",
                "hough_line_threshold", "hough_line_min_length", "hough_line_max_gap",
                "wall_thickness_min_mm", "wall_thickness_max_mm",
                "default_scale_mm_per_px", "autocad_version",
                "lsd_length_threshold", "ai_api_key", "ai_provider",
            ]
            data = {k: getattr(self, k) for k in keys}
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def get_progid(self) -> str:
        """获取当前 AutoCAD 版本的 ProgID"""
        return self.autocad_progid_map.get(self.autocad_version, "AutoCAD.Application.24")
