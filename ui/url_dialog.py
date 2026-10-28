"""URL Download Dialog for fetching images from direct links or web pages."""

from typing import Optional
from PIL import Image
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QApplication,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from core.downloader import DownloadWorker


class URLDownloadDialog(QDialog):
    """Dialog allowing user to input or paste any image/webpage URL."""

    image_downloaded = Signal(object, str)  # (PIL.Image, source_url)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open Image from URL")
        self.setMinimumWidth(540)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.worker: Optional[DownloadWorker] = None
        self._setup_ui()
        self._check_clipboard_for_url()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title / instructions
        title_label = QLabel("Enter Image or Web Page Link:")
        title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #f3f4f6;")
        layout.addWidget(title_label)

        hint_label = QLabel(
            "Paste direct links (JPEG, PNG, WebP) or article/page links. "
            "Our scraper will automatically detect and extract the primary image."
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #9ca3af; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(hint_label)

        # Input row
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/image.jpg or webpage link...")
        self.url_input.returnPressed.connect(self._start_download)
        input_layout.addWidget(self.url_input)

        self.paste_btn = QPushButton("Paste Clipboard")
        self.paste_btn.clicked.connect(self._paste_clipboard)
        input_layout.addWidget(self.paste_btn)
        layout.addLayout(input_layout)

        # Progress / Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #818cf8; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate animation
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.download_btn = QPushButton("Download & Open")
        self.download_btn.setObjectName("primaryActionBtn")
        self.download_btn.clicked.connect(self._start_download)
        btn_layout.addWidget(self.download_btn)

        layout.addLayout(btn_layout)

    def _check_clipboard_for_url(self):
        """Auto-populate if clipboard contains an http link."""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text.startswith("http://") or text.startswith("https://"):
            self.url_input.setText(text)
            self.url_input.selectAll()

    def _paste_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self.url_input.setText(text)
            self.url_input.selectAll()

    def _start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Please enter a valid link.")
            return

        self.download_btn.setEnabled(False)
        self.url_input.setEnabled(False)
        self.paste_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Connecting and downloading image...")

        self.worker = DownloadWorker(url)
        self.worker.finished_success.connect(self._on_success)
        self.worker.failed.connect(self._on_failure)
        self.worker.start()

    def _on_success(self, image: Image.Image, resolved_url: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Success!")
        self.image_downloaded.emit(image, resolved_url)
        self.accept()

    def _on_failure(self, error_msg: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        self.download_btn.setEnabled(True)
        self.url_input.setEnabled(True)
        self.paste_btn.setEnabled(True)
        QMessageBox.critical(self, "Download Error", error_msg)
