"""圆与圆弧检测 — 霍夫圆检测 + 椭圆拟合"""

import math
import cv2
import numpy as np
from typing import List, Tuple

from config.app_config import AppConfig
from core.geometry import Circle2D, Arc2D, Point2D


class CircleDetector:
    """圆和圆弧检测器

    圆: 霍夫变换 HoughCircles
    圆弧: 轮廓提取 + 椭圆拟合，判断是否为部分圆弧
    """

    def __init__(self, config: AppConfig):
        self.config = config

    def detect(self, binary: np.ndarray, gray: np.ndarray | None = None) -> Tuple[List[Circle2D], List[Arc2D]]:
        """检测圆和圆弧

        Args:
            binary: 二值图像
            gray: 灰度图（用于霍夫圆检测）

        Returns:
            (circles, arcs)
        """
        circles = self._detect_circles(binary, gray)
        arcs = self._detect_arcs(binary)
        return circles, arcs

    def _detect_circles(self, binary: np.ndarray, gray: np.ndarray | None) -> List[Circle2D]:
        """霍夫圆检测"""
        source = gray if gray is not None else binary

        detected = cv2.HoughCircles(
            source,
            cv2.HOUGH_GRADIENT,
            dp=self.config.hough_circle_dp,
            minDist=self.config.hough_circle_min_dist,
            param1=self.config.hough_circle_param1,
            param2=self.config.hough_circle_param2,
            minRadius=self.config.hough_circle_min_radius,
            maxRadius=self.config.hough_circle_max_radius
        )

        if detected is None:
            return []

        circles = []
        for x, y, r in detected[0]:
            circles.append(Circle2D(
                center=Point2D(float(x), float(y)),
                radius=float(r),
                confidence=0.8
            ))
        return circles

    def _detect_arcs(self, binary: np.ndarray) -> List[Arc2D]:
        """通过轮廓提取和椭圆拟合检测圆弧

        策略:
        1. 提取所有轮廓
        2. 对每个轮廓拟合椭圆
        3. 判断轮廓是否只覆盖部分椭圆（即是否是一个弧）
        """
        contours, _ = cv2.findContours(
            binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        arcs = []
        for cnt in contours:
            if len(cnt) < 5:
                # 椭圆拟合至少需要5个点
                continue

            # 跳过太小的轮廓
            if cv2.contourArea(cnt) < self.config.contour_min_area:
                continue

            try:
                ellipse = cv2.fitEllipse(cnt)
            except cv2.error:
                continue

            # ellipse: ((cx, cy), (major_axis, minor_axis), angle)
            (cx, cy), (major, minor), angle = ellipse

            # 检查是否是接近圆形的椭圆（轴比接近1）
            if min(major, minor) < 3:
                continue
            axis_ratio = min(major, minor) / max(major, minor)
            if axis_ratio < 0.5:
                continue  # 太扁，不是圆弧

            # 判断轮廓是否只覆盖部分圆
            avg_radius = (major + minor) / 4  # 椭圆轴的一半

            # 计算轮廓相对于椭圆中心的角度跨度
            is_arc, start_angle, end_angle = self._check_arc_span(
                cnt, (cx, cy), avg_radius
            )

            if is_arc:
                arcs.append(Arc2D(
                    center=Point2D(cx, cy),
                    radius=avg_radius,
                    start_angle=start_angle,
                    end_angle=end_angle,
                    confidence=0.6
                ))

        return arcs

    def _check_arc_span(
        self, contour: np.ndarray, center: Tuple[float, float],
        radius: float
    ) -> Tuple[bool, float, float]:
        """检查轮廓是否为部分圆弧

        Returns:
            (is_arc, start_angle_deg, end_angle_deg)
        """
        cx, cy = center

        # 计算轮廓上每个点相对于中心的角度
        angles = []
        for pt in contour:
            x, y = pt[0]
            dx = x - cx
            dy = y - cy
            angle = math.degrees(math.atan2(-dy, dx))  # Y轴向下
            if angle < 0:
                angle += 360
            angles.append(angle)

        angles.sort()

        # 检查角度跨度
        if len(angles) < 10:
            return False, 0, 0

        # 计算角度差的总和（考虑跨越0度的边界）
        total_gap = 0
        for i in range(len(angles) - 1):
            gap = angles[i + 1] - angles[i]
            if gap > 30:  # 大的间隙表示轮廓不连续
                total_gap += gap

        # 加上首尾之间的间隙
        wrap_gap = 360 - angles[-1] + angles[0]
        if wrap_gap > 30:
            total_gap += wrap_gap

        # 如果总间隙超过90度且角度跨度在30-330度之间，认为是弧
        span = 360 - total_gap
        is_arc = 30 < span < 330 and total_gap > 60

        if is_arc:
            start_angle = angles[0]
            end_angle = angles[-1]
            return True, start_angle, end_angle

        return False, 0, 0
