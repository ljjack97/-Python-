"""比例尺识别 — 从图像中搜索比例尺并计算 pixel→mm 换算因子"""

import cv2
import numpy as np
from typing import Optional, List

from config.app_config import AppConfig
from core.geometry import Line2D


class ScaleEstimator:
    """比例尺识别器

    策略:
    1. 在图像右下角/底部区域搜索比例尺图案（交替黑白块）
    2. 尝试读取比例尺数字标注
    3. 如失败，返回配置文件中的默认值
    """

    def __init__(self, config: AppConfig):
        self.config = config

    def estimate(self, binary: np.ndarray, lines: List[Line2D],
                 img_shape: tuple) -> float:
        """估计比例尺（mm/像素）

        Args:
            binary: 二值图像
            lines: 已检测到的直线段
            img_shape: 图像尺寸 (height, width)

        Returns:
            mm/像素 的比例因子
        """
        h, w = img_shape[:2]

        # 策略1: 在图像底部区域搜索比例尺
        scale = self._search_scale_bar(binary, h, w)
        if scale is not None:
            return scale

        # 策略2: 从图框尺寸推断（建筑标准图纸通常有标准的图框大小）
        scale = self._infer_from_frame(lines, w)
        if scale is not None:
            return scale

        # 策略3: 使用默认值
        return self.config.default_scale_mm_per_px

    def _search_scale_bar(self, binary: np.ndarray, h: int, w: int) -> Optional[float]:
        """在图像底部区域搜索比例尺图案

        比例尺通常是一段交替黑白块的线段，出现在图纸底部。
        搜索区域: 图像底部 20%
        """
        # 取底部 20% 区域
        roi_top = int(h * 0.8)
        roi = binary[roi_top:h, 0:w]

        if roi.size == 0:
            return None

        # 水平投影（按行求和）
        horizontal_proj = np.sum(roi, axis=1) / 255

        # 找到有内容的行
        content_rows = np.where(horizontal_proj > w * 0.05)[0]
        if len(content_rows) < 5:
            return None

        # 在最底部有内容的区域搜索
        bottom_lines = binary[h - min(100, h // 5):h, :]

        # 按列求和，找水平方向的交替模式
        col_proj = np.sum(bottom_lines, axis=0) / 255
        if len(col_proj) < 10:
            return None

        # 寻找黑白交替的模式（比例尺特征）
        transitions = []
        in_black = False
        for i in range(1, len(col_proj)):
            is_black = col_proj[i] > col_proj.max() * 0.3
            if is_black != in_black:
                transitions.append(i)
                in_black = is_black

        if len(transitions) < 4:
            return None

        # 分析交替段的宽度
        segments = []
        for i in range(len(transitions) - 1):
            seg_width = transitions[i + 1] - transitions[i]
            if seg_width > 3:
                segments.append(seg_width)

        if len(segments) < 2:
            return None

        # 取中位数段宽（避免异常值）
        median_width = float(np.median(segments))

        # 假设每个段代表 1000mm（1m）—— 常见比例尺单位
        # 实际值取决于图纸比例，这里返回像素对应毫米的比例
        if median_width > 0:
            # 每段 ≈ 1000mm，所以 mm_per_px = 1000 / median_width
            return 1000.0 / median_width

        return None

    def _infer_from_frame(self, lines: List[Line2D], img_width: int) -> Optional[float]:
        """从图框尺寸推断比例尺

        如果检测到一个大的矩形框（图框），可以根据标准图纸尺寸推断。
        标准 A3: 420×297mm, A2: 594×420mm, A1: 841×594mm, A0: 1189×841mm
        """
        if not lines:
            return None

        # 找最长的两条水平线和垂直线
        h_lines = [l for l in lines if l.is_horizontal(5)]
        v_lines = [l for l in lines if l.is_vertical(5)]

        if len(h_lines) < 2 or len(v_lines) < 2:
            return None

        # 找最长的水平线和垂直线（近似图框）
        longest_h = max(h_lines, key=lambda l: l.length)
        longest_v = max(v_lines, key=lambda l: l.length)

        frame_w_px = longest_h.length
        frame_h_px = longest_v.length

        if frame_w_px < 100 or frame_h_px < 100:
            return None

        # 尝试匹配标准图纸尺寸
        standard_sizes = {
            "A3": (420, 297),
            "A2": (594, 420),
            "A1": (841, 594),
            "A0": (1189, 841),
        }

        best_match = None
        best_error = float("inf")
        for name, (w_mm, h_mm) in standard_sizes.items():
            # 可能旋转
            for (fw, fh) in [(w_mm, h_mm), (h_mm, w_mm)]:
                scale_w = fw / frame_w_px
                scale_h = fh / frame_h_px
                avg_scale = (scale_w + scale_h) / 2
                error = abs(scale_w - scale_h) / avg_scale
                if error < 0.3 and error < best_error:
                    best_error = error
                    best_match = avg_scale

        return best_match
