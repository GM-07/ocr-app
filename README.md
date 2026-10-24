# OCR

Extract text from JPG, JPEG, PNG, GIF, and PDF files. The desktop window can also capture one frame from a camera. Each input becomes one PDF or Word document. Multi-page PDFs and multi-frame GIFs are combined in page or frame order.

## Requirements

Python 3.11 or newer.

The desktop window needs Tk. On Debian or Ubuntu install it with `python3-tk`. The `ocr` command does not need a display.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows, activate the environment with `.venv\Scripts\activate`.

To run the tests as well:

```bash
pip install -e ".[dev]"
```

The first real recognition run downloads EasyOCR's English models into `~/.EasyOCR`. Later runs reuse those files. The test suite uses a fake reader and does not download models.

## Desktop window

```bash
ocr-app
```

`python -m ocr_app` opens the same window.

The window appears immediately. The OCR engine loads on a background thread, and the status line shows progress. Select documents (a new selection replaces the current batch), choose an output folder, leave PDF selected or switch to Word, then extract. **Capture from camera** adds one frame to the batch. Camera capture is only in the window. If no camera is present, the app shows an error and the other controls keep working.

## Command line

PDF is the default. Use `--format docx` for Word. `--output-dir` is the folder that receives one file per input.

```bash
ocr scan.jpg --output-dir out
ocr diagram.png --output-dir out
ocr frames.gif --output-dir out
ocr report.pdf --output-dir out
ocr scan.jpg diagram.png frames.gif report.pdf --output-dir out
ocr report.pdf --output-dir out --format docx
```

A problem with one file is printed, and the command continues with the rest. The process exits with status 1 when any file fails.

## Languages

The recognition languages are the `OCR_LANGUAGES` tuple in `src/ocr_app/settings.py`. The default is English (`en`). Edit that tuple when you want EasyOCR to load another language. The first real run downloads the models for whatever that tuple lists. With the default, that is the English model.

Blocks below a confidence of 0.4 are dropped. That threshold is `DEFAULT_CONFIDENCE_THRESHOLD` in the same file.

## Tests

```bash
pytest
```

## License

The application is released under the MIT License. See [LICENSE](LICENSE).

PDF export embeds DejaVu Sans so accents are preserved. That font is bundled under its own license: `src/ocr_app/fonts/LICENSE-DEJAVU.txt`.
