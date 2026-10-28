# Remon AI Background Remover Pro

Remon AI Background Remover Pro is a desktop application for removing image backgrounds with AI and refining the result by hand. It is built with Python, PySide6 (Qt), Pillow, and rembg.

Load an image from your computer, paste an image or link, or download an image from a webpage. Run an AI segmentation model, refine the mask with Keep and Delete brushes, preview a replacement background, then export the result.

## Features

- AI background removal with selectable BRIA RMBG, U2Net, ISNet, U2Net Human, and Silueta models.
- Optional alpha matting and mask edge smoothing.
- Keep and Delete brushes, adjustable brush size and hardness, and undo/redo.
- Transparent, solid-color, or custom-image background previews.
- Before/after split view, mask view, and hold-to-peek original view.
- Load images from disk, drag and drop, paste from the clipboard, or fetch from an image URL or webpage.
- Export as PNG, JPEG, WebP, TIFF, BMP, PDF, or ICO.
- Command-line support for opening an image file or URL.

## Requirements

- Python 3.10 or later.
- macOS, Windows, or Linux for running from source. The packaged application and DMG scripts in this repository are for macOS.
- An internet connection the first time a selected AI model is needed, so rembg can download its model if it is not already available. Internet access is also needed to download images from URLs.

The AI model files are managed by rembg and may have separate license terms from this application. Check the relevant model license before redistributing model files or using them commercially.

## Install and run from source

1. Install Python 3.10 or later.
2. Clone or download this repository, then open a terminal in the project directory.
3. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell, activate it with:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

4. Install the project dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

5. Start the application:

   ```bash
   python app.py
   ```

On macOS, the repository also includes `scripts/install_and_launch.command` for installing an already-packaged app bundle from a release or DMG. That script expects the app bundle beside it; it does not install the Python source dependencies.

## Use the application

1. **Load an image.** Choose **Open Image**, drag an image onto the canvas, paste an image from the clipboard, or choose **From URL** to download from a direct image link or a webpage containing an image.
2. **Choose the AI options.** Select a segmentation model. Optionally enable **Alpha Matting** for fine edges such as hair, or **Smooth Edges** to post-process the mask.
3. **Run background removal.** Select **Run AI Background Removal** and wait for processing to finish. The first run with a model may take longer while its model file is downloaded.
4. **Refine the result.** Paint with **Keep Brush** to restore parts of the subject or **Delete Brush** to remove remaining background. Adjust brush size and hardness as needed. Use **Undo** and **Redo** to review strokes.
5. **Preview the background.** Choose a transparent checkerboard, a solid color, or a custom background image. The background choice is also used when saving supported composite formats.
6. **Compare and export.** Use the view controls to compare the original and result. Choose **Quick PNG** for a transparent PNG, or **Save As...** to select another format.

### Open an image or URL from the terminal

Pass one local image path or HTTP(S) URL when starting the app:

```bash
python app.py path/to/photo.jpg
python app.py "https://example.com/photo.jpg"
```

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Cmd/Ctrl+O` | Open an image |
| `Cmd/Ctrl+N` | Start a new project |
| `Cmd/Ctrl+V` | Paste an image or URL |
| `Cmd/Ctrl+S` | Save a transparent PNG |
| `Cmd/Ctrl+Shift+S` | Open Save As |
| `Cmd/Ctrl+Z` | Undo a brush stroke |
| `Cmd/Ctrl+Shift+Z` or `Ctrl+Y` | Redo a brush stroke |
| `1` | Select the Keep brush |
| `2` | Select the Delete brush |
| `H` | Select the Pan tool |
| `[` / `]` | Decrease / increase brush size |
| `F` | Fit the image to the canvas |
| `0` | View at 100% |
| Hold `Tab` | Temporarily view the original image |

## Build the macOS app

The PyInstaller spec file builds a macOS application bundle. To build it from source, install the runtime dependencies and PyInstaller in the active virtual environment:

```bash
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller Remon_AI_Background_Remover.spec
```

The app bundle is created under `dist/`. The spec includes the BRIA model in the bundle only if it is already present at `~/.rembg/models/bria-rmbg/bria-rmbg.onnx` when you build. Otherwise, the packaged app may need internet access to obtain the model on first use.

To create a macOS DMG after building the app bundle:

```bash
./scripts/build_dmg.sh
```

This requires macOS and its command-line tools, including `hdiutil` and `codesign`.

## Project structure

```text
app.py                  Application entry point
requirements.txt        Python dependencies
core/
  downloader.py         Image and webpage image downloader
  mask_engine.py        Mask editing, composition, and export
  processor.py          AI model selection and background processing
ui/
  canvas.py             Image canvas, brush tools, zoom, and comparisons
  main_window.py        Main window and application controls
  theme.py              Application styling
  url_dialog.py         URL input dialog
assets/                 Application icons
scripts/                macOS packaging and installation scripts
```
