"""LSD (Line Segment Detector) for CAD drawing line detection.

LSD produces sub-pixel accurate line segments and is often better
than HoughLinesP for technical drawings with clean straight lines.

Requires opencv-contrib-python for cv2.ximgproc.createFastLineDetector.
Falls back to HoughLinesP if unavailable.
"""

import cv2
import numpy as np
from typing import List

from config.app_config import AppConfig
from core.geometry import Line2D, Point2D


class LSDDetector:
    """LSD-based line segment detector for CAD blueprints."""

    def __init__(self, config: AppConfig):
        self.config = config
        self._fld = None
        self._available = False
        try:
            # Try to create FLD (Fast Line Detector) from ximgproc
            self._fld = cv2.ximgproc.createFastLineDetector(
                config.lsd_length_threshold,
                config.lsd_distance_threshold,
                config.canny_low,
                config.canny_high,
                3,
                config.lsd_merge
            )
            self._available = True
        except (AttributeError, cv2.error):
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def detect(self, gray: np.ndarray) -> List[Line2D]:
        """Detect line segments using LSD.

        Args:
            gray: Grayscale image.

        Returns:
            List of detected Line2D objects.
        """
        if not self._available:
            return []

        try:
            lines = self._fld.detect(gray)
            if lines is None or len(lines) == 0:
                return []

            result = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                result.append(Line2D(
                    p1=Point2D(float(x1), float(y1)),
                    p2=Point2D(float(x2), float(y2)),
                    confidence=0.9  # LSD lines are high quality
                ))
            return result

        except cv2.error:
            return []
