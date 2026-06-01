"""AutoCAD SCR command templates.

Format: one parameter per line, blank line to end command.
This is the official AutoCAD-recommended SCR format.
"""

from typing import List, Tuple


def cmd_line(x1: float, y1: float, x2: float, y2: float) -> str:
    return f"LINE\n{x1:.2f},{y1:.2f}\n{x2:.2f},{y2:.2f}\n\n"


def cmd_circle(cx: float, cy: float, radius: float) -> str:
    return f"CIRCLE\n{cx:.2f},{cy:.2f}\n{radius:.2f}\n"


def cmd_arc_3pt(x1: float, y1: float, x2: float, y2: float,
                x3: float, y3: float) -> str:
    return f"ARC\n{x1:.2f},{y1:.2f}\n{x2:.2f},{y2:.2f}\n{x3:.2f},{y3:.2f}\n"


def cmd_pline(points: List[Tuple[float, float]], width: float = 0.0,
              closed: bool = True) -> str:
    if len(points) < 2:
        return ""

    parts = ["PLINE"]
    parts.append(f"{points[0][0]:.2f},{points[0][1]:.2f}")
    if width > 0:
        parts.append("W")
        parts.append(f"{width:.2f}")
        parts.append(f"{width:.2f}")
    for pt in points[1:]:
        parts.append(f"{pt[0]:.2f},{pt[1]:.2f}")
    if closed:
        parts.append("C")
    parts.append("")   # blank line = exit
    return "\n".join(parts)


def cmd_rect(x1: float, y1: float, x2: float, y2: float,
             width: float = 0.0) -> str:
    if width > 0:
        return f"RECTANG\nW\n{width:.2f}\n{x1:.2f},{y1:.2f}\n{x2:.2f},{y2:.2f}\n"
    return f"RECTANG\n{x1:.2f},{y1:.2f}\n{x2:.2f},{y2:.2f}\n"


def cmd_layer_new(name: str, color_index: int = 7) -> str:
    """Create a layer and set its color.
    -LAYER N name [Enter] [Enter] C color name [Enter] [Enter]
    """
    return f"-LAYER\nN\n{name}\n\nC\n{color_index}\n{name}\n\n"


def cmd_layer_set(name: str) -> str:
    """Switch to layer. -LAYER S name [Enter] [Enter]"""
    return f"-LAYER\nS\n{name}\n\n"


def cmd_hatch(pattern: str, scale: float, angle: float,
              points: List[Tuple[float, float]]) -> str:
    if len(points) < 3:
        return ""
    parts = ["-HATCH", f"P", pattern, f"{scale:.2f}", f"{angle:.2f}", "W"]
    for pt in points:
        parts.append(f"{pt[0]:.2f},{pt[1]:.2f}")
    parts.append("")
    parts.append("")
    return "\n".join(parts)


def cmd_zoom_extents() -> str:
    return "ZOOM\nE\n"
