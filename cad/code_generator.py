"""Code generator — maps detected geometry to AutoCAD drawing commands.

All geometry drawn on layer 0 (no layer switches to avoid -LAYER SCR issues).
"""

from typing import List, Tuple
import math

from core.geometry import (
    Line2D, Circle2D, Arc2D, Polyline, Wall, Door, Window,
    TreeSymbol, WaterFeature, PathLine, Point2D
)
from cad.cad_commands import (
    cmd_line, cmd_circle, cmd_arc_3pt, cmd_pline, cmd_hatch
)


class CodeGenerator:
    """Generates AutoCAD drawing commands (no layer management)."""

    def __init__(self, layer_manager=None):
        pass

    def generate(self, geometry_list: List, scale_factor: float) -> str:
        lines: List[str] = []
        for geom in geometry_list:
            cmd = self._dispatch(geom, scale_factor)
            if cmd:
                lines.append(cmd)
        return "\n".join(lines)

    def _dispatch(self, geom, factor: float) -> str:
        if isinstance(geom, Wall): return self._gen_wall(geom, factor)
        elif isinstance(geom, Line2D): return self._gen_line(geom, factor)
        elif isinstance(geom, Circle2D): return self._gen_circle(geom, factor)
        elif isinstance(geom, Arc2D): return self._gen_arc(geom, factor)
        elif isinstance(geom, Polyline): return self._gen_polyline(geom, factor)
        elif isinstance(geom, Door): return self._gen_door(geom, factor)
        elif isinstance(geom, Window): return self._gen_window(geom, factor)
        elif isinstance(geom, TreeSymbol): return self._gen_tree(geom, factor)
        elif isinstance(geom, WaterFeature): return self._gen_water(geom, factor)
        elif isinstance(geom, PathLine): return self._gen_path(geom, factor)
        return ""

    def _s(self, pt: Point2D, f: float) -> Tuple[float, float]:
        return (pt.x * f, pt.y * f)

    def _gen_wall(self, w: Wall, f: float) -> str:
        p1 = self._s(w.centerline.p1, f)
        p2 = self._s(w.centerline.p2, f)
        t = w.thickness * f  # px -> mm
        if t < 1:
            t = 100  # minimum visible wall thickness
        pts = [(p1[0], p1[1]), (p2[0], p2[1])]
        return cmd_pline(pts, width=t, closed=False)

    def _gen_line(self, l: Line2D, f: float) -> str:
        p1 = self._s(l.p1, f); p2 = self._s(l.p2, f)
        return cmd_line(p1[0], p1[1], p2[0], p2[1])

    def _gen_circle(self, c: Circle2D, f: float) -> str:
        cx, cy = self._s(c.center, f)
        return cmd_circle(cx, cy, c.radius * f)

    def _gen_arc(self, a: Arc2D, f: float) -> str:
        p1 = self._s(a.get_start_point(), f)
        pm = self._s(a.get_mid_point(), f)
        p3 = self._s(a.get_end_point(), f)
        return cmd_arc_3pt(p1[0], p1[1], pm[0], pm[1], p3[0], p3[1])

    def _gen_polyline(self, pl: Polyline, f: float) -> str:
        pts = [self._s(p, f) for p in pl.points]
        return cmd_pline(pts, width=0, closed=pl.closed)

    def _gen_door(self, d: Door, f: float) -> str:
        px, py = self._s(d.position, f)
        dw = d.width * f
        rad = math.radians(d.swing_angle)
        ex, ey = px + dw * math.cos(rad), py - dw * math.sin(rad)
        mx, my = px + dw * math.cos(rad/2), py - dw * math.sin(rad/2)
        return cmd_line(px, py, ex, ey) + "\n" + cmd_arc_3pt(px, py, mx, my, ex, ey)

    def _gen_window(self, w: Window, f: float) -> str:
        px, py = self._s(w.position, f)
        hl = w.length * f / 2; ht = w.thickness * f / 2
        return (cmd_line(px - hl, py - ht, px + hl, py - ht) + "\n" +
                cmd_line(px - hl, py + ht, px + hl, py + ht))

    def _gen_tree(self, t: TreeSymbol, f: float) -> str:
        cx, cy = self._s(t.center, f)
        return cmd_circle(cx, cy, t.radius * f)

    def _gen_water(self, w: WaterFeature, f: float) -> str:
        pts = [self._s(p, f) for p in w.contour]
        return cmd_hatch("AR-HBONE", 50.0, 0, pts)

    def _gen_path(self, p: PathLine, f: float) -> str:
        pts = [self._s(pt, f) for pt in p.polyline]
        return cmd_pline(pts, width=p.width * f, closed=False)
