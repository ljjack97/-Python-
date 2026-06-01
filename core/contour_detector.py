"""轮廓检测 — 提取闭合形状并进行多边形近似与分类"""

import cv2
import numpy as np
from typing import List

from config.app_config import AppConfig
from core.geometry import Polyline, Point2D


class ContourDetector:
    """轮廓检测器

    提取闭合形状，通过多边形近似进行分类。
    用于检测不规则形状（如水体边界、花坛、铺装区域等）。
    """

    def __init__(self, config: AppConfig):
        self.config = config

    def detect(self, binary: np.ndarray) -> List[Polyline]:
        """检测所有闭合轮廓

        Args:
            binary: 二值图像

        Returns:
            多边形近似后的闭合轮廓列表
        """
        contours, hierarchy = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        polylines = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.config.contour_min_area:
                continue

            polyline = self._approx_polygon(cnt)
            if polyline is not None:
                polylines.append(polyline)

        return polylines

    def _approx_polygon(self, contour: np.ndarray) -> Polyline | None:
        """对轮廓进行多边形近似

        Args:
            contour: OpenCV 轮廓

        Returns:
            Polyline 对象，如果近似失败返回 None
        """
        perimeter = cv2.arcLength(contour, closed=True)
        if perimeter < 1:
            return None

        # 使用 Douglas-Peucker 算法进行多边形近似
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, closed=True)

        if len(approx) < 3:
            return None

        points = [Point2D(float(pt[0][0]), float(pt[0][1])) for pt in approx]

        # 判断是否闭合（首尾点距离足够近）
        closed = points[0].distance_to(points[-1]) < epsilon * 2

        return Polyline(points=points, closed=closed)

    def classify_shape(self, polyline: Polyline, area: float) -> str:
        """分类形状类型

        Args:
            polyline: 轮廓多段线
            area: 轮廓面积

        Returns:
            形状分类标签
        """
        n = polyline.point_count

        if n == 3:
            return "triangle"
        elif n == 4:
            # 检查是否是矩形
            if self._is_rectangular(polyline):
                aspect_ratio = self._aspect_ratio(polyline)
                if 0.8 < aspect_ratio < 1.2:
                    return "square"
                return "rectangle"
            return "quadrilateral"
        elif n <= 6:
            return "polygon_small"
        elif n <= 12:
            return "polygon_medium"
        else:
            # 检查曲率
            if self._is_smooth(polyline):
                return "smooth_contour"
            return "complex_polygon"

    @staticmethod
    def _is_rectangular(polyline: Polyline) -> bool:
        """检查多段线是否近似矩形（四个角接近90度）"""
        if polyline.point_count != 4:
            return False
        import math
        pts = polyline.points
        for i in range(4):
            p0 = pts[i]
            p1 = pts[(i + 1) % 4]
            p2 = pts[(i + 2) % 4]
            v1 = (p1.x - p0.x, p1.y - p0.y)
            v2 = (p2.x - p1.x, p2.y - p1.y)
            dot = v1[0] * v2[0] + v1[1] * v2[1]
            len1 = math.sqrt(v1[0]**2 + v1[1]**2)
            len2 = math.sqrt(v2[0]**2 + v2[1]**2)
            if len1 < 1e-9 or len2 < 1e-9:
                return False
            cos_angle = dot / (len1 * len2)
            if abs(cos_angle) > 0.3:  # 远离90度
                return False
        return True

    @staticmethod
    def _aspect_ratio(polyline: Polyline) -> float:
        """计算包围盒宽高比"""
        xs = [p.x for p in polyline.points]
        ys = [p.y for p in polyline.points]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        if height < 1:
            return float("inf")
        return width / height

    @staticmethod
    def _is_smooth(polyline: Polyline) -> bool:
        """检查多段线是否平滑（相邻边角度变化小）"""
        if polyline.point_count < 6:
            return False
        import math
        pts = polyline.points
        total_angle_change = 0
        count = len(pts)
        for i in range(count):
            p0 = pts[i]
            p1 = pts[(i + 1) % count]
            p2 = pts[(i + 2) % count]
            v1 = (p1.x - p0.x, p1.y - p0.y)
            v2 = (p2.x - p1.x, p2.y - p1.y)
            len1 = math.sqrt(v1[0]**2 + v1[1]**2)
            len2 = math.sqrt(v2[0]**2 + v2[1]**2)
            if len1 < 1 or len2 < 1:
                continue
            dot = v1[0] * v2[0] + v1[1] * v2[1]
            cos_a = max(-1.0, min(1.0, dot / (len1 * len2)))
            angle = math.degrees(math.acos(cos_a))
            total_angle_change += angle
        avg_change = total_angle_change / count if count > 0 else 0
        return avg_change < 30  # 平均角度变化小于30度视为平滑
