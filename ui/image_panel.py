"""Image preview panel — displays original image with detection overlay.

Features:
- Scroll wheel / button zoom (10%–400%)
- Pan with left-drag
- Double-click to toggle original/overlay view
- Rubber-band region selection for partial detection
- Right-click context menu
"""

import cv2
import numpy as np
from typing import List, Optional, Tuple

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QPointF, QRect
from PyQt5.QtGui import (
    QImage, QPixmap, QPainter, QPen, QColor, QBrush, QFont, QCursor
)
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMenu, QAction, QPushButton, QRubberBand
)

from core.geometry import (
    Line2D, Circle2D, Arc2D, Polyline, Wall, Door, Window,
    TreeSymbol, WaterFeature, PathLine, Point2D
)
from ui.theme import (
    OVERLAY_RED, OVERLAY_BLUE, OVERLAY_GREEN,
    OVERLAY_CYAN, OVERLAY_YELLOW, PANEL_BG, TEXT_SECONDARY, ACCENT
)


class ImageView(QGraphicsView):
    """Custom image view with zoom, pan, double-click toggle, selection, and resize."""

    double_clicked = pyqtSignal()
    region_selected = pyqtSignal(QRectF)
    region_cleared = pyqtSignal()           # Click outside selection
    region_changed = pyqtSignal(QRectF)     # Resize handle drag
    zoom_changed = pyqtSignal(float)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._zoom = 1.0
        self._selecting = False
        self._sel_origin_view = None
        self._rubber_band = None
        # Resize state
        self._dragging_handle = False
        self._active_handle = None   # 'nw','n','ne','e','se','s','sw','w'
        self._selection_scene = None  # Current selection in scene coords

    # ── Zoom ──────────────────────────────────────────

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        new_zoom = self._zoom * factor
        if 0.1 <= new_zoom <= 4.0:
            self._zoom = new_zoom
            self.scale(factor, factor)
            self.zoom_changed.emit(self._zoom)

    def zoom_in(self): self._zoom = min(4.0, self._zoom * 1.25); self.scale(1.25, 1.25); self.zoom_changed.emit(self._zoom)
    def zoom_out(self): self._zoom = max(0.1, self._zoom / 1.25); self.scale(1/1.25, 1/1.25); self.zoom_changed.emit(self._zoom)
    def zoom_fit(self): self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio); self._zoom = self.transform().m11(); self.zoom_changed.emit(self._zoom)

    @property
    def zoom_level(self) -> float: return self._zoom

    def set_selection(self, rect: QRectF):
        """Store selection for click-outside and resize detection."""
        self._selection_scene = rect

    def clear_selection(self):
        self._selection_scene = None
        self._active_handle = None

    # ── Rubber-band selection ──

    def _start_selection(self):
        self._selection_scene = None
        self._selecting = True
        self.setCursor(Qt.CrossCursor)
        self.setDragMode(QGraphicsView.NoDrag)

    def _end_selection(self):
        self._selecting = False; self._sel_origin_view = None
        if self._rubber_band: self._rubber_band.hide(); self._rubber_band = None
        self.setCursor(Qt.ArrowCursor); self.setDragMode(QGraphicsView.ScrollHandDrag)

    def _get_handles(self, scene_rect: QRectF) -> dict:
        """Return dict of handle_name -> QPointF (scene coords)."""
        r = scene_rect
        return {
            'nw': r.topLeft(),     'n': QPointF(r.center().x(), r.top()),
            'ne': r.topRight(),    'e': QPointF(r.right(), r.center().y()),
            'se': r.bottomRight(), 's': QPointF(r.center().x(), r.bottom()),
            'sw': r.bottomLeft(),  'w': QPointF(r.left(), r.center().y()),
        }

    def _hit_handle(self, pos: QPointF) -> str | None:
        """Check if view pos hits a handle. Returns handle name or None."""
        if self._selection_scene is None:
            return None
        scene_pos = self.mapToScene(pos)
        # Handle radius in pixels (screen space) — match 10px visual size
        radius = 12 / max(self._zoom, 0.1)
        for name, hp in self._get_handles(self._selection_scene).items():
            dx = scene_pos.x() - hp.x(); dy = scene_pos.y() - hp.y()
            if (dx*dx + dy*dy) < radius*radius:
                return name
        return None

    def _hit_selection(self, pos) -> bool:
        """Check if view pos is inside the selection rect."""
        if self._selection_scene is None:
            return False
        return self._selection_scene.contains(self.mapToScene(pos))

    def _cursor_for_handle(self, name: str) -> Qt.CursorShape:
        cursors = {'nw': Qt.SizeFDiagCursor, 'se': Qt.SizeFDiagCursor,
                   'ne': Qt.SizeBDiagCursor, 'sw': Qt.SizeBDiagCursor,
                   'n': Qt.SizeVerCursor, 's': Qt.SizeVerCursor,
                   'e': Qt.SizeHorCursor, 'w': Qt.SizeHorCursor}
        return cursors.get(name, Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if self._selecting and event.button() == Qt.LeftButton:
            self._sel_origin_view = event.pos()
            if self._rubber_band: self._rubber_band.deleteLater()
            self._rubber_band = QRubberBand(QRubberBand.Rectangle, self)
            self._rubber_band.setGeometry(QRect(event.pos(), event.pos()))
            self._rubber_band.show()
            return

        # Check handle click
        if event.button() == Qt.LeftButton:
            handle = self._hit_handle(event.pos())
            if handle:
                self._dragging_handle = True
                self._active_handle = handle
                self.setCursor(self._cursor_for_handle(handle))
                self.setDragMode(QGraphicsView.NoDrag)
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._selecting and self._rubber_band and self._sel_origin_view is not None:
            rect = QRect(self._sel_origin_view, event.pos()).normalized()
            self._rubber_band.setGeometry(rect)
            return

        if self._dragging_handle and self._selection_scene:
            new_pos = self.mapToScene(event.pos())
            new_rect = QRectF(self._selection_scene)
            h = self._active_handle
            if 'w' in h: new_rect.setLeft(new_pos.x())
            if 'e' in h: new_rect.setRight(new_pos.x())
            if 'n' in h: new_rect.setTop(new_pos.y())
            if 's' in h: new_rect.setBottom(new_pos.y())
            if new_rect.width() > 5 and new_rect.height() > 5:
                self._selection_scene = new_rect.normalized()
                self.region_changed.emit(self._selection_scene)
            return

        # Update cursor for hover over handles
        if not self._selecting and not self._dragging_handle:
            handle = self._hit_handle(event.pos())
            if handle:
                self.setCursor(self._cursor_for_handle(handle))
            elif not self._selecting:
                self.setCursor(Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._selecting and event.button() == Qt.LeftButton and self._sel_origin_view is not None:
            if self._rubber_band: self._rubber_band.hide()
            view_rect = QRect(self._sel_origin_view, event.pos()).normalized()
            if view_rect.width() > 10 and view_rect.height() > 10:
                scene_rect = self.mapToScene(view_rect).boundingRect()
                self._selection_scene = scene_rect
                self.region_selected.emit(scene_rect)
            self._end_selection()
            return

        if self._dragging_handle:
            self._dragging_handle = False
            self._active_handle = None
            self.setCursor(Qt.ArrowCursor)
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self._selecting:
                self._end_selection()
            elif self._selection_scene:
                self.clear_selection()
                self.region_cleared.emit()
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act_toggle = QAction("切换原图 / 检测叠加层", self); act_toggle.triggered.connect(self.double_clicked.emit); menu.addAction(act_toggle)
        menu.addSeparator()
        act_zoom_in = QAction("放大 (+)", self); act_zoom_in.triggered.connect(self.zoom_in); menu.addAction(act_zoom_in)
        act_zoom_out = QAction("缩小 (-)", self); act_zoom_out.triggered.connect(self.zoom_out); menu.addAction(act_zoom_out)
        act_fit = QAction("适应窗口", self); act_fit.triggered.connect(self.zoom_fit); menu.addAction(act_fit)
        menu.addSeparator()
        act_select = QAction("框选检测区域", self); act_select.triggered.connect(self._start_selection); menu.addAction(act_select)
        if self._selection_scene:
            act_clear = QAction("清除选区", self); act_clear.triggered.connect(lambda: (self.clear_selection(), self.region_cleared.emit())); menu.addAction(act_clear)
        menu.exec_(event.globalPos())


class ImagePanel(QWidget):
    """Image preview panel with zoom controls and selection support."""

    region_selected = pyqtSignal(tuple)  # (x, y, w, h) in image pixel coords

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_view_signals()
        self._reset_state()

    def _connect_view_signals(self):
        """Connect ImageView signals for selection manipulation."""
        self._view.region_cleared.connect(self._on_selection_cleared)
        self._view.region_changed.connect(self._on_selection_resized)

    def _on_selection_cleared(self):
        """User clicked outside selection -> clear it."""
        self._reset_selection()

    def _on_selection_resized(self, scene_rect: QRectF):
        """User dragged a resize handle -> update selection."""
        if self._original_img is None:
            return
        h_img, w_img = self._original_img.shape[:2]
        x = max(0, min(int(scene_rect.x()), w_img - 1))
        y = max(0, min(int(scene_rect.y()), h_img - 1))
        w = max(1, min(int(scene_rect.width()), w_img - x))
        h = max(1, min(int(scene_rect.height()), h_img - y))
        self._selection_rect = (x, y, w, h)
        # Redraw
        self._redraw_with_selection()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Image view
        self._scene = QGraphicsScene(self)
        self._view = ImageView(self._scene)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setRenderHint(QPainter.SmoothPixmapTransform)
        self._view.setDragMode(QGraphicsView.ScrollHandDrag)
        self._view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self._view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self._view.setBackgroundBrush(QBrush(QColor(PANEL_BG)))
        self._view.setStyleSheet(
            f"border: 1px solid #BBDEFB; border-radius: 3px; background-color: {PANEL_BG};")
        self._view.double_clicked.connect(self._on_toggle_view)
        self._view.region_selected.connect(self._on_region_selected)
        self._view.zoom_changed.connect(self._on_zoom_changed)
        layout.addWidget(self._view, 1)

        # Zoom control bar
        zoom_bar = QHBoxLayout()
        zoom_bar.setContentsMargins(4, 2, 4, 2)

        self._btn_zoom_out = QPushButton("−")
        self._btn_zoom_out.setToolTip("缩小")
        self._btn_zoom_out.setFixedSize(28, 28)
        self._btn_zoom_out.clicked.connect(self._view.zoom_out)
        self._btn_zoom_out.setStyleSheet(
            "QPushButton { font-size: 16px; font-weight: bold; }")
        zoom_bar.addWidget(self._btn_zoom_out)

        self._lbl_zoom = QLabel("100%")
        self._lbl_zoom.setAlignment(Qt.AlignCenter)
        self._lbl_zoom.setMinimumWidth(50)
        self._lbl_zoom.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        zoom_bar.addWidget(self._lbl_zoom)

        self._btn_zoom_in = QPushButton("+")
        self._btn_zoom_in.setToolTip("放大")
        self._btn_zoom_in.setFixedSize(28, 28)
        self._btn_zoom_in.clicked.connect(self._view.zoom_in)
        self._btn_zoom_in.setStyleSheet(
            "QPushButton { font-size: 16px; font-weight: bold; }")
        zoom_bar.addWidget(self._btn_zoom_in)

        self._btn_zoom_fit = QPushButton("适应")
        self._btn_zoom_fit.setToolTip("适应窗口")
        self._btn_zoom_fit.setFixedHeight(28)
        self._btn_zoom_fit.clicked.connect(self._view.zoom_fit)
        zoom_bar.addWidget(self._btn_zoom_fit)

        zoom_bar.addStretch()

        self._btn_select = QPushButton("框选区域")
        self._btn_select.setToolTip("框选需要检测的区域，只检测框内部分")
        self._btn_select.setFixedHeight(28)
        self._btn_select.clicked.connect(self._view._start_selection)
        self._btn_select.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: white; font-size: 11px; padding: 2px 8px; }}"
            f"QPushButton:hover {{ background-color: #1565C0; }}")
        zoom_bar.addWidget(self._btn_select)

        self._btn_reset_sel = QPushButton("重置选区")
        self._btn_reset_sel.setToolTip("恢复全图检测")
        self._btn_reset_sel.setFixedHeight(28)
        self._btn_reset_sel.clicked.connect(self._reset_selection)
        self._btn_reset_sel.setEnabled(False)
        zoom_bar.addWidget(self._btn_reset_sel)

        layout.addLayout(zoom_bar)

        # Placeholder
        self._placeholder = QLabel(
            "请打开一张图像\n\n滚轮缩放 | 拖拽平移 | 双击切换原图\n右键菜单更多操作",
            self._view)
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 15px; background: transparent;")
        self._placeholder.setGeometry(0, 0, 450, 100)

    def _reset_state(self):
        self._original_img: Optional[np.ndarray] = None
        self._overlay_img: Optional[np.ndarray] = None
        self._geometry_list: List = []
        self._show_overlay = True
        self._selection_rect: Optional[Tuple[int, int, int, int]] = None  # (x,y,w,h)

    def display_image(self, img: np.ndarray, keep_selection: bool = False):
        self._original_img = img.copy()
        self._overlay_img = None
        self._geometry_list = []
        if not keep_selection:
            self._selection_rect = None
            self._btn_reset_sel.setEnabled(False)

        pixmap = self._cv_to_qpixmap(img)
        self._scene.clear()
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self._view.zoom_fit()
        self._placeholder.hide()

    def set_overlay(self, geometry_list: List):
        if self._original_img is None:
            return
        self._geometry_list = geometry_list
        overlay = self._original_img.copy()
        self._draw_geometry(overlay, geometry_list)
        if self._selection_rect:
            x, y, w, h = self._selection_rect
            self._draw_selection_handles(overlay, x, y, w, h)
        self._overlay_img = overlay
        pixmap = self._cv_to_qpixmap(overlay)
        self._scene.clear()
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self._view.zoom_fit()

    def get_selected_region(self) -> Optional[Tuple[int, int, int, int]]:
        """Returns (x, y, width, height) of selected region in image pixels, or None."""
        return self._selection_rect

    def _draw_selection_handles(self, img: np.ndarray, x: int, y: int, w: int, h: int):
        """Draw selection rectangle with resize handles (thick lines, large handles)."""
        # Main rectangle — thick border
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 200, 255), 8)
        # 8 handles (8x8 pixel filled squares)
        cx, cy = x + w//2, y + h//2
        handles = [(x,y),(cx,y),(x+w,y),(x+w,cy),(x+w,y+h),(cx,y+h),(x,y+h),(x,cy)]
        for hx, hy in handles:
            cv2.rectangle(img, (hx-5, hy-5), (hx+5, hy+5), (0, 200, 255), -1)
            cv2.rectangle(img, (hx-5, hy-5), (hx+5, hy+5), (255, 255, 255), 1)

    def _redraw_with_selection(self):
        """Redraw always from original to avoid ghost handles."""
        if self._selection_rect is None or self._original_img is None:
            return
        x, y, w, h = self._selection_rect
        img = self._original_img.copy()
        if self._geometry_list:
            self._draw_geometry(img, self._geometry_list)
        self._draw_selection_handles(img, x, y, w, h)
        if self._geometry_list:
            self._overlay_img = img
        pixmap = self._cv_to_qpixmap(img)
        self._scene.clear()
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))

    def _on_region_selected(self, scene_rect: QRectF):
        if self._original_img is None:
            return
        h_img, w_img = self._original_img.shape[:2]
        x = max(0, min(int(scene_rect.x()), w_img - 1))
        y = max(0, min(int(scene_rect.y()), h_img - 1))
        w = max(1, min(int(scene_rect.width()), w_img - x))
        h = max(1, min(int(scene_rect.height()), h_img - y))

        self._selection_rect = (x, y, w, h)
        self._btn_reset_sel.setEnabled(True)
        self._view._end_selection()
        self._view.set_selection(QRectF(float(x), float(y), float(w), float(h)))

        # Draw with handles
        if self._overlay_img is not None:
            self.set_overlay(self._geometry_list)
        self._redraw_with_selection()
        self.region_selected.emit((x, y, w, h))

    def _reset_selection(self):
        self._selection_rect = None
        self._btn_reset_sel.setEnabled(False)
        self._view._end_selection()
        self._view.clear_selection()
        if self._overlay_img is not None:
            self.set_overlay(self._geometry_list)
        elif self._original_img is not None:
            self.display_image(self._original_img)

    def _on_zoom_changed(self, zoom: float):
        self._lbl_zoom.setText(f"{int(zoom * 100)}%")

    def _on_toggle_view(self):
        if self._overlay_img is None:
            return
        self._show_overlay = not self._show_overlay
        if self._show_overlay:
            pixmap = self._cv_to_qpixmap(self._overlay_img)
        else:
            pixmap = self._cv_to_qpixmap(self._original_img)
        self._scene.clear()
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))

    # === Drawing functions (unchanged) ===
    def _draw_geometry(self, img, geometry_list):
        for geom in geometry_list:
            if isinstance(geom, Wall): self._draw_wall(img, geom)
            elif isinstance(geom, Line2D): self._draw_line(img, geom)
            elif isinstance(geom, Circle2D): self._draw_circle(img, geom)
            elif isinstance(geom, Arc2D): self._draw_arc(img, geom)
            elif isinstance(geom, Polyline): self._draw_polyline(img, geom)
            elif isinstance(geom, Door): self._draw_door(img, geom)
            elif isinstance(geom, Window): self._draw_window(img, geom)
            elif isinstance(geom, TreeSymbol): self._draw_tree(img, geom)
            elif isinstance(geom, WaterFeature): self._draw_water(img, geom)
            elif isinstance(geom, PathLine): self._draw_path(img, geom)

    def _to_int_pt(self, pt): return (int(pt.x), int(pt.y))
    def _draw_wall(self, img, wall):
        corners = wall.get_corner_points()
        pts = np.array([[self._to_int_pt(p)] for p in corners], dtype=np.int32)
        cv2.polylines(img, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
        cv2.line(img, self._to_int_pt(wall.centerline.p1), self._to_int_pt(wall.centerline.p2), (0, 100, 255), 1)
    def _draw_line(self, img, line):
        cv2.line(img, self._to_int_pt(line.p1), self._to_int_pt(line.p2), (200, 200, 200), 1)
    def _draw_circle(self, img, circle):
        cv2.circle(img, self._to_int_pt(circle.center), int(circle.radius), (0, 255, 0), 2)
    def _draw_arc(self, img, arc):
        cv2.ellipse(img, self._to_int_pt(arc.center), (int(arc.radius), int(arc.radius)), 0, arc.start_angle, arc.end_angle, (255, 255, 0), 2)
    def _draw_polyline(self, img, pl):
        pts = np.array([[self._to_int_pt(p)] for p in pl.points], dtype=np.int32)
        cv2.polylines(img, [pts], isClosed=pl.closed, color=(150, 150, 150), thickness=1)
    def _draw_door(self, img, door):
        cv2.circle(img, self._to_int_pt(door.position), 5, (0, 0, 255), -1)
    def _draw_window(self, img, window):
        cv2.circle(img, self._to_int_pt(window.position), 4, (255, 0, 0), -1)
    def _draw_tree(self, img, tree):
        cv2.circle(img, self._to_int_pt(tree.center), int(tree.radius), (0, 180, 0), -1)
    def _draw_water(self, img, water):
        pts = np.array([[self._to_int_pt(p)] for p in water.contour], dtype=np.int32)
        overlay = img.copy(); cv2.fillPoly(overlay, [pts], (255, 200, 0)); img[:] = cv2.addWeighted(img, 0.7, overlay, 0.3, 0)
    def _draw_path(self, img, path):
        pts = np.array([[self._to_int_pt(p)] for p in path.polyline], dtype=np.int32)
        cv2.polylines(img, [pts], isClosed=False, color=(0, 255, 255), thickness=2)

    @staticmethod
    def _cv_to_qpixmap(img):
        if img is None: return QPixmap()
        h, w = img.shape[:2]
        if len(img.shape) == 2:
            qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
        else:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def clear(self):
        self._scene.clear()
        self._reset_state()
        self._placeholder.show()

    @property
    def has_image(self) -> bool:
        return self._original_img is not None
