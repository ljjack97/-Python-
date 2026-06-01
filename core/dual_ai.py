"""Dual-AI pipeline: Vision AI detects, Text AI generates precise SCR.

Stage 1: Vision model (step-1o-vision-32k) analyzes image, outputs structured JSON.
Stage 2: Text model (step-3) takes JSON, fixes coordinates, generates exact SCR.
"""

import json, base64, cv2, numpy as np
from typing import List
from urllib import request


class DualAI:
    """Two-stage AI: detect with vision, generate code with text model."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._available = bool(api_key)

    @property
    def available(self) -> bool:
        return self._available

    def detect_and_generate(self, img: np.ndarray) -> str:
        """Full pipeline: detect -> generate SCR.

        Returns complete SCR script text ready to save.
        """
        if not self._available:
            return ""

        # Stage 1: Vision detection
        detection = self._stage1_detect(img)
        if not detection:
            return ""

        # Stage 2: Text model generates precise SCR
        scr = self._stage2_generate(detection, img.shape[1], img.shape[0])
        return scr

    def _stage1_detect(self, img: np.ndarray) -> dict:
        """Vision model: analyze image, output detailed structured description."""
        import cv2
        h, w = img.shape[:2]
        s = min(1.0, 2048 / max(w, h))
        img_s = cv2.resize(img, (int(w*s), int(h*s))) if s < 1 else img
        h2, w2 = img_s.shape[:2]

        rgb = cv2.cvtColor(img_s, cv2.COLOR_BGR2RGB)
        _, buf = cv2.imencode('.jpg', rgb, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_b64 = base64.b64encode(buf).decode()

        prompt = f"""Analyze this drawing ({w2}x{h2}px). Identify ALL visible elements.
Output a JSON object with these keys:
{{
  "elements": [
    {{"type":"line","x1":int,"y1":int,"x2":int,"y2":int}},
    {{"type":"circle","cx":int,"cy":int,"radius":int}},
    {{"type":"arc","x1":int,"y1":int,"x2":int,"y2":int,"x3":int,"y3":int}},
    {{"type":"polyline","points":[[int,int],...],"closed":bool}}
  ],
  "scale_estimate_mm_per_px": 10.0
}}
Be EXTREMELY thorough. List EVERY visible line, every curve, every shape.
Coordinates MUST be in pixels relative to the {w2}x{h2} image.
Return ONLY the JSON object, no markdown, no extra text."""

        data = json.dumps({
            "model": "step-1o-vision-32k",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}"}}
            ]}],
            "max_tokens": 8192, "temperature": 0.1
        }).encode()

        try:
            req = request.Request(
                "https://api.stepfun.com/v1/chat/completions", data=data,
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"})
            req.timeout = 120
            with request.urlopen(req) as resp:
                r = json.loads(resp.read().decode())
            text = r["choices"][0]["message"]["content"].strip()
            if text.startswith("```"): text = text.split("\n", 1)[1].split("\n```")[0]
            return json.loads(text)
        except Exception:
            return {}

    def _stage2_generate(self, detection: dict, orig_w: int, orig_h: int) -> str:
        """Text model: take detection JSON, generate precise SCR script.

        The text model can think step-by-step about coordinate precision,
        fixing AI rounding errors and ensuring valid AutoCAD commands.
        """
        elements_json = json.dumps(detection, indent=2)

        prompt = f"""Convert this CAD detection data to an AutoCAD .scr script.
Image: {orig_w}x{orig_h}px. Scale: multiply pixel coords by 10 for mm.

Elements:
{elements_json}

Generate SCR using newline format (one value per line, blank line ends command):
  LINE\\nx1,y1\\nx2,y2\\n\\n
  CIRCLE\\ncx,cy\\nradius\\n
  ARC\\nx1,y1\\nx2,y2\\nx3,y3\\n
  PLINE\\nx1,y1\\nx2,y2\\nC\\n\\n
End with: ZOOM\\nE

IMPORTANT: Output ONLY the SCR commands. NO explanations, NO markdown, NO extra text. Just raw SCR."""

        data = json.dumps({
            "model": "step-3",  # Strong text model for precise code generation
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 16384, "temperature": 0.0
        }).encode()

        try:
            req = request.Request(
                "https://api.stepfun.com/v1/chat/completions", data=data,
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"})
            req.timeout = 120
            with request.urlopen(req) as resp:
                r = json.loads(resp.read().decode())
            text = r["choices"][0]["message"]["content"].strip()
            if text.startswith("```"): text = text.split("\n", 1)[1].rsplit("\n```", 1)[0]
            text = r["choices"][0]["message"]["content"].strip()
            if text.startswith("```"): text = text.split("\n", 1)[1].rsplit("\n```", 1)[0]
            # Keep only valid SCR: LINE/CIRCLE/ARC/PLINE/ZOOM + coord lines
            valid = []
            for line in text.split("\n"):
                s = line.strip().upper()
                if not s: valid.append("")
                elif any(s.startswith(c) for c in ["LINE","CIRCLE","ARC","PLINE","ZOOM","RECT"]):
                    valid.append(line.strip())
                elif "," in s: valid.append(line.strip())
            # Ensure single ZOOM E at end
            scr = "\n".join(valid)
            if "ZOOM" in scr:
                scr = scr[:scr.rfind("ZOOM")].rstrip()
            scr = scr.rstrip() + "\nZOOM\nE"
            return scr
        except Exception:
            return ""
