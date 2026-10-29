# OCR

Extract text from photos, scans, and PDFs on your own computer. Each file becomes one PDF or one Word document. Nothing is uploaded.

The desktop window can also take a single camera frame. The `ocr` command does the same extraction without a window.

## Guidelines for readers

Read this before you run a batch or change the code.

- **Your files stay local.** Recognition runs in this process. The first real run downloads EasyOCR’s English model into `~/.EasyOCR`. Later runs reuse that file.
- **One input, one output.** A multi-page PDF stays one document, in page order. A multi-frame GIF stays one document, in frame order. A folder of files produces one result per file.
- **English is the default.** The language list is `OCR_LANGUAGES` in [`src/ocr_app/settings.py`](src/ocr_app/settings.py). It is `("en",)`. Add another EasyOCR language code there before the first run if you need it. That first run then downloads the extra model.
- **Low-confidence text is dropped.** A block under `0.4` is not written. That cutoff is `DEFAULT_CONFIDENCE_THRESHOLD` in the same file. Raise it when the page is noisy. Lower it when faint text is being skipped.
- **Reading order is visual, not the raw detector order.** Words on the same line are joined left to right. Lines run top to bottom. Pages are separated by a blank line.
- **A bad file does not stop the batch.** The command prints the path and the error, continues, and exits with status `1` if anything failed.
- **The camera is only in the window.** `ocr` reads JPG, JPEG, PNG, GIF, and PDF paths. If no camera is present, the window shows an error and the other controls keep working.
- **The desktop window needs Tk.** On Debian or Ubuntu, install `python3-tk`. The `ocr` command does not need a display.

## Requirements

Python 3.11 or newer.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows, activate with `.venv\Scripts\activate`.

To run the tests as well:

```bash
pip install -e ".[dev]"
pytest
```

The tests use a fake reader. They do not download models.

## Desktop window

```bash
ocr-app
```

`python -m ocr_app` opens the same window.

The window appears immediately. The engine loads on a background thread, and the status line shows progress.

1. Select documents. A new selection replaces the current batch.
2. Choose an output folder.
3. Leave PDF selected, or switch to Word.
4. Extract.

**Capture from camera** adds one frame to the batch.

## Command line

PDF is the default. `--output-dir` is the folder that receives one file per input.

```bash
ocr scan.jpg --output-dir out
ocr diagram.png --output-dir out
ocr frames.gif --output-dir out
ocr report.pdf --output-dir out
ocr scan.jpg diagram.png frames.gif report.pdf --output-dir out
ocr report.pdf --output-dir out --format docx
```

## Where to read the code

| Path | What it owns |
| --- | --- |
| `src/ocr_app/presentation/` | The window and the batch the window is holding |
| `src/ocr_app/application/` | Extract one batch: load, preprocess, recognize, export |
| `src/ocr_app/domain/` | Pages, text blocks, and reading order |
| `src/ocr_app/infrastructure/` | EasyOCR, image loading, camera, PDF and Word export |
| `src/ocr_app/settings.py` | Language list and confidence cutoff |
| `src/ocr_app/cli.py` | The `ocr` command |

## License

[MIT](LICENSE). PDF export embeds DejaVu Sans so accents are preserved. That font has its own license: [`src/ocr_app/fonts/LICENSE-DEJAVU.txt`](src/ocr_app/fonts/LICENSE-DEJAVU.txt).
