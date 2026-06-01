"""Image preprocessor — grayscale, enhance, threshold, denoise.

Pipeline: grayscale -> CLAHE -> bilateral denoise -> gentle blur
         -> adaptive threshold -> morphological close -> morphological open
(Sharpening removed — caused mosaic artifacts with CLAHE tile boundaries.)
"""

import cv2
import numpy as np
from typing import Tuple

from config.app_config import AppConfig


class Preprocessor:
    """Image preprocessor for CAD blueprint detection."""

    def __init__(self, config: AppConfig):
        self.config = config

    def process(self, img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Full preprocessing pipeline.

        Returns:
            (binary_image, gray_image)
        """
        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. CLAHE contrast enhancement (gentle, large tiles)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16, 16))
        enhanced = clahe.apply(gray)

        # 3. Bilateral filter — denoise while preserving edges
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)

        # 4. Gentle Gaussian blur — smooth before threshold (avoids mosaic)
        enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0.5)

        # 5. Adaptive threshold
        block = self.config.adaptive_thresh_block
        if block % 2 == 0:
            block += 1
        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            block,
            self.config.adaptive_thresh_c
        )

        # 6. Morphological close — bridge small gaps in lines
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close)

        # 7. Morphological open — remove salt noise
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)

        return binary, enhanced

    def get_preview(self, img: np.ndarray) -> np.ndarray:
        """Generate side-by-side preview: original | enhanced | binary"""
        binary, enhanced = self.process(img)

        binary_color = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        gray_orig = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        orig_display = cv2.cvtColor(gray_orig, cv2.COLOR_GRAY2BGR)
        enhanced_display = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        h_img, w_img = img.shape[:2]
        scale = min(1.0, 900 / (w_img * 3))
        new_w = int(w_img * scale)
        new_h = int(h_img * scale)

        orig_display = cv2.resize(orig_display, (new_w, new_h))
        enhanced_display = cv2.resize(enhanced_display, (new_w, new_h))
        binary_color = cv2.resize(binary_color, (new_w, new_h))

        labels = ["Original", "Enhanced", "Binary"]
        displays = [orig_display, enhanced_display, binary_color]
        for disp, label in zip(displays, labels):
            cv2.putText(disp, label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)

        return np.hstack(displays)

    def to_binary(self, img: np.ndarray) -> np.ndarray:
        binary, _ = self.process(img)
        return binary
