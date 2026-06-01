"""图片加载与格式校验"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

from config.app_config import AppConfig


class ImageLoader:
    """图片加载器，支持常见图像格式"""

    def __init__(self, config: AppConfig):
        self.config = config
        self._current_path: Optional[Path] = None

    @property
    def current_path(self) -> Optional[Path]:
        return self._current_path

    def load(self, path: str | Path) -> Tuple[np.ndarray, Tuple[int, int]]:
        """加载图片并返回 (BGR数组, (宽, 高))

        Args:
            path: 图片文件路径

        Returns:
            (image_bgr, (width, height))

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的格式或无法读取
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        suffix = path.suffix.lower()
        if suffix not in self.config.supported_formats:
            raise ValueError(f"不支持的图片格式: {suffix}。支持的格式: {self.config.supported_formats}")

        # 使用 np.fromfile + cv2.imdecode 加载（支持中文路径）
        try:
            img_array = np.fromfile(str(path), dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception:
            img = None

        if img is None:
            # 尝试用 Pillow 中转（处理特殊编码的 TIFF 等）
            img = self._load_via_pillow(path)

        if img is None:
            raise ValueError(f"无法读取图片文件: {path}")

        self._current_path = path
        h, w = img.shape[:2]
        return img, (w, h)

    def _load_via_pillow(self, path: Path) -> Optional[np.ndarray]:
        """使用 Pillow 加载特殊格式图片并转为 numpy 数组"""
        try:
            from PIL import Image
            pil_img = Image.open(str(path))
            pil_img = pil_img.convert("RGB")
            arr = np.array(pil_img)
            # PIL RGB → OpenCV BGR
            return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        except Exception:
            return None

    def validate(self, img: np.ndarray) -> bool:
        """校验图片是否可用"""
        if img is None:
            return False
        if len(img.shape) not in (2, 3):
            return False
        h, w = img.shape[:2]
        if h < 10 or w < 10:
            return False
        return True
