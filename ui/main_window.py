"""Main application window integrating AI Background Removal, Refine Canvas, and URL Downloader."""

import os
from typing import Optional
from PIL import Image
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QColorDialog,
    QStatusBar,
    QProgressBar,
    QToolBar,
    QButtonGroup,
    QApplication,
    QScrollArea,
    QFrame,
    QSplitter,
)
from PySide6.QtGui import (
    QAction,
    QIcon,
    QKeySequence,
    QColor,
    QClipboard,
    QImage,
)
from PySide6.QtCore import Qt, QSize

from core.mask_engine import MaskEngine, BrushMode
from core.processor import AIProcessorWorker, AVAILABLE_MODELS
from core.downloader import fetch_image_from_url
from ui.canvas import ImageCanvas
from ui.url_dialog import URLDownloadDialog


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Remon AI Background Remover Pro V 01.02")
        self.resize(1240, 800)
        self.setMinimumSize(700, 480)

        self.mask_engine = MaskEngine(max_history=30)
        self.canvas = ImageCanvas(self.mask_engine, self)
        self.ai_worker: Optional[AIProcessorWorker] = None
        self.custom_bg_pil: Optional[Image.Image] = None
        self.current_file_path: Optional[str] = None

        self._setup_ui()
        self._setup_menus_and_shortcuts()
        self._setup_connections()

        # Update initial states
        self._update_action_states()

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # ---------------------------------------------------------------------
        # Top Global Action Bar (Full Window Width - High Visibility & Fluid)
        # ---------------------------------------------------------------------
        top_bar_frame = QFrame()
        top_bar_frame.setObjectName("topHeaderBar")
        top_bar_layout = QHBoxLayout(top_bar_frame)
        top_bar_layout.setContentsMargins(8, 4, 8, 4)
        top_bar_layout.setSpacing(8)

        # Sidebar toggle
        self.toggle_sidebar_btn = QPushButton("◀ Panel")
        self.toggle_sidebar_btn.setObjectName("toggleSidebarBtn")
        self.toggle_sidebar_btn.setToolTip("Toggle sidebar controls visibility (Ctrl+B / Cmd+B)")
        self.toggle_sidebar_btn.setFixedWidth(74)
        self.toggle_sidebar_btn.clicked.connect(self._toggle_sidebar)
        top_bar_layout.addWidget(self.toggle_sidebar_btn)

        # Start New (Prominent vibrant emerald button)
        self.start_new_btn = QPushButton("✨ Start New")
        self.start_new_btn.setObjectName("startNewBtn")
        self.start_new_btn.setToolTip("Clear current canvas and start a new image project (Cmd+N / Ctrl+N)")
        self.start_new_btn.clicked.connect(self.start_new_project)
        top_bar_layout.addWidget(self.start_new_btn)

        # File Opening actions
        self.open_file_btn = QPushButton("📂 Open Image")
        self.open_file_btn.setObjectName("openFileBtn")
        self.open_file_btn.setToolTip("Open image file (Cmd+O / Ctrl+O)")
        self.open_file_btn.clicked.connect(self.open_image_file)
        top_bar_layout.addWidget(self.open_file_btn)

        self.open_url_btn = QPushButton("🌐 From URL")
        self.open_url_btn.setObjectName("openUrlBtn")
        self.open_url_btn.setToolTip("Open from link or web page (Cmd+L / Ctrl+L)")
        self.open_url_btn.clicked.connect(self.open_from_url_dialog)
        top_bar_layout.addWidget(self.open_url_btn)

        self.paste_clip_btn = QPushButton("📋 Paste")
        self.paste_clip_btn.setObjectName("pasteClipBtn")
        self.paste_clip_btn.setToolTip("Paste copied image or URL (Cmd+V / Ctrl+V)")
        self.paste_clip_btn.clicked.connect(self.paste_from_clipboard)
        top_bar_layout.addWidget(self.paste_clip_btn)

        top_bar_layout.addStretch()

        # Save As (All Formats) & Export
        self.save_as_btn = QPushButton("💾 Save As...")
        self.save_as_btn.setObjectName("saveAsBtn")
        self.save_as_btn.setToolTip("Save in any format: PNG, JPG, WebP, TIFF, BMP, PDF, ICO (Cmd+Shift+S / Ctrl+Shift+S)")
        self.save_as_btn.clicked.connect(self.save_as_dialog)
        top_bar_layout.addWidget(self.save_as_btn)

        self.save_png_btn = QPushButton("⚡ Quick PNG")
        self.save_png_btn.setObjectName("quickPngBtn")
        self.save_png_btn.setToolTip("Quickly save transparent cutout as PNG (Cmd+S / Ctrl+S)")
        self.save_png_btn.clicked.connect(self.export_transparent_png)
        top_bar_layout.addWidget(self.save_png_btn)

        self.copy_result_btn = QPushButton("📋 Copy Cutout")
        self.copy_result_btn.setObjectName("copyResultBtn")
        self.copy_result_btn.setToolTip("Copy cutout directly to system clipboard (Cmd+C / Ctrl+C)")
        self.copy_result_btn.clicked.connect(self.copy_result_to_clipboard)
        top_bar_layout.addWidget(self.copy_result_btn)

        main_layout.addWidget(top_bar_frame)

        # ---------------------------------------------------------------------
        # Main Splitter (Left Sidebar + Center Canvas)
        # ---------------------------------------------------------------------
        self.splitter = QSplitter(Qt.Horizontal)

        # ---------------------------------------------------------------------
        # Left Sidebar (Controls)
        # ---------------------------------------------------------------------
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setMinimumWidth(280)
        self.sidebar_scroll.setMaximumWidth(340)
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setFrameShape(QFrame.NoFrame)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sidebar_container = QWidget()
        sidebar_container.setMinimumWidth(265)
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 6, 0)
        sidebar_layout.setSpacing(12)

        # --- Section 1: AI Background Removal ---
        ai_box, ai_layout = self._create_card_box("⚡ AI Background Removal")
        ai_layout.setSpacing(8)

        model_label = QLabel("Segmentation Model:")
        model_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        ai_layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.addItem("BRIA RMBG (High Precision)", "bria-rmbg")
        self.model_combo.addItem("U2Net (General Purpose)", "u2net")
        self.model_combo.addItem("ISNet (General Use)", "isnet-general-use")
        self.model_combo.addItem("U2Net Human (Portraits)", "u2net_human_seg")
        self.model_combo.addItem("Silueta (Ultra Fast/Mobile)", "silueta")
        ai_layout.addWidget(self.model_combo)

        self.alpha_matting_cb = QCheckBox("Alpha Matting (Hair and fine edges)")
        ai_layout.addWidget(self.alpha_matting_cb)

        self.post_process_cb = QCheckBox("Smooth Edges (Post-process mask)")
        ai_layout.addWidget(self.post_process_cb)

        self.run_ai_btn = QPushButton("✨ Run AI Background Removal")
        self.run_ai_btn.setObjectName("runAiBtn")
        self.run_ai_btn.setMinimumHeight(40)
        self.run_ai_btn.clicked.connect(self.trigger_ai_removal)
        ai_layout.addWidget(self.run_ai_btn)

        self.ai_progress_bar = QProgressBar()
        self.ai_progress_bar.setRange(0, 0)
        self.ai_progress_bar.setVisible(False)
        ai_layout.addWidget(self.ai_progress_bar)

        self.ai_status_label = QLabel("")
        self.ai_status_label.setWordWrap(True)
        self.ai_status_label.setStyleSheet("color: #818cf8; font-size: 11px;")
        ai_layout.addWidget(self.ai_status_label)

        sidebar_layout.addWidget(ai_box)

        # --- Section 2: Refine / Keep & Delete Tools ---
        refine_box, refine_layout = self._create_card_box("🖌️ Refine Selection (Keep / Delete)")
        refine_layout.setSpacing(10)

        self.tool_button_group = QButtonGroup(self)
        self.tool_button_group.setExclusive(True)

        # Keep and Delete brushes side-by-side
        brush_row = QHBoxLayout()
        brush_row.setSpacing(8)

        self.keep_btn = QPushButton("🟢 Keep Brush")
        self.keep_btn.setObjectName("keepBrushBtn")
        self.keep_btn.setCheckable(True)
        self.keep_btn.setChecked(True)
        self.keep_btn.setToolTip("Paint over areas to KEEP / restore subject (Key: 1 or K)")
        self.tool_button_group.addButton(self.keep_btn)
        brush_row.addWidget(self.keep_btn)

        self.delete_btn = QPushButton("🔴 Delete Brush")
        self.delete_btn.setObjectName("deleteBrushBtn")
        self.delete_btn.setCheckable(True)
        self.delete_btn.setToolTip("Paint over areas to DELETE / erase background (Key: 2 or E)")
        self.tool_button_group.addButton(self.delete_btn)
        brush_row.addWidget(self.delete_btn)
        refine_layout.addLayout(brush_row)

        # Pan tool row
        pan_row = QHBoxLayout()
        self.pan_btn = QPushButton("✋ Pan Canvas (Key: H / Space)")
        self.pan_btn.setObjectName("panToolBtn")
        self.pan_btn.setCheckable(True)
        self.pan_btn.setToolTip("Pan / move image (Key: H or Middle-click / Spacebar)")
        self.tool_button_group.addButton(self.pan_btn)
        pan_row.addWidget(self.pan_btn)
        refine_layout.addLayout(pan_row)

        # Brush Size Slider
        size_label = QLabel("Brush Size: [ / ]")
        size_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        refine_layout.addWidget(size_label)

        size_row = QHBoxLayout()
        self.brush_size_slider = QSlider(Qt.Horizontal)
        self.brush_size_slider.setRange(1, 200)
        self.brush_size_slider.setValue(25)
        self.brush_size_slider.valueChanged.connect(self._on_brush_size_slider_changed)
        size_row.addWidget(self.brush_size_slider)

        self.brush_size_spin = QSpinBox()
        self.brush_size_spin.setRange(1, 200)
        self.brush_size_spin.setValue(25)
        self.brush_size_spin.setSuffix(" px")
        self.brush_size_spin.valueChanged.connect(self._on_brush_size_spin_changed)
        size_row.addWidget(self.brush_size_spin)
        refine_layout.addLayout(size_row)

        # Brush Hardness Slider
        hardness_label = QLabel("Brush Hardness (Soft to Hard):")
        hardness_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        refine_layout.addWidget(hardness_label)

        hardness_row = QHBoxLayout()
        self.brush_hardness_slider = QSlider(Qt.Horizontal)
        self.brush_hardness_slider.setRange(10, 100)
        self.brush_hardness_slider.setValue(100)
        self.brush_hardness_slider.valueChanged.connect(self._on_hardness_changed)
        hardness_row.addWidget(self.brush_hardness_slider)

        self.hardness_label_val = QLabel("100%")
        self.hardness_label_val.setStyleSheet("color: #d1d5db; min-width: 38px;")
        hardness_row.addWidget(self.hardness_label_val)
        refine_layout.addLayout(hardness_row)

        # Quick Actions Grid
        quick_grid = QGridLayout()
        quick_grid.setSpacing(6)

        self.reset_ai_btn = QPushButton("↩ Reset to AI")
        self.reset_ai_btn.setToolTip("Reset mask back to original AI cutout")
        self.reset_ai_btn.clicked.connect(self._on_reset_to_ai)
        quick_grid.addWidget(self.reset_ai_btn, 0, 0)

        self.invert_mask_btn = QPushButton("⇄ Invert Mask")
        self.invert_mask_btn.setToolTip("Swap kept and deleted areas")
        self.invert_mask_btn.clicked.connect(self._on_invert_mask)
        quick_grid.addWidget(self.invert_mask_btn, 0, 1)

        self.keep_all_btn = QPushButton("Keep All")
        self.keep_all_btn.setToolTip("Restore whole original image")
        self.keep_all_btn.clicked.connect(lambda: self.mask_engine.fill_all(BrushMode.KEEP) or self.canvas.update() or self._update_action_states())
        quick_grid.addWidget(self.keep_all_btn, 1, 0)

        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.setToolTip("Erase entire image")
        self.clear_all_btn.clicked.connect(lambda: self.mask_engine.fill_all(BrushMode.DELETE) or self.canvas.update() or self._update_action_states())
        quick_grid.addWidget(self.clear_all_btn, 1, 1)

        refine_layout.addLayout(quick_grid)
        sidebar_layout.addWidget(refine_box)

        # --- Section 3: Backdrop & Background Replacement ---
        bg_box, bg_layout = self._create_card_box("🎨 Background Backdrop")
        bg_layout.setSpacing(8)

        self.bg_combo = QComboBox()
        self.bg_combo.addItem("🏁 Transparent (Checkerboard)", "checkerboard")
        self.bg_combo.addItem("⬜ Solid Color Fill", "color")
        self.bg_combo.addItem("🖼️ Custom Background Image", "custom_image")
        self.bg_combo.currentIndexChanged.connect(self._on_bg_combo_changed)
        bg_layout.addWidget(self.bg_combo)

        # Quick Color Swatches
        self.color_swatch_widget = QWidget()
        color_row = QHBoxLayout(self.color_swatch_widget)
        color_row.setContentsMargins(0, 0, 0, 0)
        color_row.setSpacing(6)

        btn_white = QPushButton("White")
        btn_white.clicked.connect(lambda: self._set_bg_color(QColor(255, 255, 255)))
        color_row.addWidget(btn_white)

        btn_black = QPushButton("Black")
        btn_black.clicked.connect(lambda: self._set_bg_color(QColor(0, 0, 0)))
        color_row.addWidget(btn_black)

        btn_green = QPushButton("Green")
        btn_green.clicked.connect(lambda: self._set_bg_color(QColor(0, 255, 0)))
        color_row.addWidget(btn_green)

        btn_pick = QPushButton("Pick...")
        btn_pick.clicked.connect(self._pick_custom_color)
        color_row.addWidget(btn_pick)
        bg_layout.addWidget(self.color_swatch_widget)
        self.color_swatch_widget.setVisible(False)

        # Custom Background Image Controls
        self.custom_bg_widget = QWidget()
        custom_bg_row = QHBoxLayout(self.custom_bg_widget)
        custom_bg_row.setContentsMargins(0, 0, 0, 0)
        custom_bg_row.setSpacing(6)

        self.browse_bg_btn = QPushButton("Select Image...")
        self.browse_bg_btn.clicked.connect(self._browse_custom_bg)
        custom_bg_row.addWidget(self.browse_bg_btn)

        self.clear_bg_btn = QPushButton("Remove")
        self.clear_bg_btn.clicked.connect(self._clear_custom_bg)
        custom_bg_row.addWidget(self.clear_bg_btn)
        bg_layout.addWidget(self.custom_bg_widget)
        self.custom_bg_widget.setVisible(False)

        sidebar_layout.addWidget(bg_box)

        # --- Section 4: View & Compare ---
        view_box, view_layout = self._create_card_box("👁️ View & Comparison")
        view_layout.setSpacing(8)

        self.view_combo = QComboBox()
        self.view_combo.addItem("Normal Result Preview", "composite")
        self.view_combo.addItem("Split Slider (Before / After)", "split")
        self.view_combo.addItem("Black & White Mask View", "mask")
        self.view_combo.currentIndexChanged.connect(self._on_view_combo_changed)
        view_layout.addWidget(self.view_combo)

        self.peek_orig_btn = QPushButton("Hold to Peek Original (Tab)")
        self.peek_orig_btn.pressed.connect(lambda: self.canvas.set_peek_original(True))
        self.peek_orig_btn.released.connect(lambda: self.canvas.set_peek_original(False))
        view_layout.addWidget(self.peek_orig_btn)

        sidebar_layout.addWidget(view_box)

        sidebar_layout.addStretch()
        self.sidebar_scroll.setWidget(sidebar_container)

        # ---------------------------------------------------------------------
        # Center Canvas Workspace
        # ---------------------------------------------------------------------
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(4)

        # Canvas Utility Bar (Reset, Undo, Redo, Zoom Controls)
        canvas_bar_frame = QFrame()
        canvas_bar_frame.setObjectName("canvasBarFrame")
        canvas_bar = QHBoxLayout(canvas_bar_frame)
        canvas_bar.setContentsMargins(4, 2, 4, 2)
        canvas_bar.setSpacing(4)

        # Reset button (Vibrant Amber/Orange)
        self.reset_btn = QPushButton("🔄 Reset Edits")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setToolTip("Reset all brush edits and restore original AI cutout (Cmd+Shift+R)")
        self.reset_btn.clicked.connect(self.reset_current_project)
        canvas_bar.addWidget(self.reset_btn)

        self.undo_btn = QPushButton("↩ Undo")
        self.undo_btn.setToolTip("Undo last brush stroke (Cmd+Z / Ctrl+Z)")
        self.undo_btn.clicked.connect(self._on_undo)
        canvas_bar.addWidget(self.undo_btn)

        self.redo_btn = QPushButton("↪ Redo")
        self.redo_btn.setToolTip("Redo brush stroke (Cmd+Shift+Z / Ctrl+Y)")
        self.redo_btn.clicked.connect(self._on_redo)
        canvas_bar.addWidget(self.redo_btn)

        canvas_bar.addStretch()

        # Zoom Controls
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setObjectName("zoomBtn")
        self.zoom_out_btn.setToolTip("Zoom Out")
        self.zoom_out_btn.clicked.connect(lambda: self.canvas.set_zoom_level(self.canvas.zoom * 0.8))
        canvas_bar.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #ffffff; font-weight: 700; min-width: 38px; text-align: center;")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        canvas_bar.addWidget(self.zoom_label)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setObjectName("zoomBtn")
        self.zoom_in_btn.setToolTip("Zoom In")
        self.zoom_in_btn.clicked.connect(lambda: self.canvas.set_zoom_level(self.canvas.zoom * 1.25))
        canvas_bar.addWidget(self.zoom_in_btn)

        self.zoom_fit_btn = QPushButton("⊡ Fit View")
        self.zoom_fit_btn.setToolTip("Fit image to canvas (Key: F)")
        self.zoom_fit_btn.clicked.connect(self.canvas.reset_view)
        canvas_bar.addWidget(self.zoom_fit_btn)

        self.zoom_100_btn = QPushButton("1:1 Size")
        self.zoom_100_btn.setToolTip("Actual pixel size (Key: 0)")
        self.zoom_100_btn.clicked.connect(lambda: self.canvas.set_zoom_level(1.0))
        canvas_bar.addWidget(self.zoom_100_btn)

        self.canvas_dim_badge = QLabel("Ready")
        self.canvas_dim_badge.setStyleSheet(
            "background-color: #202436; border: 1px solid #363d59; color: #a5b4fc; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700;"
        )
        canvas_bar.addWidget(self.canvas_dim_badge)

        canvas_layout.addWidget(canvas_bar_frame)
        canvas_layout.addWidget(self.canvas, stretch=1)

        # Assemble Splitter for Fluid Resizing
        self.splitter.addWidget(self.sidebar_scroll)
        self.splitter.addWidget(canvas_container)
        self.splitter.setCollapsible(0, True)   # sidebar can be collapsed
        self.splitter.setCollapsible(1, False)  # canvas never collapses
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([290, 950])
        main_layout.addWidget(self.splitter, stretch=1)

        # ---------------------------------------------------------------------
        # Status Bar
        # ---------------------------------------------------------------------
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_msg_label = QLabel("Ready. Open an image or paste a link to get started.")
        self.status_msg_label.setStyleSheet("color: #9ca3af;")
        self.status_bar.addWidget(self.status_msg_label, stretch=1)

        self.cursor_info_label = QLabel("")
        self.cursor_info_label.setStyleSheet("color: #6b7280; font-family: Menlo, Monaco, 'Courier New', monospace;")
        self.status_bar.addPermanentWidget(self.cursor_info_label)

        self.image_dim_label = QLabel("No image loaded")
        self.image_dim_label.setStyleSheet("color: #9ca3af; padding-right: 12px;")
        self.status_bar.addPermanentWidget(self.image_dim_label)

    def _create_card_box(self, title: str):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background-color: #17181f; border: 1px solid #282a36; border-radius: 8px; padding: 6px; }"
        )
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: 600; font-size: 12px; color: #a5b4fc; margin-bottom: 4px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(title_lbl)
        return frame, layout

    def _setup_connections(self):
        # Tool group buttons
        self.keep_btn.clicked.connect(lambda: self.canvas.set_tool_mode("keep"))
        self.delete_btn.clicked.connect(lambda: self.canvas.set_tool_mode("delete"))
        self.pan_btn.clicked.connect(lambda: self.canvas.set_tool_mode("pan"))

        # Canvas signals
        self.canvas.zoom_changed.connect(self._on_zoom_changed)
        self.canvas.cursor_info_changed.connect(self.cursor_info_label.setText)
        self.canvas.mask_modified.connect(self._update_action_states)
        self.canvas.image_dropped.connect(self.load_image_from_path)

    def _setup_menus_and_shortcuts(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        start_new_action = QAction("&Start New Project", self)
        start_new_action.setShortcut(QKeySequence.New)
        start_new_action.triggered.connect(self.start_new_project)
        file_menu.addAction(start_new_action)

        open_action = QAction("&Open Image...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_image_file)
        file_menu.addAction(open_action)

        url_action = QAction("Open from &URL / Link...", self)
        url_action.setShortcut(QKeySequence("Ctrl+L"))
        url_action.triggered.connect(self.open_from_url_dialog)
        file_menu.addAction(url_action)

        paste_action = QAction("&Paste Image or Link", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste_from_clipboard)
        file_menu.addAction(paste_action)

        file_menu.addSeparator()

        save_as_action = QAction("&Save As (All Formats)...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_dialog)
        file_menu.addAction(save_as_action)

        save_png_action = QAction("Save &Transparent PNG...", self)
        save_png_action.setShortcut(QKeySequence.Save)
        save_png_action.triggered.connect(self.export_transparent_png)
        file_menu.addAction(save_png_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")

        self.undo_action = QAction("&Undo Stroke", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("&Redo Stroke", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        self.redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        reset_action = QAction("&Reset All Edits to Initial AI", self)
        reset_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        reset_action.triggered.connect(self.reset_current_project)
        edit_menu.addAction(reset_action)

        edit_menu.addSeparator()

        copy_action = QAction("&Copy Cutout to Clipboard", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_result_to_clipboard)
        edit_menu.addAction(copy_action)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")

        run_ai_action = QAction("Run &AI Background Removal", self)
        run_ai_action.setShortcut(QKeySequence("Ctrl+R"))
        run_ai_action.triggered.connect(self.trigger_ai_removal)
        tools_menu.addAction(run_ai_action)

        tools_menu.addSeparator()

        keep_tool_action = QAction("&Keep Brush", self)
        keep_tool_action.setShortcut(QKeySequence("1"))
        keep_tool_action.triggered.connect(lambda: self.keep_btn.setChecked(True) or self.canvas.set_tool_mode("keep"))
        tools_menu.addAction(keep_tool_action)

        delete_tool_action = QAction("&Delete Brush", self)
        delete_tool_action.setShortcut(QKeySequence("2"))
        delete_tool_action.triggered.connect(lambda: self.delete_btn.setChecked(True) or self.canvas.set_tool_mode("delete"))
        tools_menu.addAction(delete_tool_action)

        pan_tool_action = QAction("&Pan Tool", self)
        pan_tool_action.setShortcut(QKeySequence("H"))
        pan_tool_action.triggered.connect(lambda: self.pan_btn.setChecked(True) or self.canvas.set_tool_mode("pan"))
        tools_menu.addAction(pan_tool_action)

        # Keyboard shortcuts for brush radius
        dec_brush_action = QAction("Decrease Brush Size", self)
        dec_brush_action.setShortcut(QKeySequence("["))
        dec_brush_action.triggered.connect(lambda: self.brush_size_slider.setValue(max(1, self.brush_size_slider.value() - 5)))
        self.addAction(dec_brush_action)

        inc_brush_action = QAction("Increase Brush Size", self)
        inc_brush_action.setShortcut(QKeySequence("]"))
        inc_brush_action.triggered.connect(lambda: self.brush_size_slider.setValue(min(200, self.brush_size_slider.value() + 5)))
        self.addAction(inc_brush_action)

        # View shortcuts
        fit_action = QAction("Fit to View", self)
        fit_action.setShortcut(QKeySequence("F"))
        fit_action.triggered.connect(self.canvas.reset_view)
        self.addAction(fit_action)

        actual_size_action = QAction("Actual Size 1:1", self)
        actual_size_action.setShortcut(QKeySequence("0"))
        actual_size_action.triggered.connect(lambda: self.canvas.set_zoom_level(1.0))
        self.addAction(actual_size_action)

        toggle_panel_action = QAction("Toggle Sidebar Panel", self)
        toggle_panel_action.setShortcut(QKeySequence("Ctrl+B"))
        toggle_panel_action.triggered.connect(self._toggle_sidebar)
        self.addAction(toggle_panel_action)

    def _toggle_sidebar(self):
        visible = not self.sidebar_scroll.isVisible()
        self.sidebar_scroll.setVisible(visible)
        self.toggle_sidebar_btn.setText("◀ Panel" if visible else "▶ Panel")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._handle_responsive_layout(self.width())

    def _handle_responsive_layout(self, width: int):
        compact = width < 960
        self.canvas_dim_badge.setVisible(not compact)
        if compact:
            self.start_new_btn.setText("✨ New")
            self.open_file_btn.setText("📂 Open")
            self.open_url_btn.setText("🌐 URL")
            self.paste_clip_btn.setText("📋 Paste")
            self.save_as_btn.setText("💾 Save As")
            self.save_png_btn.setText("⚡ PNG")
            self.copy_result_btn.setText("📋 Copy")
            self.reset_btn.setText("↺ Reset")
            self.undo_btn.setText("Undo")
            self.redo_btn.setText("Redo")
            self.zoom_fit_btn.setText("Fit")
            self.zoom_100_btn.setText("1:1")
        else:
            self.start_new_btn.setText("✨ Start New")
            self.open_file_btn.setText("📂 Open Image")
            self.open_url_btn.setText("🌐 From URL")
            self.paste_clip_btn.setText("📋 Paste")
            self.save_as_btn.setText("💾 Save As...")
            self.save_png_btn.setText("⚡ Quick PNG")
            self.copy_result_btn.setText("📋 Copy Cutout")
            self.reset_btn.setText("🔄 Reset Edits")
            self.undo_btn.setText("↩ Undo")
            self.redo_btn.setText("↪ Redo")
            self.zoom_fit_btn.setText("⊡ Fit View")
            self.zoom_100_btn.setText("1:1 Size")

    # -------------------------------------------------------------------------
    # Image Loading & Opening
    # -------------------------------------------------------------------------

    def open_image_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image File",
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All Files (*)",
        )
        if file_path:
            self.load_image_from_path(file_path)

    def load_image_from_path(self, file_path: str):
        try:
            img = Image.open(file_path)
            self.current_file_path = file_path
            self.set_loaded_image(img, source_name=os.path.basename(file_path))
        except Exception as e:
            QMessageBox.critical(self, "Error Opening Image", f"Failed to load image:\n{str(e)}")

    def open_from_url_dialog(self):
        dialog = URLDownloadDialog(self)
        dialog.image_downloaded.connect(self._on_url_image_received)
        dialog.exec()

    def _on_url_image_received(self, image: Image.Image, source_url: str):
        self.current_file_path = None
        self.set_loaded_image(image, source_name=source_url.split("/")[-1] or "Downloaded Image")

    def paste_from_clipboard(self):
        """Check clipboard for copied image or URL string."""
        clipboard = QApplication.clipboard()

        # Check if clipboard has image data
        mime_data = clipboard.mimeData()
        if mime_data.hasImage():
            qimage = clipboard.image()
            if not qimage.isNull():
                # Convert QImage to PIL
                qimage = qimage.convertToFormat(QImage.Format_RGBA8888)
                ptr = qimage.constBits()
                arr = np.frombuffer(ptr, dtype=np.uint8).reshape((qimage.height(), qimage.width(), 4))
                pil_img = Image.fromarray(arr, mode="RGBA").convert("RGB")
                self.current_file_path = None
                self.set_loaded_image(pil_img, source_name="Clipboard Image")
                return

        # Check if clipboard has text that looks like a URL
        text = clipboard.text().strip()
        if text.startswith("http://") or text.startswith("https://"):
            self.open_from_url_dialog()
            return

        QMessageBox.information(
            self,
            "Clipboard Empty",
            "Clipboard does not contain an image or valid web link.\nCopy an image or URL and try again.",
        )

    def set_loaded_image(self, pil_image: Image.Image, source_name: str = ""):
        """Load new image into mask engine and reset canvas view."""
        self.mask_engine.load_image_and_mask(pil_image)
        self.canvas.reset_view()

        self.image_dim_label.setText(f"{self.mask_engine.width} × {self.mask_engine.height} px")
        self.canvas_dim_badge.setText(f"{self.mask_engine.width} × {self.mask_engine.height} px")
        self.status_msg_label.setText(
            f"Loaded {source_name}. Click 'Run AI Background Removal' or use Keep/Delete brushes."
        )
        self._update_action_states()

        # Automatically prompt or trigger AI background removal
        self.trigger_ai_removal()

    # -------------------------------------------------------------------------
    # AI Background Removal Trigger
    # -------------------------------------------------------------------------

    def trigger_ai_removal(self):
        if not self.mask_engine.has_image:
            QMessageBox.information(self, "No Image", "Please open or paste an image first.")
            return

        model_name = self.model_combo.currentData() or "bria-rmbg"
        alpha_matting = self.alpha_matting_cb.isChecked()
        post_process = self.post_process_cb.isChecked()

        # Disable trigger button during processing
        self.run_ai_btn.setEnabled(False)
        self.ai_progress_bar.setVisible(True)
        self.ai_status_label.setText("Preparing AI model...")
        self.status_msg_label.setText("AI background removal running...")

        self.ai_worker = AIProcessorWorker(
            image=self.mask_engine.original_pil,
            model_name=model_name,
            alpha_matting=alpha_matting,
            post_process=post_process,
            parent=self,
        )
        self.ai_worker.progress_status.connect(self.ai_status_label.setText)
        self.ai_worker.finished_success.connect(self._on_ai_success)
        self.ai_worker.failed.connect(self._on_ai_failed)
        self.ai_worker.start()

    def _on_ai_success(self, rgba: Image.Image, mask: Image.Image):
        self.run_ai_btn.setEnabled(True)
        self.ai_progress_bar.setVisible(False)
        self.ai_status_label.setText("✓ Background removed successfully!")
        self.status_msg_label.setText(
            "Subject detected! Use Keep (1) or Delete (2) brush to touch up any areas."
        )

        self.mask_engine.update_mask_from_ai(mask)
        self.canvas.update()
        self._update_action_states()

    def _on_ai_failed(self, error_msg: str):
        self.run_ai_btn.setEnabled(True)
        self.ai_progress_bar.setVisible(False)
        self.ai_status_label.setText("✗ Processing failed")
        self.status_msg_label.setText("AI processing encountered an error.")
        QMessageBox.critical(self, "AI Error", error_msg)

    # -------------------------------------------------------------------------
    # Undo / Redo & Mask Actions
    # -------------------------------------------------------------------------

    def _on_undo(self):
        if self.mask_engine.undo():
            self.canvas.update()
            self._update_action_states()
            self.status_msg_label.setText("Undid last brush stroke.")

    def _on_redo(self):
        if self.mask_engine.redo():
            self.canvas.update()
            self._update_action_states()
            self.status_msg_label.setText("Redid brush stroke.")

    def reset_current_project(self):
        """Reset the current image edits back to initial AI state and fit view."""
        if not self.mask_engine.has_image:
            return

        reply = QMessageBox.question(
            self,
            "Reset Edits",
            "Are you sure you want to reset all keep/delete brush edits back to the initial AI detection?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.mask_engine.reset_to_initial()
            self.canvas.reset_view()
            self.canvas.update()
            self._update_action_states()
            self.status_msg_label.setText("✓ Reset all edits and restored initial AI cutout.")

    def start_new_project(self):
        """Clear the current project and return to pristine blank state."""
        if self.mask_engine.has_image:
            reply = QMessageBox.question(
                self,
                "Start New Project",
                "Start a new project? Any unsaved edits on the current image will be lost.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self.mask_engine.clear()
        self.custom_bg_pil = None
        self.current_file_path = None
        self.canvas.clear_canvas()
        self.image_dim_label.setText("No image loaded")
        self.canvas_dim_badge.setText("Ready")
        self.status_msg_label.setText("Ready. Open an image, drop a file, or paste a link to get started.")
        self._update_action_states()

    def _on_reset_to_ai(self):
        self.reset_current_project()

    def _on_invert_mask(self):
        self.mask_engine.invert_mask()
        self.canvas.update()
        self._update_action_states()
        self.status_msg_label.setText("Inverted keep and delete mask.")

    def _update_action_states(self):
        has_img = self.mask_engine.has_image
        self.save_as_btn.setEnabled(has_img)
        self.save_png_btn.setEnabled(has_img)
        self.copy_result_btn.setEnabled(has_img)
        self.run_ai_btn.setEnabled(has_img)
        self.reset_btn.setEnabled(has_img)
        self.start_new_btn.setEnabled(True)
        self.open_file_btn.setEnabled(True)
        self.open_url_btn.setEnabled(True)
        self.paste_clip_btn.setEnabled(True)
        self.peek_orig_btn.setEnabled(has_img)
        self.reset_ai_btn.setEnabled(has_img)
        self.invert_mask_btn.setEnabled(has_img)
        self.keep_all_btn.setEnabled(has_img)
        self.clear_all_btn.setEnabled(has_img)

        can_undo = self.mask_engine.can_undo()
        can_redo = self.mask_engine.can_redo()
        self.undo_btn.setEnabled(can_undo)
        self.undo_action.setEnabled(can_undo)
        self.redo_btn.setEnabled(can_redo)
        self.redo_action.setEnabled(can_redo)

    # -------------------------------------------------------------------------
    # Brush Controls Handlers
    # -------------------------------------------------------------------------

    def _on_brush_size_slider_changed(self, value: int):
        self.brush_size_spin.blockSignals(True)
        self.brush_size_spin.setValue(value)
        self.brush_size_spin.blockSignals(False)
        self.canvas.set_brush_radius(value)

    def _on_brush_size_spin_changed(self, value: int):
        self.brush_size_slider.blockSignals(True)
        self.brush_size_slider.setValue(value)
        self.brush_size_slider.blockSignals(False)
        self.canvas.set_brush_radius(value)

    def _on_hardness_changed(self, value: int):
        self.hardness_label_val.setText(f"{value}%")
        self.canvas.set_brush_hardness(value / 100.0)

    def _on_zoom_changed(self, zoom: float):
        self.zoom_label.setText(f"{int(zoom * 100)}%")

    # -------------------------------------------------------------------------
    # Backdrop & View Mode Handlers
    # -------------------------------------------------------------------------

    def _on_bg_combo_changed(self, index: int):
        mode = self.bg_combo.currentData()
        self.canvas.set_bg_mode(mode)
        self.color_swatch_widget.setVisible(mode == "color")
        self.custom_bg_widget.setVisible(mode == "custom_image")

    def _set_bg_color(self, color: QColor):
        self.canvas.set_bg_color(color)

    def _pick_custom_color(self):
        color = QColorDialog.getColor(self.canvas.bg_color, self, "Select Background Color")
        if color.isValid():
            self._set_bg_color(color)

    def _browse_custom_bg(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Background Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp);;All Files (*)",
        )
        if file_path:
            try:
                bg_img = Image.open(file_path)
                self.custom_bg_pil = bg_img
                self.canvas.set_custom_bg_image(bg_img)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load background image:\n{str(e)}")

    def _clear_custom_bg(self):
        self.custom_bg_pil = None
        self.canvas.set_custom_bg_image(None)

    def _on_view_combo_changed(self, index: int):
        mode = self.view_combo.currentData()
        self.canvas.set_view_mode(mode)

    # -------------------------------------------------------------------------
    # Export & Clipboard
    # -------------------------------------------------------------------------

    def save_as_dialog(self):
        """Save As dialog offering all image formats: PNG, JPEG, WebP, TIFF, BMP, PDF, ICO."""
        if not self.mask_engine.has_image:
            return

        default_name = "cutout_result.png"
        if self.current_file_path:
            base, _ = os.path.splitext(os.path.basename(self.current_file_path))
            default_name = f"{base}_cutout.png"

        filters = (
            "PNG Image (*.png);;"
            "JPEG Image (*.jpg *.jpeg);;"
            "WebP Image (*.webp);;"
            "TIFF Image (*.tiff *.tif);;"
            "BMP Image (*.bmp);;"
            "PDF Document (*.pdf);;"
            "Icon File (*.ico);;"
            "All Supported Formats (*.png *.jpg *.jpeg *.webp *.tiff *.tif *.bmp *.pdf *.ico);;"
            "All Files (*.*)"
        )

        save_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Cutout Image As",
            default_name,
            filters,
        )
        if not save_path:
            return

        # Deduce extension if missing
        if "." not in os.path.basename(save_path):
            if "JPEG" in selected_filter:
                save_path += ".jpg"
            elif "WebP" in selected_filter:
                save_path += ".webp"
            elif "TIFF" in selected_filter:
                save_path += ".tiff"
            elif "BMP" in selected_filter:
                save_path += ".bmp"
            elif "PDF" in selected_filter:
                save_path += ".pdf"
            elif "Icon" in selected_filter:
                save_path += ".ico"
            else:
                save_path += ".png"

        try:
            c = self.canvas.bg_color
            rgb_color = (c.red(), c.green(), c.blue())
            bg_mode = self.canvas.bg_mode

            self.mask_engine.save_to_file(
                filepath=save_path,
                bg_mode=bg_mode,
                bg_color=rgb_color,
                custom_bg_pil=self.custom_bg_pil,
            )
            self.status_msg_label.setText(f"✓ Saved: {os.path.basename(save_path)}")
            QMessageBox.information(
                self,
                "Save Successful",
                f"Image saved successfully to:\n{save_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")

    def export_transparent_png(self):
        if not self.mask_engine.has_image:
            return

        default_name = "cutout_transparent.png"
        if self.current_file_path:
            base, _ = os.path.splitext(self.current_file_path)
            default_name = f"{base}_nobg.png"

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Transparent PNG",
            default_name,
            "PNG Image (*.png)",
        )
        if save_path:
            try:
                result_pil = self.mask_engine.get_export_pil_image("transparent")
                result_pil.save(save_path, format="PNG")
                self.status_msg_label.setText(f"Saved: {os.path.basename(save_path)}")
                QMessageBox.information(self, "Export Successful", f"Saved cutout to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")

    def export_with_background(self):
        if not self.mask_engine.has_image:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Composite Image",
            "cutout_composite.jpg",
            "JPEG Image (*.jpg *.jpeg);;PNG Image (*.png)",
        )
        if save_path:
            try:
                c = self.canvas.bg_color
                rgb_color = (c.red(), c.green(), c.blue())
                bg_mode = self.canvas.bg_mode
                if bg_mode == "checkerboard":
                    bg_mode = "color"
                    rgb_color = (255, 255, 255)

                result_pil = self.mask_engine.get_export_pil_image(
                    bg_mode=bg_mode,
                    bg_color=rgb_color,
                    custom_bg_pil=self.custom_bg_pil,
                )
                fmt = "JPEG" if save_path.lower().endswith((".jpg", ".jpeg")) else "PNG"
                result_pil.save(save_path, format=fmt, quality=95)
                self.status_msg_label.setText(f"Saved: {os.path.basename(save_path)}")
                QMessageBox.information(self, "Export Successful", f"Saved composite image to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")

    def copy_result_to_clipboard(self):
        if not self.mask_engine.has_image:
            return

        try:
            qimg = self.mask_engine.get_composite_rgba_qimage()
            clipboard = QApplication.clipboard()
            clipboard.setImage(qimg)
            self.status_msg_label.setText("✓ Cutout copied to clipboard! Ready to paste into Photoshop, Figma, or Word.")
        except Exception as e:
            QMessageBox.critical(self, "Clipboard Error", f"Failed to copy to clipboard:\n{str(e)}")

    def closeEvent(self, event):
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.requestInterruption()
            self.ai_worker.wait(1000)
        super().closeEvent(event)
