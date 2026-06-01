"""Precise raster-to-vector converter for CAD drawings.

Uses Potrace (industrial-grade engine) for curve/line extraction,
with OpenCV preprocessing and skeleton fallback.
"""

import os, subprocess, tempfile
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple

from core.geometry import Line2D, Circle2D, Polyline, Point2D


PROJECT_ROOT = Path(__file__).parent.parent
POTRACE = str(PROJECT_ROOT / "tools" / "potrace.exe")


class Vectorizer:
    """Convert raster CAD image to precise vector geometry."""

    def __init__(self):
        self._potrace_ok = os.path.exists(POTRACE)

    def detect(self, img: np.ndarray) -> List:
        """Extract all visible geometry from a CAD image.

        Uses Potrace for precise curves -> polylines,
        plus Hough for straight lines, plus contour detection.
        """
        h, w = img.shape[:2]

        # Step 1: Preprocess
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 7, 50, 50)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Step 2: Morphological cleaning
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        result = []

        # Step 3: Potrace (precise vectorization)
        if self._potrace_ok:
            potrace_objs = self._run_potrace(binary, w, h)
            # Filter Potrace: only keep significant segments
            min_pts = 5
            for obj in potrace_objs:
                if isinstance(obj, Polyline) and obj.point_count >= min_pts:
                    total_len = sum(obj.points[i].distance_to(obj.points[i+1])
                                    for i in range(obj.point_count-1))
                    if total_len > min(w, h) * 0.03:  # >3% of image diagonal
                        result.append(obj)

        # Step 4: Hough lines (supplemental straight lines)
        edges = cv2.Canny(gray, 30, 100)
        min_line_len = int(min(w, h) * 0.02)  # 2% of image size = main structure only
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40,
                                 minLineLength=min_line_len, maxLineGap=20)
        if lines is not None:
            for x1, y1, x2, y2 in lines[:, 0]:
                result.append(Line2D(Point2D(x1, y1), Point2D(x2, y2), 0.95))

        # Step 5: Circles (only distinct ones)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=30,
                                    param1=50, param2=35, minRadius=8,
                                    maxRadius=min(w, h)//4)
        if circles is not None:
            for cx, cy, r in circles[0]:
                result.append(Circle2D(Point2D(cx, cy), r, 0.9))

        # Step 6: Contours (only significant areas)
        min_area = int(min(w, h) * min(w, h) * 0.0005)  # 0.05% of image
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                epsilon = 0.005 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                if len(approx) >= 3:
                    pts = [Point2D(p[0][0], p[0][1]) for p in approx]
                    closed = pts[0].distance_to(pts[-1]) < 10
                    result.append(Polyline(pts, closed=closed))

        return self._dedup(result)

    def _run_potrace(self, binary: np.ndarray, img_w: int, img_h: int) -> List:
        """Run Potrace on a binary image, return polylines."""
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as f_in:
            cv2.imwrite(f_in.name, binary)
            out_svg = f_in.name + ".svg"
            try:
                subprocess.run(
                    [POTRACE, "-b", "svg", "-o", out_svg, f_in.name],
                    capture_output=True, timeout=30, check=True)
                return self._parse_svg(out_svg, img_w, img_h)
            except Exception:
                return []
            finally:
                for f in [f_in.name, out_svg]:
                    try: os.unlink(f)
                    except OSError: pass

    @staticmethod
    def _parse_svg(svg_path: str, img_w: int, img_h: int) -> List:
        """Parse SVG output from Potrace into Polyline objects."""
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg = f.read()
        except Exception:
            return []

        import re
        result = []
        # Find all path elements
        for m in re.finditer(r'<path[^>]*d="([^"]*)"', svg):
            path = m.group(1)
            pts = []
            # Parse SVG path: M x y L x y L x y ... or M x y C ...
            nums = re.findall(r'([-]?\d+\.?\d*)', path.replace(",", " "))
            coords = [float(x) for x in nums]
            # "M x y" starts, then "L x y" or "C x1 y1 x2 y2 x y" continues
            i = 0
            current_pts = []
            while i < len(coords) - 1:
                cmd_idx = i
                x, y = coords[i], coords[i+1]
                current_pts.append(Point2D(x, y))
                i += 2
                # Heuristic: group segments by proximity
                if len(current_pts) >= 2:
                    last = current_pts[-1]
                    prev = current_pts[-2]
                    if last.distance_to(prev) > 500:
                        if len(current_pts) >= 3:
                            result.append(Polyline(current_pts[:-1], closed=current_pts[0].distance_to(current_pts[-2]) < 5))
                        current_pts = [current_pts[-1]]
            if len(current_pts) >= 3:
                result.append(Polyline(current_pts, closed=current_pts[0].distance_to(current_pts[-1]) < 5))

        return result

    @staticmethod
    def _dedup(objects: List) -> List:
        """Aggressive merge: combine overlapping collinear segments."""
        lines = [o for o in objects if isinstance(o, Line2D)]
        others = [o for o in objects if not isinstance(o, Line2D)]
        if len(lines) <= 1:
            return objects

        import math
        kept = []
        used = [False] * len(lines)
        for i, l1 in enumerate(lines):
            if used[i]: continue
            merged = l1
            for j, l2 in enumerate(lines):
                if i == j or used[j]: continue
                if l1.length < 5 or l2.length < 5: continue
                a1, a2 = l1.angle_deg, l2.angle_deg
                diff = abs(a1 - a2)
                if diff > 180 - diff: diff = 180 - diff
                # Wide angle tolerance for rough sketch lines
                if diff > 20: continue
                # Check if close enough
                d1 = l2.distance_to_point(l1.p1)
                d2 = l2.distance_to_point(l1.p2)
                d3 = l1.distance_to_point(l2.p1)
                d4 = l1.distance_to_point(l2.p2)
                if min(d1, d2, d3, d4) < 25:
                    pts = [l1.p1, l1.p2, l2.p1, l2.p2]
                    xs = [p.x for p in pts]; ys = [p.y for p in pts]
                    merged = Line2D(Point2D(min(xs), min(ys)),
                                    Point2D(max(xs), max(ys)), 0.95)
                    used[j] = True
            kept.append(merged)
        return kept + others
