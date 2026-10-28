"""Main application entry point for Remon AI Background Remover Pro V 01.02."""

import os
import sys
import threading
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from ui.main_window import MainWindow
from ui.theme import DARK_THEME_QSS


def configure_model_environment():
    """Point REMBG_HOME directly to bundled models without copying 1GB of data."""
    if os.getenv("REMBG_HOME") or os.getenv("U2NET_HOME"):
        return
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "Resources")),
        os.path.abspath(os.path.join(base_dir, "..", "Resources")),
        base_dir,
    ]
    for c in candidates:
        if os.path.exists(os.path.join(c, "models", "bria-rmbg", "bria-rmbg.onnx")):
            os.environ["REMBG_HOME"] = c
            return


def _background_warmup():
    """Silently warm up rembg module in background RAM while user sees GUI immediately."""
    try:
        import rembg
    except Exception:
        pass


def main():
    # Instant environment configuration (< 0.001s, zero file copies)
    configure_model_environment()

    app = QApplication(sys.argv)
    app.setApplicationName("Remon AI Background Remover Pro V 01.02")
    app.setOrganizationName("SpaceShip")

    # Set application icon
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    icon_paths = [
        os.path.join(base_dir, "assets", "app_icon_1024.png"),
        os.path.join(base_dir, "assets", "icon.icns"),
    ]
    for p in icon_paths:
        if os.path.exists(p):
            app.setWindowIcon(QIcon(p))
            break

    # Native macOS system font
    font = QFont()
    font.setFamily("Helvetica Neue")
    font.setPointSize(12)
    app.setFont(font)

    # Modern dark theme
    app.setStyleSheet(DARK_THEME_QSS)

    # Show window immediately
    window = MainWindow()
    window.show()
    app.processEvents()

    # Launch background warmup thread (does not block GUI)
    threading.Thread(target=_background_warmup, daemon=True).start()

    # Handle optional CLI arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if arg.startswith("http://") or arg.startswith("https://"):
            from core.downloader import fetch_image_from_url
            try:
                img, url = fetch_image_from_url(arg)
                window.set_loaded_image(img, source_name=url)
            except Exception as e:
                print(f"Error loading initial URL: {e}", file=sys.stderr)
        elif os.path.isfile(arg):
            window.load_image_from_path(arg)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
