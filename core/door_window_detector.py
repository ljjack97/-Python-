"""门窗检测 — 基于弧+墙体间隙识别门，基于墙体间细矩形识别窗"""

import math
from typing import List, Tuple, Optional

from config.app_config import AppConfig
from core.geometry import Line2D, Arc2D, Point2D, Wall, Door, Window


class DoorWindowDetector:
    """门和窗检测器

    门检测:
    1. 弧方法：圆弧端点落在两面墙中心线上 → 门扇弧
    2. 间隙方法：沿墙中心线搜索间隙 → 门洞

    窗检测:
    沿墙中心线搜索墙体细缝 → 窗户
    """

    def __init__(self, config: AppConfig):
        self.config = config

    def detect(
        self, walls: List[Wall], arcs: List[Arc2D],
        lines: List[Line2D], scale_mm_per_px: float
    ) -> Tuple[List[Door], List[Window]]:
        """检测门和窗

        Args:
            walls: 已检测到的墙体
            arcs: 已检测到的圆弧
            lines: 所有直线段
            scale_mm_per_px: 比例尺

        Returns:
            (doors, windows)
        """
        doors = self._detect_doors(walls, arcs, scale_mm_per_px)
        windows = self._detect_windows(walls, lines, scale_mm_per_px)
        return doors, windows

    def _detect_doors(
        self, walls: List[Wall], arcs: List[Arc2D], scale_mm_per_px: float
    ) -> List[Door]:
        """检测门"""
        doors = []

        # 方法1: 弧端点落在墙上
        for arc in arcs:
            arc_start = arc.get_start_point()
            arc_end = arc.get_end_point()

            # 检查弧端点是否贴近某面墙
            w1 = self._find_nearest_wall(arc_start, walls, max_dist=30)
            w2 = self._find_nearest_wall(arc_end, walls, max_dist=30)

            if w1 is not None and w2 is not None:
                # 确定门的位置（弧的圆心附近）
                door_pos = arc.center
                # 宽度约为弧半径（门扇通常朝向室内）
                door_width_mm = arc.radius * scale_mm_per_px

                if self.config.door_width_min_mm < door_width_mm < self.config.door_width_max_mm:
                    # 确定开启角度
                    swing = arc.angular_span
                    doors.append(Door(
                        position=door_pos,
                        wall_ref=w1.centerline,
                        width=door_width_mm,
                        swing_angle=90.0,
                        confidence=0.7
                    ))

        return doors

    def _detect_windows(
        self, walls: List[Wall], lines: List[Line2D], scale_mm_per_px: float
    ) -> List[Window]:
        """Detect windows only when walls exist, with strict length filtering."""
        if not walls:
            return []  # No walls = no windows

        windows = []
        for wall in walls:
            wall_windows = self._find_windows_on_wall(wall, lines, scale_mm_per_px)
            windows.extend(wall_windows)

        # Limit: max 4 windows per wall to avoid false positives
        return windows[:len(walls) * 4]

    def _find_windows_on_wall(
        self, wall: Wall, lines: List[Line2D], scale_mm_per_px: float
    ) -> List[Window]:
        """在单面墙上搜索窗户"""
        windows = []
        cl = wall.centerline

        # 取墙中心线方向
        wall_dir_x = cl.p2.x - cl.p1.x
        wall_dir_y = cl.p2.y - cl.p1.y
        wall_length = cl.length
        if wall_length < 1:
            return windows

        # 单位方向向量
        ux = wall_dir_x / wall_length
        uy = wall_dir_y / wall_length

        # 搜索平行于墙但间隙很小的线对（窗户的两条边线）
        # 这些线应该: (1) 与墙平行，(2) 间距在窗厚度范围内，(3) 在墙的投影范围内

        window_thickness_min_px = self.config.window_thickness_mm / scale_mm_per_px
        window_thickness_max_px = self.config.window_thickness_max_mm / scale_mm_per_px

        # Filter for short lines parallel to wall, near the wall
        parallel_short = []
        min_win_len = max(20, wall_length * 0.05)  # At least 5% of wall or 20px
        for line in lines:
            if line.length > wall_length * 0.7:
                continue  # Too long for a window
            if line.length < min_win_len:
                continue  # Too short, probably noise
            angle_diff = abs(cl.angle_deg - line.angle_deg)
            if angle_diff > 180 - angle_diff:
                angle_diff = 180 - angle_diff
            if angle_diff > 10:
                continue
            dist_to_wall = cl.distance_to_point(line.midpoint)
            if dist_to_wall < wall.thickness * 2:
                parallel_short.append(line)

        # 找到距离在窗户厚度范围内的平行线对
        for i in range(len(parallel_short)):
            for j in range(i + 1, len(parallel_short)):
                l1 = parallel_short[i]
                l2 = parallel_short[j]

                # 计算间距
                d1 = l2.distance_to_point(l1.p1)
                d2 = l2.distance_to_point(l1.p2)
                avg_dist = (d1 + d2) / 2

                if window_thickness_min_px < avg_dist < window_thickness_max_px:
                    # 计算窗的中点位置
                    mid = Point2D(
                        (l1.midpoint.x + l2.midpoint.x) / 2,
                        (l1.midpoint.y + l2.midpoint.y) / 2
                    )
                    win_length = (l1.length + l2.length) / 2 * scale_mm_per_px

                    windows.append(Window(
                        position=mid,
                        wall_ref=cl,
                        length=win_length,
                        thickness=avg_dist * scale_mm_per_px,
                        confidence=0.6
                    ))

        return windows

    @staticmethod
    def _find_nearest_wall(pt: Point2D, walls: List[Wall], max_dist: float) -> Optional[Wall]:
        """找到离给定点最近的墙体"""
        best = None
        best_dist = max_dist
        for wall in walls:
            dist = wall.centerline.distance_to_point(pt)
            if dist < best_dist:
                best_dist = dist
                best = wall
        return best
