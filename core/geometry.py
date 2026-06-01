"""所有几何数据类定义

所有检测器模块的输出和 CAD 代码生成层的输入都使用这些数据类。
坐标系统：原始检测结果使用像素坐标；生成 CAD 代码时通过 scale_factor 转换为 mm。
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class Point2D:
    """二维点"""
    x: float
    y: float

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def to_int_tuple(self) -> Tuple[int, int]:
        return (int(round(self.x)), int(round(self.y)))

    def __add__(self, other: "Point2D") -> "Point2D":
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point2D") -> "Point2D":
        return Point2D(self.x - other.x, self.y - other.y)

    def distance_to(self, other: "Point2D") -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5

    def scaled(self, factor: float) -> "Point2D":
        """按比例缩放"""
        return Point2D(self.x * factor, self.y * factor)


@dataclass
class Line2D:
    """线段"""
    p1: Point2D
    p2: Point2D
    confidence: float = 1.0  # 0.0 ~ 1.0，来自霍夫累加器的归一化置信度

    @property
    def length(self) -> float:
        return self.p1.distance_to(self.p2)

    @property
    def midpoint(self) -> Point2D:
        return Point2D((self.p1.x + self.p2.x) / 2, (self.p1.y + self.p2.y) / 2)

    @property
    def slope(self) -> float:
        """返回弧度角 [-pi/2, pi/2]"""
        import math
        dx = self.p2.x - self.p1.x
        dy = self.p2.y - self.p1.y
        if abs(dx) < 1e-9:
            return math.pi / 2 if dy > 0 else -math.pi / 2
        return math.atan2(dy, dx)

    @property
    def angle_deg(self) -> float:
        """返回角度 [0, 180)"""
        import math
        deg = math.degrees(self.slope)
        if deg < 0:
            deg += 180
        if deg >= 180:
            deg -= 180
        return deg

    def is_horizontal(self, tolerance_deg: float = 15.0) -> bool:
        """判断是否接近水平"""
        a = self.angle_deg
        return a <= tolerance_deg or a >= 180 - tolerance_deg

    def is_vertical(self, tolerance_deg: float = 15.0) -> bool:
        """判断是否接近垂直"""
        a = self.angle_deg
        return 90 - tolerance_deg <= a <= 90 + tolerance_deg

    def projection_onto_x(self) -> Tuple[float, float]:
        """在 X 轴上的投影区间 (min_x, max_x)"""
        return (min(self.p1.x, self.p2.x), max(self.p1.x, self.p2.x))

    def projection_onto_y(self) -> Tuple[float, float]:
        """在 Y 轴上的投影区间 (min_y, max_y)"""
        return (min(self.p1.y, self.p2.y), max(self.p1.y, self.p2.y))

    def distance_to_point(self, pt: Point2D) -> float:
        """点到线段的距离"""
        import math
        dx = self.p2.x - self.p1.x
        dy = self.p2.y - self.p1.y
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            return pt.distance_to(self.p1)
        t = ((pt.x - self.p1.x) * dx + (pt.y - self.p1.y) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        proj = Point2D(self.p1.x + t * dx, self.p1.y + t * dy)
        return pt.distance_to(proj)


@dataclass
class Circle2D:
    """圆"""
    center: Point2D
    radius: float
    confidence: float = 1.0


@dataclass
class Arc2D:
    """圆弧"""
    center: Point2D
    radius: float
    start_angle: float   # 起始角度（度，0° = +X 方向即东，逆时针）
    end_angle: float     # 结束角度（度）
    confidence: float = 1.0

    def get_start_point(self) -> Point2D:
        """计算圆弧起点"""
        import math
        rad = math.radians(self.start_angle)
        return Point2D(
            self.center.x + self.radius * math.cos(rad),
            self.center.y - self.radius * math.sin(rad)  # Y轴向下（图像坐标）
        )

    def get_end_point(self) -> Point2D:
        """计算圆弧终点"""
        import math
        rad = math.radians(self.end_angle)
        return Point2D(
            self.center.x + self.radius * math.cos(rad),
            self.center.y - self.radius * math.sin(rad)
        )

    def get_mid_point(self) -> Point2D:
        """计算圆弧中点"""
        import math
        mid_angle = (self.start_angle + self.end_angle) / 2
        rad = math.radians(mid_angle)
        return Point2D(
            self.center.x + self.radius * math.cos(rad),
            self.center.y - self.radius * math.sin(rad)
        )

    @property
    def angular_span(self) -> float:
        """圆弧的角度跨度（度）"""
        span = self.end_angle - self.start_angle
        if span < 0:
            span += 360
        return span


@dataclass
class Polyline:
    """多段线"""
    points: List[Point2D]
    closed: bool = False

    @property
    def point_count(self) -> int:
        return len(self.points)

    def to_tuple_list(self) -> List[Tuple[float, float]]:
        return [p.to_tuple() for p in self.points]


@dataclass
class Wall:
    """墙体"""
    centerline: Line2D           # 墙中心线
    thickness: float             # 墙厚（像素）
    points: List[Point2D] = field(default_factory=list)  # 4个角点（矩形墙体）
    confidence: float = 1.0

    @property
    def length(self) -> float:
        return self.centerline.length

    def get_corner_points(self) -> List[Point2D]:
        """计算墙体4个角点（如果有中心线+厚度）"""
        if self.points:
            return self.points

        import math
        dx = self.centerline.p2.x - self.centerline.p1.x
        dy = self.centerline.p2.y - self.centerline.p1.y
        length = self.centerline.length
        if length < 1e-9:
            return [self.centerline.p1] * 4

        # 垂直方向单位向量
        nx = -dy / length
        ny = dx / length
        half_t = self.thickness / 2

        p1 = self.centerline.p1
        p2 = self.centerline.p2

        return [
            Point2D(p1.x + nx * half_t, p1.y + ny * half_t),
            Point2D(p2.x + nx * half_t, p2.y + ny * half_t),
            Point2D(p2.x - nx * half_t, p2.y - ny * half_t),
            Point2D(p1.x - nx * half_t, p1.y - ny * half_t),
        ]


@dataclass
class Door:
    """门"""
    position: Point2D           # 门的位置（铰链侧）
    wall_ref: Optional[Line2D]  # 所在墙体的中心线引用
    width: float = 800.0        # 门宽（mm）
    swing_angle: float = 90.0   # 门扇开启角度（度，0=沿X+方向）
    confidence: float = 1.0


@dataclass
class Window:
    """窗"""
    position: Point2D           # 窗的中点
    wall_ref: Optional[Line2D]  # 所在墙体的中心线引用
    length: float = 1200.0      # 窗长度（mm）
    thickness: float = 200.0    # 窗厚度（mm）
    confidence: float = 1.0


@dataclass
class TreeSymbol:
    """树符号"""
    center: Point2D
    radius: float
    confidence: float = 1.0


@dataclass
class WaterFeature:
    """水体特征"""
    contour: List[Point2D]      # 闭合多边形轮廓
    area: float = 0.0           # 面积（像素²）
    confidence: float = 1.0


@dataclass
class PathLine:
    """道路/路径"""
    polyline: List[Point2D]     # 道路中线
    width: float = 1200.0       # 道路宽度（mm）
    confidence: float = 1.0


# === 类型别名 ===
GeometryList = List[
    Line2D | Circle2D | Arc2D | Polyline | Wall | Door | Window | TreeSymbol | WaterFeature | PathLine
]
