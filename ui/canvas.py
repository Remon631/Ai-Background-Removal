"""Interactive image editing canvas supporting zoom, pan, Keep/Delete brush painting, and comparison views."""

from typing import Optional, Tuple
from PIL import Image
import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QPixmap,
    QImage,
    QMouseEvent,
    QWheelEvent,
    QPaintEvent,
    QCursor,
    QDragEnterEvent,
    QDropEvent,
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from core.mask_engine import MaskEngine, BrushMode


class ImageCanvas(QWidget):
    """
    High-performance canvas widget for viewing and retouching images.
    Features:
        - Smooth pan & zoom centered on mouse cursor
        - Keep Brush (restore foreground) & Delete Brush (erase foreground)
        - Visual circular brush cursor overlay
        - Checkerboard, solid color, and custom background image rendering
        - Split-screen Before/After comparison slider
        - Drag-and-drop file support
    """

    zoom_changed = Signal(float)       # emits zoom factor e.g. 1.0 (100%)
    cursor_info_changed = Signal(str)  # status bar coordinate info
    mask_modified = Signal()           # emitted on stroke completion
    image_dropped = Signal(str)        # emits dropped file path

    def __init__(self, mask_engine: MaskEngine, parent=None):
        super().__init__(parent)
        self.mask_engine = mask_engine
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAcceptDrops(True)

        # View transform state
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        # Tool states: "keep", "delete", "pan"
        self.tool_mode = "keep"
        self.brush_radius = 25.0  # in image coordinates
        self.brush_hardness = 1.0  # 0.1 to 1.0

        # Background preview settings
        self.bg_mode = "checkerboard"  # "checkerboard", "color", "custom_image"
        self.bg_color = QColor(255, 255, 255)
        self.custom_bg_qimage: Optional[QImage] = None

        # View mode: "composite", "split", "mask", "peek_original"
        self.view_mode = "composite"
        self.split_position = 0.5  # 0.0 to 1.0 (relative to image width)
        self.peek_original = False

        # Interaction tracking
        self._is_painting = False
        self._is_panning = False
        self._is_dragging_split = False
        self._last_mouse_pos = QPointF(0, 0)
        self._last_image_pos = QPointF(0, 0)
        self._cursor_window_pos = QPointF(-100, -100)

        # Cached checkerboard tile
        self._checkerboard_tile: Optional[QPixmap] = None
        self._init_checkerboard()

    def _init_checkerboard(self):
        tile_size = 14
        pm = QPixmap(tile_size * 2, tile_size * 2)
        p = QPainter(pm)
        c1 = QColor(30, 32, 40)
        c2 = QColor(42, 45, 56)
        p.fillRect(0, 0, tile_size * 2, tile_size * 2, c1)
        p.fillRect(0, 0, tile_size, tile_size, c2)
        p.fillRect(tile_size, tile_size, tile_size, tile_size, c2)
        p.end()
        self._checkerboard_tile = pm

    # -------------------------------------------------------------------------
    # Public Configuration Methods
    # -------------------------------------------------------------------------

    def set_tool_mode(self, mode: str):
        """Set tool mode: 'keep', 'delete', or 'pan'."""
        self.tool_mode = mode
        self._update_cursor()
        self.update()

    def set_brush_radius(self, radius: float):
        self.brush_radius = max(1.0, float(radius))
        self.update()

    def set_brush_hardness(self, hardness: float):
        self.brush_hardness = min(1.0, max(0.1, float(hardness)))

    def set_bg_mode(self, mode: str):
        self.bg_mode = mode
        self.update()

    def set_bg_color(self, color: QColor):
        self.bg_color = color
        self.update()

    def set_custom_bg_image(self, pil_image: Optional[Image.Image]):
        if pil_image is None:
            self.custom_bg_qimage = None
        else:
            rgb = pil_image.convert("RGB")
            arr = np.array(rgb, dtype=np.uint8)
            self.custom_bg_qimage = QImage(
                arr.data, rgb.width, rgb.height, rgb.width * 3, QImage.Format_RGB888
            ).copy()
        self.update()

    def set_view_mode(self, mode: str):
        self.view_mode = mode
        self.update()

    def set_peek_original(self, peek: bool):
        self.peek_original = peek
        self.update()

    def reset_view(self):
        """Fit image to current canvas size and center it."""
        if not self.mask_engine.has_image:
            return

        w = self.width()
        h = self.height()
        img_w = self.mask_engine.width
        img_h = self.mask_engine.height

        scale_x = (w * 0.9) / img_w
        scale_y = (h * 0.9) / img_h
        self.zoom = max(0.05, min(scale_x, scale_y, 1.0))

        self.offset_x = (w - img_w * self.zoom) / 2.0
        self.offset_y = (h - img_h * self.zoom) / 2.0

        self.zoom_changed.emit(self.zoom)
        self.update()

    def set_zoom_level(self, zoom: float):
        """Set zoom centered on widget viewport."""
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        self._apply_zoom(zoom, center_x, center_y)

    def _apply_zoom(self, new_zoom: float, pivot_x: float, pivot_y: float):
        new_zoom = max(0.05, min(25.0, new_zoom))
        if abs(new_zoom - self.zoom) < 1e-4:
            return

        # Keep the point under (pivot_x, pivot_y) stationary in canvas coordinates
        img_x = (pivot_x - self.offset_x) / self.zoom
        img_y = (pivot_y - self.offset_y) / self.zoom

        self.zoom = new_zoom
        self.offset_x = pivot_x - img_x * self.zoom
        self.offset_y = pivot_y - img_y * self.zoom

        self.zoom_changed.emit(self.zoom)
        self.update()

    def clear_canvas(self):
        """Reset canvas to blank state."""
        self.custom_bg_qimage = None
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.peek_original = False
        self.view_mode = "composite"
        self.tool_mode = "keep"
        self._is_painting = False
        self._is_panning = False
        self._is_dragging_split = False
        self.zoom_changed.emit(1.0)
        self.cursor_info_changed.emit("")
        self._update_cursor()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep canvas responsive when window is resized
        if self.mask_engine.has_image:
            w = self.width()
            h = self.height()
            img_w = self.mask_engine.width * self.zoom
            img_h = self.mask_engine.height * self.zoom
            if img_w <= w:
                self.offset_x = (w - img_w) / 2.0
            if img_h <= h:
                self.offset_y = (h - img_h) / 2.0
            self.update()

    # -------------------------------------------------------------------------
    # Coordinate Mapping
    # -------------------------------------------------------------------------

    def window_to_image_coords(self, pt: QPointF) -> QPointF:
        """Convert widget screen coordinates to image pixel coordinates."""
        return QPointF(
            (pt.x() - self.offset_x) / self.zoom,
            (pt.y() - self.offset_y) / self.zoom,
        )

    def image_to_window_coords(self, pt: QPointF) -> QPointF:
        """Convert image pixel coordinates to widget screen coordinates."""
        return QPointF(
            pt.x() * self.zoom + self.offset_x,
            pt.y() * self.zoom + self.offset_y,
        )

    def get_image_screen_rect(self) -> QRectF:
        """Get bounding rect of image in widget coordinates."""
        if not self.mask_engine.has_image:
            return QRectF()
        return QRectF(
            self.offset_x,
            self.offset_y,
            self.mask_engine.width * self.zoom,
            self.mask_engine.height * self.zoom,
        )

    # -------------------------------------------------------------------------
    # Mouse & Event Handlers
    # -------------------------------------------------------------------------

    def _update_cursor(self):
        if self.tool_mode == "pan":
            self.setCursor(Qt.OpenHandCursor)
        elif self.tool_mode in ("keep", "delete"):
            # Hide default cursor over canvas so custom circular ring shows clearly
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event: QWheelEvent):
        # Zoom centered at mouse position
        angle = event.angleDelta().y()
        if angle == 0:
            return

        factor = 1.15 if angle > 0 else (1.0 / 1.15)
        new_zoom = self.zoom * factor
        pos = event.position()
        self._apply_zoom(new_zoom, pos.x(), pos.y())

    def mousePressEvent(self, event: QMouseEvent):
        self._last_mouse_pos = event.position()
        img_pos = self.window_to_image_coords(event.position())
        self._last_image_pos = img_pos

        # Check split view divider drag
        if self.view_mode == "split" and self.mask_engine.has_image:
            rect = self.get_image_screen_rect()
            divider_x = rect.left() + rect.width() * self.split_position
            if abs(event.position().x() - divider_x) < 15:
                self._is_dragging_split = True
                return

        # Middle mouse button or Spacebar hold triggers pan
        if event.button() == Qt.MiddleButton or self.tool_mode == "pan":
            self._is_panning = True
            self.setCursor(Qt.ClosedHandCursor)
            return

        # Left mouse button triggers brush
        if event.button() == Qt.LeftButton and self.tool_mode in ("keep", "delete"):
            if not self.mask_engine.has_image:
                return
            self._is_painting = True
            brush_mode = BrushMode.KEEP if self.tool_mode == "keep" else BrushMode.DELETE

            self.mask_engine.push_undo_state()
            self.mask_engine.draw_brush_stroke(
                img_pos, img_pos, brush_mode, self.brush_radius, self.brush_hardness
            )
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        self._cursor_window_pos = event.position()
        img_pos = self.window_to_image_coords(event.position())

        # Update status bar info
        if self.mask_engine.has_image:
            ix = int(img_pos.x())
            iy = int(img_pos.y())
            if 0 <= ix < self.mask_engine.width and 0 <= iy < self.mask_engine.height:
                self.cursor_info_changed.emit(f"X: {ix} px  Y: {iy} px")
            else:
                self.cursor_info_changed.emit("")

        # Handle split slider dragging
        if self._is_dragging_split and self.mask_engine.has_image:
            rect = self.get_image_screen_rect()
            if rect.width() > 0:
                rel = (event.position().x() - rect.left()) / rect.width()
                self.split_position = max(0.02, min(0.98, rel))
                self.update()
                return

        # Handle panning
        if self._is_panning:
            delta = event.position() - self._last_mouse_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self._last_mouse_pos = event.position()
            self.update()
            return

        # Handle painting
        if self._is_painting and self.mask_engine.has_image:
            brush_mode = BrushMode.KEEP if self.tool_mode == "keep" else BrushMode.DELETE
            self.mask_engine.draw_brush_stroke(
                self._last_image_pos,
                img_pos,
                brush_mode,
                self.brush_radius,
                self.brush_hardness,
            )
            self._last_image_pos = img_pos
            self.update()
            return

        # Redraw cursor ring
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_painting:
            self._is_painting = False
            self.mask_modified.emit()
            self.update()

        if self._is_panning:
            self._is_panning = False
            self._update_cursor()

        if self._is_dragging_split:
            self._is_dragging_split = False

    def leaveEvent(self, event):
        self._cursor_window_pos = QPointF(-100, -100)
        self.update()

    # -------------------------------------------------------------------------
    # Drag & Drop Support
    # -------------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path:
                self.image_dropped.emit(file_path)
                event.acceptProposedAction()

    # -------------------------------------------------------------------------
    # Rendering & Painting
    # -------------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 1. Fill canvas workspace background
        painter.fillRect(self.rect(), QColor(18, 19, 22))

        if not self.mask_engine.has_image:
            # Draw stylized drop zone container in center
            w = min(480.0, max(240.0, self.width() - 40.0))
            h = min(230.0, max(180.0, self.height() - 40.0))
            rx = (self.width() - w) / 2.0
            ry = (self.height() - h) / 2.0
            drop_rect = QRectF(rx, ry, w, h)

            # Dashed card background
            painter.setBrush(QColor(23, 24, 31))
            dashed_pen = QPen(QColor(55, 60, 78), 2, Qt.DashLine)
            painter.setPen(dashed_pen)
            painter.drawRoundedRect(drop_rect, 12, 12)

            # Icon
            painter.setPen(QColor(129, 140, 248))
            f_icon = painter.font()
            f_icon.setPointSize(28)
            painter.setFont(f_icon)
            painter.drawText(QRectF(rx, ry + 20, w, 42), Qt.AlignCenter, "🖼️")

            # Main Title
            painter.setPen(QColor(243, 244, 246))
            f_title = painter.font()
            f_title.setPointSize(14)
            f_title.setBold(True)
            painter.setFont(f_title)
            painter.drawText(QRectF(rx + 15, ry + 68, w - 30, 28), Qt.AlignCenter, "Drag & Drop Image Here")

            # Subtitle
            painter.setPen(QColor(156, 163, 175))
            f_sub = painter.font()
            f_sub.setPointSize(11)
            f_sub.setBold(False)
            painter.setFont(f_sub)
            painter.drawText(QRectF(rx + 15, ry + 102, w - 30, 42), Qt.AlignCenter, "or use Open Image, From Link/URL, or Paste (Cmd+V)")

            # Badge / Formats
            painter.setPen(QColor(99, 102, 241))
            f_badge = painter.font()
            f_badge.setPointSize(10)
            painter.setFont(f_badge)
            painter.drawText(QRectF(rx + 15, ry + 150, w - 30, 24), Qt.AlignCenter, "PNG • JPG • WebP • TIFF • BMP • PDF • ICO")
            return

        rect = self.get_image_screen_rect()

        # 2. Render Backdrop according to selected bg_mode
        if self.bg_mode == "checkerboard" and self._checkerboard_tile:
            painter.drawTiledPixmap(rect, self._checkerboard_tile)
        elif self.bg_mode == "color":
            painter.fillRect(rect, self.bg_color)
        elif self.bg_mode == "custom_image" and self.custom_bg_qimage:
            painter.drawImage(rect, self.custom_bg_qimage)
        else:
            painter.fillRect(rect, QColor(0, 0, 0))

        # 3. Render Subject / Result
        if self.peek_original:
            # Peek original mode
            orig_qimage = self.mask_engine.get_original_qimage()
            painter.drawImage(rect, orig_qimage)

        elif self.view_mode == "mask":
            # Mask view
            if self.mask_engine.current_mask_qimage:
                painter.drawImage(rect, self.mask_engine.current_mask_qimage)

        elif self.view_mode == "split":
            # Split Screen View: Left is original, Right is cutout
            orig_qimage = self.mask_engine.get_original_qimage()
            subject_qimage = self.mask_engine.get_composite_rgba_qimage()

            split_x = rect.left() + rect.width() * self.split_position
            left_width = split_x - rect.left()
            right_width = rect.right() - split_x

            # Draw left (original)
            painter.save()
            painter.setClipRect(QRectF(rect.left(), rect.top(), left_width, rect.height()))
            painter.drawImage(rect, orig_qimage)
            painter.restore()

            # Draw right (cutout subject)
            painter.save()
            painter.setClipRect(QRectF(split_x, rect.top(), right_width, rect.height()))
            painter.drawImage(rect, subject_qimage)
            painter.restore()

            # Draw split divider line & handle
            divider_pen = QPen(QColor(255, 255, 255, 220), 2)
            painter.setPen(divider_pen)
            painter.drawLine(QPointF(split_x, rect.top()), QPointF(split_x, rect.bottom()))

            # Circular handle in center
            cy = rect.top() + rect.height() / 2.0
            painter.setBrush(QColor(79, 70, 229))
            painter.drawEllipse(QPointF(split_x, cy), 12, 12)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(QRectF(split_x - 10, cy - 10, 20, 20), Qt.AlignCenter, "⬌")

        else:
            # Standard composite view
            subject_qimage = self.mask_engine.get_composite_rgba_qimage()
            painter.drawImage(rect, subject_qimage)

        # 4. Draw outer border around image bounds
        border_pen = QPen(QColor(55, 65, 81, 180), 1)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

        # 5. Draw live interactive Circular Brush Cursor
        if self.tool_mode in ("keep", "delete") and rect.contains(self._cursor_window_pos):
            radius_screen = self.brush_radius * self.zoom
            cx = self._cursor_window_pos.x()
            cy = self._cursor_window_pos.y()

            if self.tool_mode == "keep":
                # Emerald green ring with white dashed contrast
                brush_pen = QPen(QColor(16, 185, 129, 230), 2)
            else:
                # Crimson red ring
                brush_pen = QPen(QColor(239, 68, 68, 230), 2)

            painter.setPen(brush_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), radius_screen, radius_screen)

            # Tiny center indicator dot
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), 2, 2)
