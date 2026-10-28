"""Interactive Mask Engine managing mask state, brush strokes, undo/redo, and image composition."""

import enum
from typing import Optional, List, Tuple
from PIL import Image, ImageOps
import numpy as np
from PySide6.QtGui import (
    QImage,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QRadialGradient,
    QPixmap,
)
from PySide6.QtCore import QPointF, Qt, QRectF


class BrushMode(enum.Enum):
    KEEP = "keep"      # Paint subject (restore foreground / opaque)
    DELETE = "delete"  # Paint background (erase / transparent)


class MaskEngine:
    """
    Manages the subject mask, brush interactions, undo/redo stacks,
    and rendering composites for preview and export.
    """

    def __init__(self, max_history: int = 30):
        self.max_history = max_history
        self.original_pil: Optional[Image.Image] = None
        self.original_rgb_array: Optional[np.ndarray] = None  # (H, W, 3) uint8

        self.current_mask_qimage: Optional[QImage] = None  # Format_Grayscale8
        self.ai_initial_mask_qimage: Optional[QImage] = None

        self.undo_stack: List[QImage] = []
        self.redo_stack: List[QImage] = []

        self.width = 0
        self.height = 0

    @property
    def has_image(self) -> bool:
        return self.original_pil is not None and self.current_mask_qimage is not None

    def load_image_and_mask(self, pil_image: Image.Image, pil_mask: Optional[Image.Image] = None):
        """Initialize engine with a new image and optional starting mask."""
        self.original_pil = pil_image.convert("RGB")
        self.width, self.height = self.original_pil.size
        self.original_rgb_array = np.array(self.original_pil, dtype=np.uint8)

        if pil_mask is None:
            # Default to fully opaque mask (everything kept)
            self.current_mask_qimage = QImage(self.width, self.height, QImage.Format_Grayscale8)
            self.current_mask_qimage.fill(255)
        else:
            if pil_mask.size != (self.width, self.height):
                pil_mask = pil_mask.resize((self.width, self.height), Image.Resampling.BILINEAR)
            if pil_mask.mode != "L":
                pil_mask = pil_mask.convert("L")
            raw_bytes = pil_mask.tobytes("raw", "L")
            self.current_mask_qimage = QImage(
                raw_bytes, self.width, self.height, self.width, QImage.Format_Grayscale8
            ).copy()

        self.ai_initial_mask_qimage = self.current_mask_qimage.copy()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def update_mask_from_ai(self, pil_mask: Image.Image):
        """Update current mask with fresh AI background removal result, saving previous state."""
        if not self.has_image:
            return
        self.push_undo_state()
        if pil_mask.size != (self.width, self.height):
            pil_mask = pil_mask.resize((self.width, self.height), Image.Resampling.BILINEAR)
        if pil_mask.mode != "L":
            pil_mask = pil_mask.convert("L")

        raw_bytes = pil_mask.tobytes("raw", "L")
        self.current_mask_qimage = QImage(
            raw_bytes, self.width, self.height, self.width, QImage.Format_Grayscale8
        ).copy()
        self.ai_initial_mask_qimage = self.current_mask_qimage.copy()

    def push_undo_state(self):
        """Save a snapshot of the current mask before modifying it."""
        if self.current_mask_qimage is None:
            return
        if len(self.undo_stack) >= self.max_history:
            self.undo_stack.pop(0)
        self.undo_stack.append(self.current_mask_qimage.copy())
        self.redo_stack.clear()

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def undo(self) -> bool:
        if not self.can_undo():
            return False
        self.redo_stack.append(self.current_mask_qimage.copy())
        self.current_mask_qimage = self.undo_stack.pop()
        return True

    def redo(self) -> bool:
        if not self.can_redo():
            return False
        self.undo_stack.append(self.current_mask_qimage.copy())
        self.current_mask_qimage = self.redo_stack.pop()
        return True

    def reset_to_ai_result(self):
        """Reset mask to initial AI output."""
        if self.ai_initial_mask_qimage is not None:
            self.push_undo_state()
            self.current_mask_qimage = self.ai_initial_mask_qimage.copy()

    def fill_all(self, mode: BrushMode):
        """Fill entire mask with Keep (255) or Delete (0)."""
        if not self.has_image:
            return
        self.push_undo_state()
        val = 255 if mode == BrushMode.KEEP else 0
        self.current_mask_qimage.fill(val)

    def invert_mask(self):
        """Invert current mask."""
        if not self.has_image:
            return
        self.push_undo_state()
        self.current_mask_qimage.invertPixels()

    def draw_brush_stroke(
        self,
        p1: QPointF,
        p2: QPointF,
        mode: BrushMode,
        radius: float,
        hardness: float = 1.0,
    ):
        """
        Draw a brush stroke between p1 and p2 on the mask.
        Supports continuous lines with round caps and hardness adjustment.
        """
        if not self.has_image or self.current_mask_qimage is None:
            return

        target_color = QColor(255, 255, 255) if mode == BrushMode.KEEP else QColor(0, 0, 0)
        diameter = radius * 2.0

        painter = QPainter(self.current_mask_qimage)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if hardness >= 0.85:
            # High hardness: standard antialiased pen is extremely fast & smooth
            pen = QPen(target_color, diameter, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(p1, p2)
        else:
            # Feathered soft brush: interpolate along path with radial gradient stamp
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            distance = (dx * dx + dy * dy) ** 0.5
            step = max(1.0, radius * 0.25)
            steps = max(1, int(distance / step))

            painter.setPen(Qt.NoPen)
            val = 255 if mode == BrushMode.KEEP else 0

            for i in range(steps + 1):
                t = i / float(steps)
                cx = p1.x() + dx * t
                cy = p1.y() + dy * t

                grad = QRadialGradient(QPointF(cx, cy), radius)
                # Outer fade based on hardness
                grad.setColorAt(0.0, QColor(val, val, val, 255))
                grad.setColorAt(max(0.1, hardness), QColor(val, val, val, int(255 * 0.9)))
                grad.setColorAt(1.0, QColor(val, val, val, 0))

                painter.setBrush(QBrush(grad))
                painter.drawEllipse(QPointF(cx, cy), radius, radius)

        painter.end()

    def get_mask_numpy(self) -> np.ndarray:
        """Return 2D uint8 numpy array (H, W) of the current mask."""
        if self.current_mask_qimage is None:
            return np.zeros((self.height, self.width), dtype=np.uint8)

        ptr = self.current_mask_qimage.constBits()
        bytes_per_line = self.current_mask_qimage.bytesPerLine()
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((self.height, bytes_per_line))
        return arr[:, :self.width]

    def get_composite_rgba_numpy(self) -> np.ndarray:
        """Return (H, W, 4) uint8 numpy array with RGB from original and A from mask."""
        if not self.has_image:
            return np.zeros((10, 10, 4), dtype=np.uint8)

        mask_arr = self.get_mask_numpy()
        rgba = np.empty((self.height, self.width, 4), dtype=np.uint8)
        rgba[:, :, :3] = self.original_rgb_array
        rgba[:, :, 3] = mask_arr
        return rgba

    def get_composite_rgba_qimage(self) -> QImage:
        """Generate full RGBA QImage of the cut-out subject."""
        if not self.has_image:
            return QImage()

        rgba_arr = self.get_composite_rgba_numpy()
        # Keep a copy so the underlying memory buffer is safely retained
        qimg = QImage(
            rgba_arr.data,
            self.width,
            self.height,
            self.width * 4,
            QImage.Format_RGBA8888,
        ).copy()
        return qimg

    def get_original_qimage(self) -> QImage:
        """Return QImage of original RGB image."""
        if not self.has_image:
            return QImage()
        return QImage(
            self.original_rgb_array.data,
            self.width,
            self.height,
            self.width * 3,
            QImage.Format_RGB888,
        ).copy()

    def clear(self):
        """Reset engine completely to empty state (for Start New)."""
        self.original_pil = None
        self.original_rgb_array = None
        self.current_mask_qimage = None
        self.ai_initial_mask_qimage = None
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.width = 0
        self.height = 0

    def reset_to_initial(self):
        """Reset mask to initial AI result and clear undo/redo stacks."""
        if self.ai_initial_mask_qimage is not None:
            self.current_mask_qimage = self.ai_initial_mask_qimage.copy()
        elif self.has_image:
            self.current_mask_qimage.fill(255)
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_export_pil_image(
        self,
        bg_mode: str = "transparent",
        bg_color: Tuple[int, int, int] = (255, 255, 255),
        custom_bg_pil: Optional[Image.Image] = None,
    ) -> Image.Image:
        """
        Produce high-resolution PIL Image for saving or exporting.
        Options:
            - bg_mode='transparent': PNG with transparent alpha channel
            - bg_mode='color': Solid background color (RGB)
            - bg_mode='custom_image': Replaced background image (fitted/stretched)
        """
        if not self.has_image:
            raise ValueError("No image loaded.")

        mask_arr = self.get_mask_numpy()
        mask_pil = Image.fromarray(mask_arr, mode="L")

        subject_rgba = self.original_pil.convert("RGBA")
        subject_rgba.putalpha(mask_pil)

        if bg_mode == "transparent":
            return subject_rgba

        elif bg_mode == "color":
            bg = Image.new("RGBA", (self.width, self.height), (*bg_color, 255))
            composite = Image.alpha_composite(bg, subject_rgba)
            return composite.convert("RGB")

        elif bg_mode == "custom_image" and custom_bg_pil is not None:
            # Resize custom background to fill canvas
            bg = custom_bg_pil.convert("RGBA")
            bg = ImageOps.fit(bg, (self.width, self.height), method=Image.Resampling.LANCZOS)
            composite = Image.alpha_composite(bg, subject_rgba)
            return composite.convert("RGB")

        return subject_rgba

    def save_to_file(
        self,
        filepath: str,
        bg_mode: str = "transparent",
        bg_color: Tuple[int, int, int] = (255, 255, 255),
        custom_bg_pil: Optional[Image.Image] = None,
    ):
        """
        Save the cutout to any requested format:
        PNG, JPEG, WebP, TIFF, BMP, PDF, ICO.
        Automatically handles transparency for formats that support it,
        and clean compositing for formats that do not (e.g. JPEG, BMP).
        """
        if not self.has_image:
            raise ValueError("No image loaded.")

        ext = filepath.split(".")[-1].lower() if "." in filepath else "png"

        # Formats that support transparent alpha channels
        if ext in ("png", "webp", "tiff", "tif"):
            if bg_mode == "transparent":
                out_img = self.get_export_pil_image("transparent")
            else:
                out_img = self.get_export_pil_image(bg_mode, bg_color, custom_bg_pil)

            if ext == "webp":
                out_img.save(filepath, format="WEBP", quality=95)
            elif ext in ("tiff", "tif"):
                out_img.save(filepath, format="TIFF")
            else:
                out_img.save(filepath, format="PNG")

        # Formats that require opaque RGB channels
        elif ext in ("jpg", "jpeg", "bmp", "pdf"):
            # If transparent was selected, composite over chosen bg_color (default white)
            actual_bg_mode = bg_mode if bg_mode in ("color", "custom_image") else "color"
            out_img = self.get_export_pil_image(actual_bg_mode, bg_color, custom_bg_pil).convert("RGB")

            if ext in ("jpg", "jpeg"):
                out_img.save(filepath, format="JPEG", quality=95)
            elif ext == "bmp":
                out_img.save(filepath, format="BMP")
            elif ext == "pdf":
                out_img.save(filepath, format="PDF", resolution=300.0)

        # Icon format
        elif ext == "ico":
            out_img = self.get_export_pil_image("transparent")
            if out_img.width > 256 or out_img.height > 256:
                out_img.thumbnail((256, 256), Image.Resampling.LANCZOS)
            out_img.save(
                filepath,
                format="ICO",
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
            )

        else:
            # Fallback to PNG
            out_img = self.get_export_pil_image(bg_mode, bg_color, custom_bg_pil)
            out_img.save(filepath)

