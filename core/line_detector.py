"""直线检测 — Canny 边缘 + 霍夫直线检测 + 共线合并"""

import math
import cv2
import numpy as np
from typing import List

from config.app_config import AppConfig
from core.geometry import Line2D, Point2D


class LineDetector:
    """直线检测器

    流程: Canny 边缘检测 → HoughLinesP → 共线线段合并
    """

    def __init__(self, config: AppConfig):
        self.config = config

    def detect(self, binary: np.ndarray) -> List[Line2D]:
        """检测图像中的所有直线段

        Args:
            binary: 二值图像

        Returns:
            合并后的直线段列表
        """
        edges = self._canny(binary)
        segments = self._hough_lines(edges)
        merged = self._merge_collinear(segments)
        return merged

    def _canny(self, binary: np.ndarray) -> np.ndarray:
        """Canny 边缘检测"""
        return cv2.Canny(
            binary,
            self.config.canny_low,
            self.config.canny_high,
            apertureSize=3
        )

    def _hough_lines(self, edges: np.ndarray) -> List[Line2D]:
        """霍夫直线检测"""
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self.config.hough_line_threshold,
            minLineLength=self.config.hough_line_min_length,
            maxLineGap=self.config.hough_line_max_gap
        )

        if lines is None:
            return []

        result = []
        max_votes = self.config.hough_line_threshold * 2  # 估计最大累加值
        for line in lines:
            x1, y1, x2, y2 = line[0]
            conf = min(1.0, self.config.hough_line_threshold / max_votes + 0.5)
            result.append(Line2D(
                p1=Point2D(x1, y1),
                p2=Point2D(x2, y2),
                confidence=conf
            ))
        return result

    def _merge_collinear(self, segments: List[Line2D]) -> List[Line2D]:
        """合并共线且重叠的线段

        策略:
        1. 按角度分组（每5度一组）
        2. 在每组内，按截距进一步分组
        3. 合并每组中投影重叠的线段
        """
        if len(segments) <= 1:
            return segments

        # 计算每条线的斜率和截距
        line_params = []
        for seg in segments:
            angle = seg.angle_deg
            # 计算直线方程: ax + by + c = 0
            dx = seg.p2.x - seg.p1.x
            dy = seg.p2.y - seg.p1.y
            a = -dy
            b = dx
            c = -(a * seg.p1.x + b * seg.p1.y)
            # 归一化
            norm = math.sqrt(a * a + b * b)
            if norm > 1e-9:
                a /= norm
                b /= norm
                c /= norm
            line_params.append((seg, angle, a, b, c))

        # 按角度分组
        groups: List[List[tuple]] = []
        used = [False] * len(line_params)
        angle_tol = 5.0  # 角度容差

        for i, (seg_i, ang_i, a_i, b_i, c_i) in enumerate(line_params):
            if used[i]:
                continue
            group = [(seg_i, a_i, b_i, c_i)]
            used[i] = True
            for j in range(i + 1, len(line_params)):
                if used[j]:
                    continue
                _, ang_j, a_j, b_j, c_j = line_params[j]
                if abs(ang_i - ang_j) <= angle_tol or abs(ang_i - ang_j) >= 180 - angle_tol:
                    # 检查截距是否接近
                    if abs(c_i - c_j) <= 10.0:
                        group.append((line_params[j][0], a_j, b_j, c_j))
                        used[j] = True
            groups.append(group)

        # 合并每组中的线段
        merged = []
        for group in groups:
            if len(group) == 1:
                merged.append(group[0][0])
            else:
                m = self._merge_group(group)
                merged.extend(m)

        return merged

    def _merge_group(self, group: List[tuple]) -> List[Line2D]:
        """合并同一组内的线段，按投影重叠判断"""
        segs = [item[0] for item in group]
        # 计算投影方向（平均角度）
        avg_angle = sum(s.angle_deg for s in segs) / len(segs)
        rad = math.radians(avg_angle)
        proj_dir = (math.cos(rad), math.sin(rad))

        # 计算每条线段在投影方向上的区间
        def project(seg: Line2D) -> tuple:
            v1 = seg.p1.x * proj_dir[0] + seg.p1.y * proj_dir[1]
            v2 = seg.p2.x * proj_dir[0] + seg.p2.y * proj_dir[1]
            return (min(v1, v2), max(v1, v2), seg)

        intervals = [project(s) for s in segs]
        intervals.sort(key=lambda x: x[0])

        # 合并重叠区间
        merged_segs = []
        current_min, current_max, current_seg = intervals[0]
        for t_min, t_max, t_seg in intervals[1:]:
            if t_min <= current_max + 10:  # 重叠或接近
                # 合并：取最小起点和最大终点的线段端点
                current_max = max(current_max, t_max)
                # 选择最远的两个端点作为新线段
                all_pts = [
                    current_seg.p1, current_seg.p2,
                    t_seg.p1, t_seg.p2
                ]
                # 找到最远的两个点
                max_dist = 0
                far_pts = (all_pts[0], all_pts[1])
                for a in range(len(all_pts)):
                    for b in range(a + 1, len(all_pts)):
                        d = all_pts[a].distance_to(all_pts[b])
                        if d > max_dist:
                            max_dist = d
                            far_pts = (all_pts[a], all_pts[b])
                current_seg = Line2D(
                    p1=far_pts[0],
                    p2=far_pts[1],
                    confidence=max(current_seg.confidence, t_seg.confidence)
                )
            else:
                merged_segs.append(current_seg)
                current_min, current_max, current_seg = t_min, t_max, t_seg
        merged_segs.append(current_seg)

        return merged_segs
