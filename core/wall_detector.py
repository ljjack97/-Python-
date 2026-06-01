"""墙体检测 — 平行线聚类识别墙体"""

import math
from typing import List, Tuple, Optional

from config.app_config import AppConfig
from core.geometry import Line2D, Point2D, Wall


class WallDetector:
    """墙体检测器

    核心算法:
    1. 将直线分为"近水平"和"近垂直"两组
    2. 在同组内找到间距在墙体厚度范围内的平行线对
    3. 要求平行线的投影重叠 ≥ 70%
    4. 合并为墙体对象（中心线 + 厚度）
    """

    def __init__(self, config: AppConfig):
        self.config = config

    def detect(self, lines: List[Line2D], scale_mm_per_px: float) -> List[Wall]:
        """从直线段中检测墙体

        Args:
            lines: 已检测到的直线段列表
            scale_mm_per_px: 比例尺（mm/像素）

        Returns:
            检测到的墙体列表
        """
        # 转换厚度范围到像素
        min_thickness_px = self.config.wall_thickness_min_mm / scale_mm_per_px
        max_thickness_px = self.config.wall_thickness_max_mm / scale_mm_per_px

        # 按方向分组
        h_lines = [l for l in lines if l.is_horizontal(self.config.wall_angle_tolerance)]
        v_lines = [l for l in lines if l.is_vertical(self.config.wall_angle_tolerance)]

        # 从两组中分别检测墙体
        walls = []
        walls.extend(self._detect_in_group(h_lines, min_thickness_px, max_thickness_px, "horizontal"))
        walls.extend(self._detect_in_group(v_lines, min_thickness_px, max_thickness_px, "vertical"))

        # 去重
        walls = self._deduplicate(walls)

        return walls

    def _detect_in_group(
        self, lines: List[Line2D], min_t: float, max_t: float, orientation: str
    ) -> List[Wall]:
        """在一组平行线中检测墙体"""
        if len(lines) < 2:
            return []

        walls = []
        used = [False] * len(lines)

        for i in range(len(lines)):
            if used[i]:
                continue
            for j in range(i + 1, len(lines)):
                if used[j]:
                    continue

                wall = self._try_pair(lines[i], lines[j], min_t, max_t)
                if wall is not None:
                    walls.append(wall)
                    used[i] = True
                    used[j] = True
                    break

        return walls

    def _try_pair(
        self, l1: Line2D, l2: Line2D, min_t: float, max_t: float
    ) -> Optional[Wall]:
        """检查两条平行线能否形成墙体

        Args:
            l1, l2: 两条线段
            min_t: 最小厚度（像素）
            max_t: 最大厚度（像素）

        Returns:
            Wall 对象，如果不能形成墙体返回 None
        """
        # 1. 检查距离（使用中点距离估算）
        dist = self._parallel_distance(l1, l2)

        if dist < min_t or dist > max_t:
            return None

        # 2. 检查投影重叠率
        overlap = self._projection_overlap(l1, l2)
        if overlap < self.config.wall_overlap_ratio:
            return None

        # 3. 构建中心线
        centerline = self._compute_centerline(l1, l2)

        # 4. 计算墙体角点
        corner_pts = self._compute_wall_corners(l1, l2, centerline)

        return Wall(
            centerline=centerline,
            thickness=dist,
            points=corner_pts,
            confidence=(l1.confidence + l2.confidence) / 2
        )

    @staticmethod
    def _parallel_distance(l1: Line2D, l2: Line2D) -> float:
        """计算两条近似平行线的间距"""
        # 使用 l1 两端点到 l2 的平均距离
        d1 = l2.distance_to_point(l1.p1)
        d2 = l2.distance_to_point(l1.p2)
        return (d1 + d2) / 2

    @staticmethod
    def _projection_overlap(l1: Line2D, l2: Line2D) -> float:
        """计算两条线段沿其方向轴的投影重叠比例"""
        # 平均方向
        avg_angle = (l1.angle_deg + l2.angle_deg) / 2
        rad = math.radians(avg_angle)
        dx = math.cos(rad)
        dy = math.sin(rad)

        def component(p: Point2D) -> float:
            return p.x * dx + p.y * dy

        # 计算两条线段在方向上的投影区间
        a1, a2 = component(l1.p1), component(l1.p2)
        proj1 = (min(a1, a2), max(a1, a2))

        b1, b2 = component(l2.p1), component(l2.p2)
        proj2 = (min(b1, b2), max(b1, b2))

        # 计算重叠长度
        overlap_start = max(proj1[0], proj2[0])
        overlap_end = min(proj1[1], proj2[1])
        overlap_len = max(0, overlap_end - overlap_start)

        # 相对于较短线段的长度
        min_len = min(proj1[1] - proj1[0], proj2[1] - proj2[0])
        if min_len < 1:
            return 0.0

        return overlap_len / min_len

    @staticmethod
    def _compute_centerline(l1: Line2D, l2: Line2D) -> Line2D:
        """计算两条平行线的中心线"""
        # 取两条线的中点，连线即为近似的中心线
        mid1 = l1.midpoint
        mid2 = l2.midpoint

        # 投影到平均方向
        avg_angle = (l1.angle_deg + l2.angle_deg) / 2
        rad = math.radians(avg_angle)
        dx = math.cos(rad)
        dy = math.sin(rad)

        # 取两条线端点在平均方向上的最值
        points = [l1.p1, l1.p2, l2.p1, l2.p2]

        def proj(p: Point2D) -> float:
            return p.x * dx + p.y * dy

        projs = [proj(p) for p in points]
        min_idx = projs.index(min(projs))
        max_idx = projs.index(max(projs))

        return Line2D(p1=points[min_idx], p2=points[max_idx])

    @staticmethod
    def _compute_wall_corners(l1: Line2D, l2: Line2D, centerline: Line2D) -> List[Point2D]:
        """计算矩形墙体的4个角点"""
        # 基于中心线和厚度计算角点
        dx = centerline.p2.x - centerline.p1.x
        dy = centerline.p2.y - centerline.p1.y
        length = (dx * dx + dy * dy) ** 0.5
        if length < 1e-9:
            return [centerline.p1, centerline.p2, centerline.p2, centerline.p1]

        # 垂直方向
        nx = -dy / length
        ny = dx / length

        # 使用两条线的平均端点到中心线的距离作为半厚度
        d1 = abs(l1.p1.x * nx + l1.p1.y * ny - centerline.p1.x * nx - centerline.p1.y * ny)
        d2 = abs(l2.p1.x * nx + l2.p1.y * ny - centerline.p1.x * nx - centerline.p1.y * ny)
        half_t = (d1 + d2) / 2

        p1 = centerline.p1
        p2 = centerline.p2

        return [
            Point2D(p1.x + nx * half_t, p1.y + ny * half_t),
            Point2D(p2.x + nx * half_t, p2.y + ny * half_t),
            Point2D(p2.x - nx * half_t, p2.y - ny * half_t),
            Point2D(p1.x - nx * half_t, p1.y - ny * half_t),
        ]

    @staticmethod
    def _deduplicate(walls: List[Wall], tolerance_px: float = 10.0) -> List[Wall]:
        """去除重复检测的墙体"""
        if len(walls) <= 1:
            return walls

        deduped = []
        for wall in walls:
            is_dup = False
            for existing in deduped:
                # 比较中心线的中点和厚度
                if (wall.centerline.midpoint.distance_to(existing.centerline.midpoint) < tolerance_px
                        and abs(wall.thickness - existing.thickness) < tolerance_px):
                    is_dup = True
                    break
            if not is_dup:
                deduped.append(wall)

        return deduped
