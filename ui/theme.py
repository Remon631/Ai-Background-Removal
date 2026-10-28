"""Modern dark design system stylesheet and high-contrast color palette for PySide6 UI."""

DARK_THEME_QSS = """
/* Global Application Styles */
QWidget {
    background-color: #121318;
    color: #e5e7eb;
    font-size: 13px;
    selection-background-color: #4f46e5;
    selection-color: #ffffff;
}

QMainWindow, QDialog {
    background-color: #121318;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #161820;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3b4257;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #6366f1;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: #161820;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #3b4257;
    min-width: 20px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #6366f1;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Splitter */
QSplitter::handle {
    background-color: #262a3a;
    width: 5px;
}
QSplitter::handle:hover {
    background-color: #6366f1;
}

/* Top Global Toolbar Container */
QFrame#topHeaderBar {
    background-color: #181a24;
    border: 1px solid #2d3348;
    border-radius: 8px;
    padding: 3px 6px;
}

/* Canvas Toolbar Container */
QFrame#canvasBarFrame {
    background-color: #161822;
    border: 1px solid #282d3f;
    border-radius: 6px;
    padding: 2px 4px;
}

/* ToolBar & Menu */
QToolBar {
    background-color: #181a24;
    border-bottom: 1px solid #2a2f42;
    spacing: 6px;
    padding: 6px 10px;
}

QMenuBar {
    background-color: #14161f;
    border-bottom: 1px solid #24293a;
    padding: 2px 6px;
    color: #d1d5db;
    font-weight: 500;
}
QMenuBar::item:selected {
    background-color: #2b3147;
    border-radius: 4px;
}
QMenu {
    background-color: #1c1f2c;
    border: 1px solid #363d57;
    padding: 4px;
    border-radius: 6px;
}
QMenu::item {
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    color: #e5e7eb;
}
QMenu::item:selected {
    background-color: #4f46e5;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background-color: #2d3348;
    margin: 4px 6px;
}

/* Side Panels & GroupBoxes */
QGroupBox {
    background-color: #181a24;
    border: 1px solid #2c3246;
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
    color: #cbd5e1;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: #a5b4fc;
}

/* ========================================================================= */
/* BUTTONS - High Visibility, Vivid Elevation & Distinct Visual Contrast    */
/* ========================================================================= */

QPushButton {
    background-color: #272c3d;
    border: 1px solid #434c69;
    border-radius: 6px;
    color: #f8fafc;
    padding: 6px 12px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #353b52;
    border-color: #6366f1;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #1e2230;
}
QPushButton:disabled {
    background-color: #1c1f2b;
    border: 1px solid #2e3346;
    color: #79829c;
}

/* Hero Primary Action Button (Save As...) */
QPushButton#primaryActionBtn, QPushButton#saveAsBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #4f46e5);
    border: 1px solid #818cf8;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    padding: 6px 14px;
}
QPushButton#primaryActionBtn:hover, QPushButton#saveAsBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #4338ca);
    border-color: #c7d2fe;
}
QPushButton#primaryActionBtn:pressed, QPushButton#saveAsBtn:pressed {
    background: #3730a3;
}
QPushButton#primaryActionBtn:disabled, QPushButton#saveAsBtn:disabled {
    background: #25283b;
    border: 1px solid #3c415e;
    color: #8c93b4;
}

/* Run AI Background Removal Button (Sidebar Big Action) */
QPushButton#runAiBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #4f46e5);
    border: 1px solid #a78bfa;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    padding: 7px 8px;
}
QPushButton#runAiBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #4338ca);
    border-color: #ddd6fe;
}
QPushButton#runAiBtn:pressed {
    background: #3730a3;
}
QPushButton#runAiBtn:disabled {
    background: #25283b;
    border: 1px solid #3b405c;
    color: #8c93b4;
}

/* Start New Button (Vibrant Emerald Theme) */
QPushButton#startNewBtn {
    background-color: #065f46;
    border: 1px solid #10b981;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    padding: 6px 13px;
}
QPushButton#startNewBtn:hover {
    background-color: #047857;
    border-color: #34d399;
    color: #ffffff;
}
QPushButton#startNewBtn:pressed {
    background-color: #064e3b;
}
QPushButton#startNewBtn:disabled {
    background-color: #172821;
    border: 1px solid #244234;
    color: #638d77;
}

/* Reset Button (Vibrant Amber / Orange Theme) */
QPushButton#resetBtn {
    background-color: #92400e;
    border: 1px solid #f59e0b;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    padding: 5px 9px;
}
QPushButton#resetBtn:hover {
    background-color: #b45309;
    border-color: #fbbf24;
    color: #ffffff;
}
QPushButton#resetBtn:pressed {
    background-color: #78350f;
}
QPushButton#resetBtn:disabled {
    background-color: #2c2319;
    border: 1px solid #483925;
    color: #8a7556;
}

/* Open File Button (Deep Royal Blue) */
QPushButton#openFileBtn {
    background-color: #1e40af;
    border: 1px solid #3b82f6;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    padding: 6px 12px;
}
QPushButton#openFileBtn:hover {
    background-color: #1d4ed8;
    border-color: #60a5fa;
}
QPushButton#openFileBtn:pressed {
    background-color: #172554;
}

/* Open URL Button (Cyan / Teal) */
QPushButton#openUrlBtn {
    background-color: #0e7490;
    border: 1px solid #06b6d4;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    padding: 6px 12px;
}
QPushButton#openUrlBtn:hover {
    background-color: #0891b2;
    border-color: #22d3ee;
}
QPushButton#openUrlBtn:pressed {
    background-color: #164e63;
}

/* Paste Clipboard Button (Rich Purple) */
QPushButton#pasteClipBtn {
    background-color: #6b21a8;
    border: 1px solid #a855f7;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    padding: 6px 12px;
}
QPushButton#pasteClipBtn:hover {
    background-color: #7e22ce;
    border-color: #c084fc;
}
QPushButton#pasteClipBtn:pressed {
    background-color: #581c87;
}

/* Quick PNG Button (Indigo) */
QPushButton#quickPngBtn {
    background-color: #3730a3;
    border: 1px solid #6366f1;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    padding: 6px 12px;
}
QPushButton#quickPngBtn:hover {
    background-color: #4338ca;
    border-color: #818cf8;
}
QPushButton#quickPngBtn:disabled {
    background-color: #202336;
    border: 1px solid #353957;
    color: #7e84a4;
}

/* Copy Result Button (Slate Steel) */
QPushButton#copyResultBtn {
    background-color: #334155;
    border: 1px solid #64748b;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    padding: 6px 12px;
}
QPushButton#copyResultBtn:hover {
    background-color: #475569;
    border-color: #94a3b8;
}
QPushButton#copyResultBtn:disabled {
    background-color: #1e2430;
    border: 1px solid #333a4d;
    color: #737c90;
}

/* Panel Toggle Button */
QPushButton#toggleSidebarBtn {
    background-color: #262b3c;
    border: 1px solid #404866;
    border-radius: 6px;
    color: #cbd5e1;
    font-weight: 600;
    padding: 6px 11px;
}
QPushButton#toggleSidebarBtn:hover {
    background-color: #333a52;
    border-color: #6366f1;
    color: #ffffff;
}

/* Zoom In / Out Buttons (+ and −) */
QPushButton#zoomBtn {
    background-color: #272c3d;
    border: 1px solid #454e6e;
    border-radius: 5px;
    color: #ffffff;
    font-size: 15px;
    font-weight: 800;
    min-width: 28px;
    max-width: 28px;
    min-height: 26px;
    max-height: 26px;
    padding: 0px;
}
QPushButton#zoomBtn:hover {
    background-color: #3a425c;
    border-color: #818cf8;
    color: #ffffff;
}
QPushButton#zoomBtn:pressed {
    background-color: #1e2230;
}

/* Keep Brush Button (Emerald Theme) */
QPushButton#keepBrushBtn {
    background-color: #064e3b;
    border: 2px solid #059669;
    border-radius: 6px;
    color: #a7f3d0;
    font-weight: 700;
    padding: 6px 6px;
    font-size: 11px;
}
QPushButton#keepBrushBtn:hover:!checked {
    background-color: #047857;
    border-color: #10b981;
    color: #ffffff;
}
QPushButton#keepBrushBtn:checked {
    background-color: #059669;
    border: 2px solid #34d399;
    color: #ffffff;
}

/* Delete Brush Button (Crimson Theme) */
QPushButton#deleteBrushBtn {
    background-color: #450a0a;
    border: 2px solid #b91c1c;
    border-radius: 6px;
    color: #fecaca;
    font-weight: 700;
    padding: 6px 6px;
    font-size: 11px;
}
QPushButton#deleteBrushBtn:hover:!checked {
    background-color: #7f1d1d;
    border-color: #ef4444;
    color: #ffffff;
}
QPushButton#deleteBrushBtn:checked {
    background-color: #dc2626;
    border: 2px solid #f87171;
    color: #ffffff;
}

/* Pan Tool Button (Sky Blue Theme) */
QPushButton#panToolBtn {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #cbd5e1;
    font-weight: 600;
    padding: 6px 12px;
}
QPushButton#panToolBtn:hover:!checked {
    background-color: #334155;
    border-color: #64748b;
    color: #ffffff;
}
QPushButton#panToolBtn:checked {
    background-color: #0284c7;
    border: 2px solid #38bdf8;
    color: #ffffff;
}

/* Inputs & Combos */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1a1c26;
    border: 1px solid #363c54;
    border-radius: 6px;
    padding: 5px 8px;
    color: #f3f4f6;
    font-weight: 500;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #6366f1;
    background-color: #202330;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    background-color: #1c1f2c;
    border: 1px solid #363d57;
    selection-background-color: #4f46e5;
    color: #ffffff;
    padding: 4px;
}

/* Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #2b3044;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #6366f1;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #6366f1;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #ffffff;
    border-color: #a5b4fc;
}

/* Checkbox */
QCheckBox {
    color: #d1d5db;
    spacing: 8px;
    font-weight: 500;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #485273;
    border-radius: 4px;
    background-color: #1a1c26;
}
QCheckBox::indicator:hover {
    border-color: #6366f1;
}
QCheckBox::indicator:checked {
    background-color: #4f46e5;
    border-color: #6366f1;
}

/* Tooltip */
QToolTip {
    background-color: #1f2333;
    color: #f9fafb;
    border: 1px solid #434c6e;
    padding: 5px 9px;
    border-radius: 5px;
    font-size: 11px;
}

/* Status Bar */
QStatusBar {
    background-color: #14161f;
    border-top: 1px solid #262b3c;
    color: #a0aec0;
    font-size: 12px;
}

/* Progress Bar */
QProgressBar {
    background-color: #1a1c26;
    border: 1px solid #363c54;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
    height: 14px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #10b981);
    border-radius: 3px;
}
"""
