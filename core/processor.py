"""AI Background Removal processor using rembg with session caching and background worker."""

import traceback
from typing import Dict, Tuple, Optional
from PIL import Image
from PySide6.QtCore import QThread, Signal

# Dictionary of available models with descriptive names
AVAILABLE_MODELS = {
    "bria-rmbg": "BRIA RMBG (High Precision & Speed - Recommended)",
    "u2net": "U2Net (General Use, Balanced Quality)",
    "isnet-general-use": "IS-Net (Ultra-sharp Edges & Fine Details)",
    "u2net_human_seg": "U2Net Human (Optimized for Portraits & People)",
    "silueta": "Silueta (Ultra Fast & Lightweight)",
    "u2netp": "U2NetP (Fast & Low Resource)",
}

# Session cache to avoid re-allocating ONNX sessions on every run
_SESSION_CACHE: Dict[str, object] = {}


def get_model_session(model_name: str = "bria-rmbg"):
    """Retrieve or initialize a cached rembg session (lazy-loaded)."""
    import rembg

    if model_name not in AVAILABLE_MODELS:
        model_name = "bria-rmbg"

    if model_name not in _SESSION_CACHE:
        try:
            _SESSION_CACHE[model_name] = rembg.new_session(model_name)
        except Exception as e:
            # Fallback to default if specific model fails to initialize
            if model_name != "u2net":
                return get_model_session("u2net")
            raise e

    return _SESSION_CACHE[model_name]


def process_background_removal(
    image: Image.Image,
    model_name: str = "bria-rmbg",
    alpha_matting: bool = False,
    post_process: bool = False,
) -> Tuple[Image.Image, Image.Image]:
    """
    Remove background from a PIL image.
    Returns:
        (rgba_image, mask_image) where mask_image is 8-bit grayscale ('L').
    """
    import rembg

    # Normalize input image to RGB
    if image.mode != "RGB":
        rgb_image = image.convert("RGB")
    else:
        rgb_image = image.copy()

    session = get_model_session(model_name)

    # Compute mask using rembg
    kwargs = {
        "session": session,
        "only_mask": True,
        "post_process_mask": post_process,
    }
    if alpha_matting:
        kwargs.update({
            "alpha_matting": True,
            "alpha_matting_foreground_threshold": 240,
            "alpha_matting_background_threshold": 10,
            "alpha_matting_erode_size": 10,
        })

    mask = rembg.remove(rgb_image, **kwargs)

    # Ensure mask is strictly 8-bit grayscale and matches original dimensions
    if mask.mode != "L":
        mask = mask.convert("L")
    if mask.size != rgb_image.size:
        mask = mask.resize(rgb_image.size, Image.Resampling.BILINEAR)

    # Construct RGBA image from original RGB and predicted mask
    rgba = rgb_image.convert("RGBA")
    rgba.putalpha(mask)

    return rgba, mask


class AIProcessorWorker(QThread):
    """Worker thread to run AI background removal asynchronously without locking the UI."""

    progress_status = Signal(str)
    finished_success = Signal(object, object)  # (rgba_image, mask_image)
    failed = Signal(str)

    def __init__(
        self,
        image: Image.Image,
        model_name: str = "bria-rmbg",
        alpha_matting: bool = False,
        post_process: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.image = image
        self.model_name = model_name
        self.alpha_matting = alpha_matting
        self.post_process = post_process

    def run(self):
        try:
            self.progress_status.emit(f"Loading {self.model_name} AI model...")
            # Ensure session is ready
            _ = get_model_session(self.model_name)

            self.progress_status.emit("Detecting subject and removing background...")
            rgba, mask = process_background_removal(
                self.image,
                model_name=self.model_name,
                alpha_matting=self.alpha_matting,
                post_process=self.post_process,
            )

            self.progress_status.emit("Processing complete!")
            self.finished_success.emit(rgba, mask)
        except Exception as e:
            traceback.print_exc()
            self.failed.emit(f"AI Processing failed: {str(e)}")
