"""景观元素检测 — 树（圆）、道路（曲线）、水体（闭合大轮廓）"""

from typing import List, Tuple

from config.app_config import AppConfig
from core.geometry import (
    Circle2D, Polyline, TreeSymbol, WaterFeature, PathLine, Point2D
)


class LandscapeDetector:
    """景观元素检测器

    树: 小圆 + 内部纹理判断
    道路: 曲率大的多段线
    水体: 大面积闭合轮廓 + 无内部墙线
    """

    def __init__(self, config: AppConfig):
        self.config = config

    def detect(
        self, circles: List[Circle2D], polylines: List[Polyline],
        scale_mm_per_px: float
    ) -> Tuple[List[TreeSymbol], List[PathLine], List[WaterFeature]]:
        """检测所有景观元素

        Args:
            circles: 已检测到的圆
            polylines: 已检测到的多段线/轮廓
            scale_mm_per_px: 比例尺

        Returns:
            (trees, paths, water_features)
        """
        trees = self._detect_trees(circles, scale_mm_per_px)
        water = self._detect_water(polylines, scale_mm_per_px)
        paths = self._detect_paths(polylines, scale_mm_per_px)
        return trees, paths, water

    def _detect_trees(
        self, circles: List[Circle2D], scale_mm_per_px: float
    ) -> List[TreeSymbol]:
        """检测树符号

        树在平面图中通常表示为圆形符号。
        """
        trees = []
        tree_radius_min_px = self.config.tree_radius_min_mm / scale_mm_per_px
        tree_radius_max_px = self.config.tree_radius_max_mm / scale_mm_per_px

        for circle in circles:
            if tree_radius_min_px <= circle.radius <= tree_radius_max_px:
                trees.append(TreeSymbol(
                    center=circle.center,
                    radius=circle.radius,
                    confidence=circle.confidence
                ))

        return trees

    def _detect_water(
        self, polylines: List[Polyline], scale_mm_per_px: float
    ) -> List[WaterFeature]:
        """检测水体特征

        水体通常表现为:
        - 大面积闭合轮廓
        - 形状不规则/圆滑
        - 内部无墙体线
        """
        water_features = []

        for pl in polylines:
            if not pl.closed:
                continue

            # 计算面积
            area = self._polygon_area(pl.points)
            if area < self.config.water_area_min_px:
                continue

            # 水体通常形状平滑（多点）或不规则
            if pl.point_count < 8:
                continue

            # 检查轮廓的圆度（水体通常不是完美的矩形）
            # 低圆度 = 更像自然形状
            circularity = self._compute_circularity(pl.points, area)
            if circularity < 0.8:  # 不是完美圆形，更可能是自然水体
                water_features.append(WaterFeature(
                    contour=pl.points,
                    area=area,
                    confidence=0.5
                ))

        return water_features

    def _detect_paths(
        self, polylines: List[Polyline], scale_mm_per_px: float
    ) -> List[PathLine]:
        """检测道路/路径

        道路在平面图中表现为:
        - 曲线/折线（开放多段线）
        - 有一定长度
        - 可能平行成对（道路边界），但我们取中线
        """
        paths = []

        for pl in polylines:
            if pl.closed:
                # 闭合且细长的轮廓也可能是道路
                if pl.point_count < 6:
                    continue
                if not self._is_elongated(pl):
                    continue
            else:
                if pl.point_count < 4:
                    continue

            # 计算总长度
            total_len = 0
            for i in range(len(pl.points) - 1):
                total_len += pl.points[i].distance_to(pl.points[i + 1])

            min_path_len_px = 30  # 最小路径长度
            if total_len < min_path_len_px:
                continue

            # 确定路宽
            path_width = self.config.wall_thickness_min_mm  # 默认1.2m步道
            width_px = path_width / scale_mm_per_px

            paths.append(PathLine(
                polyline=pl.points,
                width=width_px,
                confidence=0.5
            ))

        return paths

    @staticmethod
    def _polygon_area(points: List[Point2D]) -> float:
        """计算多边形面积（Shoelace 公式）"""
        n = len(points)
        if n < 3:
            return 0.0
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i].x * points[j].y
            area -= points[j].x * points[i].y
        return abs(area) / 2

    @staticmethod
    def _compute_circularity(points: List[Point2D], area: float) -> float:
        """计算轮廓的圆度 (4π*area/perimeter²)"""
        import math
        perimeter = 0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            perimeter += points[i].distance_to(points[j])
        if perimeter < 1:
            return 0.0
        return 4 * math.pi * area / (perimeter * perimeter)

    @staticmethod
    def _is_elongated(pl: Polyline) -> bool:
        """判断多段线是否细长"""
        xs = [p.x for p in pl.points]
        ys = [p.y for p in pl.points]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        if width < 1 and height < 1:
            return False
        if max(width, height) < 1:
            return False
        return max(width, height) / (min(width, height) + 1) > 3.0
