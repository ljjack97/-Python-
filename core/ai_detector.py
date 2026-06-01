"""AI-powered CAD drawing detector.

Supports two providers:
- Step-2V (阶跃星辰): domestic, strongest vision model, OpenAI-compatible API
- Qwen-VL (通义千问): domestic, good value, DashScope API
"""

import json
import base64
import numpy as np
from typing import List


class AIDetector:
    """Detect CAD features using AI vision models."""

    PROMPT = """Analyze this CAD/landscape drawing ({w}x{h}px). IGNORE the outer frame/border.
Find ALL visible drawing content INSIDE the frame. Return ONLY JSON:

{{
  "walls": [{{"x1":int,"y1":int,"x2":int,"y2":int,"thickness_px":int}}],
  "doors": [{{"x":int,"y":int,"width_px":int,"angle_deg":int}}],
  "windows": [{{"x":int,"y":int,"length_px":int}}],
  "circles": [{{"cx":int,"cy":int,"radius_px":int}}],
  "lines": [{{"x1":int,"y1":int,"x2":int,"y2":int}}],
  "scale_mm_per_px": 10.0
}}

CRITICAL: IGNORE the outermost rectangle/frame/border. Only detect content INSIDE it.

For architectural drawings:
- walls: EVERY visible wall. thickness_px = visible thickness in px.
- doors: arcs between wall gaps
- windows: short parallel lines in walls

For landscape/garden drawings:
- USE "lines" for boundary lines, paths, edges, curved lines, ANY visible line
- USE "circles" for trees, planting spots, round features
- If no walls exist, return empty walls array and put ALL lines in "lines"

Be exhaustive. Return ALL visible drawing elements."""

    def __init__(self, api_key: str = "", provider: str = "step"):
        self.api_key = api_key
        self.provider = provider
        self._available = bool(api_key)

    @property
    def available(self) -> bool:
        return self._available

    def configure(self, api_key: str, provider: str = "step"):
        self.api_key = api_key
        self.provider = provider
        self._available = bool(api_key)

    def detect(self, img: np.ndarray) -> List:
        if not self._available:
            return []
        import cv2
        h, w = img.shape[:2]
        if max(w, h) > 3000:
            return self._detect_tiled(img)
        return self._detect_single(img)

    def _detect_single(self, img: np.ndarray) -> List:
        import cv2
        h, w = img.shape[:2]
        if max(w, h) > 4096:
            s = 4096 / max(w, h)
            img = cv2.resize(img, (int(w*s), int(h*s)), interpolation=cv2.INTER_AREA)
            h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        _, buf = cv2.imencode('.jpg', rgb, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_b64 = base64.b64encode(buf).decode()
        prompt = self.PROMPT.format(w=w, h=h)
        return self._call_step(prompt, img_b64, w, h) if self.provider == "step" else self._call_qwen(prompt, img_b64, w, h)

    def _detect_tiled(self, img: np.ndarray) -> List:
        import cv2
        h, w = img.shape[:2]
        TS, OV = 2048, 256
        all_objs = []
        y = 0
        while y < h:
            x = 0
            while x < w:
                x2, y2 = min(x+TS, w), min(y+TS, h)
                tile = img[y:y2, x:x2]
                if tile.shape[1] >= 300 and tile.shape[0] >= 300:
                    objs = self._detect_single(tile)
                    for obj in objs:
                        self._offset(obj, x, y)
                    all_objs.extend(objs)
                x += TS - OV
            y += TS - OV
        return self._dedup_walls(all_objs)

    @staticmethod
    def _offset(obj, dx, dy):
        if hasattr(obj, 'centerline'):
            obj.centerline.p1.x += dx; obj.centerline.p1.y += dy
            obj.centerline.p2.x += dx; obj.centerline.p2.y += dy
        if hasattr(obj, 'position'): obj.position.x += dx; obj.position.y += dy
        if hasattr(obj, 'center'): obj.center.x += dx; obj.center.y += dy
        if hasattr(obj, 'points'):
            for p in obj.points: p.x += dx; p.y += dy
        if hasattr(obj, 'contour'):
            for p in obj.contour: p.x += dx; p.y += dy
        if hasattr(obj, 'polyline'):
            for p in obj.polyline: p.x += dx; p.y += dy

    def _call_step(self, prompt: str, img_b64: str, w: int, h: int) -> List:
        """Step-2V API (OpenAI-compatible)."""
        try:
            from urllib import request
            import urllib.error

            data = json.dumps({
                "model": "step-1o-vision-32k",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }],
                "max_tokens": 4096,
                "temperature": 0.1
            }).encode()

            req = request.Request(
                "https://api.stepfun.com/v1/chat/completions",
                data=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            req.timeout = 60

            with request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())

            text = result["choices"][0]["message"]["content"].strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].split("\n```")[0]
            return self._parse_json(text, h, w)

        except Exception:
            return []

    def _call_qwen(self, prompt: str, img_b64: str, w: int, h: int) -> List:
        """Qwen-VL API (DashScope)."""
        try:
            import dashscope
            from dashscope import MultiModalConversation

            dashscope.api_key = self.api_key
            response = MultiModalConversation.call(
                model="qwen-vl-max",
                messages=[{
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{img_b64}"},
                        {"text": prompt}
                    ]
                }]
            )

            if response.status_code != 200:
                return []

            text = response.output.choices[0].message.content[0]["text"].strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].split("\n```")[0]
            return self._parse_json(text, h, w)

        except Exception:
            return []

    @staticmethod
    def _dedup_walls(walls: List) -> List:
        """Merge overlapping walls with similar direction."""
        if len(walls) <= 1:
            return walls
        kept = []
        used = [False] * len(walls)
        for i, w1 in enumerate(walls):
            if used[i]:
                continue
            merged = w1
            for j, w2 in enumerate(walls):
                if i == j or used[j]:
                    continue
                # Check same direction (angle diff < 15 deg)
                a1 = w1.centerline.angle_deg
                a2 = w2.centerline.angle_deg
                diff = abs(a1 - a2)
                if diff > 180 - diff:
                    diff = 180 - diff
                if diff > 15:
                    continue
                # Check distance between midpoints
                d = w1.centerline.midpoint.distance_to(w2.centerline.midpoint)
                # Check thickness similarity
                if w1.thickness > 0 and w2.thickness > 0:
                    tr = max(w1.thickness, w2.thickness) / min(w1.thickness, w2.thickness)
                else:
                    tr = 1
                if d < max(w1.thickness, w2.thickness) * 3 and tr < 3:
                    # Merge: keep the longer one
                    if w2.centerline.length > merged.centerline.length:
                        merged = w2
                    used[j] = True
            kept.append(merged)
        return kept

    def _parse_json(self, text: str, h: int, w: int) -> List:
        """Parse model JSON response into geometry objects."""
        from core.geometry import (
            Line2D, Circle2D, Point2D, Wall, Door, Window
        )
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []

        result = []
        scale = data.get("scale_mm_per_px", 10.0)

        raw_walls = []
        for wd in data.get("walls", []):
            t = wd.get("thickness_px", wd.get("thickness", 20))
            raw_walls.append(Wall(
                centerline=Line2D(Point2D(wd["x1"], wd["y1"]),
                                  Point2D(wd["x2"], wd["y2"])),
                thickness=float(t),
                confidence=0.85))

        # Dedup: merge overlapping walls (same direction, close together)
        result.extend(self._dedup_walls(raw_walls))

        for d in data.get("doors", []):
            w = d.get("width_px", d.get("width", 40))
            result.append(Door(
                position=Point2D(d["x"], d["y"]), wall_ref=None,
                width=float(w),
                swing_angle=d.get("angle_deg", 90), confidence=0.8))

        for w in data.get("windows", []):
            length = w.get("length_px", w.get("length", 60))
            result.append(Window(
                position=Point2D(w["x"], w["y"]), wall_ref=None,
                length=float(length),
                thickness=float(w.get("thickness", 10)),
                confidence=0.8))

        for c in data.get("circles", []):
            r = c.get("radius_px", c.get("radius", 30))
            result.append(Circle2D(
                center=Point2D(c["cx"], c["cy"]),
                radius=float(r), confidence=0.9))

        for line in data.get("lines", []):
            result.append(Line2D(
                Point2D(line["x1"], line["y1"]),
                Point2D(line["x2"], line["y2"]), confidence=0.85))

        return result
