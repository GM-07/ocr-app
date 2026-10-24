"""Thin Tk window. OCR starts on a background thread after the window is shown."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ocr_app.application.extract_text import BatchResult, ExtractText, InputDocument
from ocr_app.application.ports import Camera, Reader
from ocr_app.domain.models import ExportFormat
from ocr_app.presentation.batch import DocumentBatch

ReaderFactory = Callable[[], Reader]
ExtractFactory = Callable[[Reader], ExtractText]

FILE_TYPES = [
    ("Documents", "*.jpg *.jpeg *.png *.gif *.pdf *.JPG *.JPEG *.PNG *.GIF *.PDF"),
    ("Images", "*.jpg *.jpeg *.png *.gif"),
    ("PDF", "*.pdf"),
]


class MainWindow(tk.Tk):
    """Select documents, pick a folder, and extract text to PDF or Word."""

    def __init__(
        self,
        reader_factory: ReaderFactory,
        extract_factory: ExtractFactory,
        camera: Camera,
    ) -> None:
        super().__init__()
        self._reader_factory = reader_factory
        self._extract_factory = extract_factory
        self._camera = camera
        self._batch = DocumentBatch()
        self._output_dir: Path | None = None
        self._reader: Reader | None = None
        self._reader_error: str | None = None
        self._engine_ready = threading.Event()
        self._ui_queue: queue.Queue[Callable[[], None]] = queue.Queue()

        self.title("Text extraction")
        self.geometry("800x600")
        self.minsize(780, 520)
        self._apply_theme()
        self._build()
        self._status_var.set("Loading OCR engine…")
        self.after(40, self._poll_ui_queue)
        self._engine_thread = threading.Thread(
            target=self._load_engine,
            name="ocr-engine",
            daemon=True,
        )
        self._engine_thread.start()

    def run(self) -> None:
        self.mainloop()

    def _apply_theme(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        padding = {"padx": 10, "pady": 4}

        intro = ttk.Label(
            self,
            text="Extract text from images and PDFs. One output file per document.",
        )
        intro.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", **padding)
        self._select_button = ttk.Button(
            toolbar, text="Select documents", command=self._select_documents
        )
        self._folder_button = ttk.Button(
            toolbar, text="Choose output folder", command=self._choose_folder
        )
        self._camera_button = ttk.Button(
            toolbar, text="Capture from camera", command=self._capture
        )
        self._select_button.grid(row=0, column=0, padx=(0, 6))
        self._folder_button.grid(row=0, column=1, padx=6)
        self._camera_button.grid(row=0, column=2, padx=6)

        options = ttk.Frame(self)
        options.grid(row=2, column=0, sticky="ew", **padding)
        ttk.Label(options, text="Export as").grid(row=0, column=0, padx=(0, 8))
        self._format_var = tk.StringVar(value=ExportFormat.PDF.value)
        ttk.Radiobutton(
            options, text="PDF", value=ExportFormat.PDF.value, variable=self._format_var
        ).grid(row=0, column=1, padx=4)
        ttk.Radiobutton(
            options, text="Word", value=ExportFormat.DOCX.value, variable=self._format_var
        ).grid(row=0, column=2, padx=4)
        self._extract_button = ttk.Button(
            options, text="Extract text", command=self._start_extraction
        )
        self._extract_button.grid(row=0, column=3, padx=(16, 0))

        self._folder_var = tk.StringVar(value="Output folder: not chosen")
        ttk.Label(self, textvariable=self._folder_var, wraplength=760).grid(
            row=3, column=0, sticky="ew", padx=12, pady=(0, 2)
        )

        list_frame = ttk.Frame(self)
        list_frame.grid(row=4, column=0, sticky="nsew", padx=12, pady=4)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        self._hint_var = tk.StringVar(
            value="No documents yet. Select files or capture a camera frame."
        )
        ttk.Label(list_frame, textvariable=self._hint_var).grid(row=0, column=0, sticky="w")
        self._files = tk.Listbox(list_frame, height=12, activestyle="dotbox")
        y_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self._files.yview)
        x_scroll = ttk.Scrollbar(list_frame, orient="horizontal", command=self._files.xview)
        self._files.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self._files.grid(row=1, column=0, sticky="nsew")
        y_scroll.grid(row=1, column=1, sticky="ns")
        x_scroll.grid(row=2, column=0, sticky="ew")

        self._status_var = tk.StringVar(value="Loading OCR engine…")
        self._status_label = ttk.Label(self, textvariable=self._status_var, wraplength=760)
        self._status_label.grid(row=5, column=0, sticky="ew", padx=12, pady=(4, 10))
        self._actions = (
            self._select_button,
            self._folder_button,
            self._camera_button,
            self._extract_button,
        )

    @property
    def format_var(self) -> tk.StringVar:
        return self._format_var

    def _load_engine(self) -> None:
        try:
            reader = self._reader_factory()
        except Exception as exc:
            self._reader_error = str(exc)
            self._post(lambda message=str(exc): self._status_var.set(
                f"OCR engine unavailable: {message}"
            ))
        else:
            self._reader = reader
            self._post(lambda: self._status_var.set("Ready"))
        finally:
            self._engine_ready.set()

    def _select_documents(self) -> None:
        selected = filedialog.askopenfilenames(title="Select documents", filetypes=FILE_TYPES)
        if not selected:
            return
        self._batch.replace_with_files([Path(path) for path in selected])
        self._refresh_files()
        count = len(self._batch.items)
        self._status_var.set(f"{count} document(s) selected.")

    def _choose_folder(self) -> None:
        chosen = filedialog.askdirectory(title="Choose output folder")
        if not chosen:
            return
        self._output_dir = Path(chosen)
        self._folder_var.set(f"Output folder: {chosen}")

    def _capture(self) -> None:
        try:
            captured = self._camera.capture()
        except Exception as exc:
            messagebox.showerror("Camera", f"No camera is available. {exc}")
            return
        if not captured.ok or captured.image is None:
            messagebox.showerror("Camera", captured.error or "No camera is available.")
            return
        self._batch.add_camera_frame(captured.image)
        self._refresh_files()
        self._status_var.set(f"Added a camera frame. {len(self._batch.items)} in the batch.")

    def _start_extraction(self) -> None:
        if not self._batch.items:
            messagebox.showwarning(
                "Nothing selected",
                "Nothing selected. Choose documents or capture a camera frame, then extract.",
            )
            return
        if self._output_dir is None:
            messagebox.showwarning(
                "No output directory",
                "No output directory. Choose a folder for the PDF or Word files.",
            )
            return
        items = self._batch.items
        output_dir = self._output_dir
        export_format = ExportFormat(self._format_var.get())
        self._set_actions_enabled(False)
        self._status_var.set("Extracting text…")
        threading.Thread(
            target=self._extract,
            args=(items, output_dir, export_format),
            name="ocr-extract",
            daemon=True,
        ).start()

    def _extract(
        self,
        items: list[InputDocument],
        output_dir: Path,
        export_format: ExportFormat,
    ) -> None:
        try:
            if not self._engine_ready.is_set():
                self._post(lambda: self._status_var.set("Waiting for the OCR engine…"))
            self._engine_ready.wait()
            reader = self._reader
            if reader is None:
                detail = self._reader_error or "The OCR engine did not start."
                self._post(lambda message=detail: self._show_fatal(message))
                return
            use_case = self._extract_factory(reader)
            result = use_case.execute(
                items,
                output_dir,
                export_format,
                on_progress=self._post_status,
            )
            self._post(lambda: self._show_result(result, output_dir))
        except Exception as exc:
            detail = str(exc)
            self._post(lambda message=detail: self._show_fatal(message))

    def _show_result(self, result: BatchResult, output_dir: Path) -> None:
        try:
            if result.failures:
                lines = [f"{item.source_name}: {item.error}" for item in result.failures]
                messagebox.showwarning("Some files failed", "Some files failed:\n\n" + "\n".join(lines))
            saved = len(result.successes)
            messagebox.showinfo(
                "Processing finished",
                f"Processing finished.\n\nSaved {saved} file(s).\n\nOutput directory:\n{output_dir}",
            )
        finally:
            self._mark_idle()

    def _show_fatal(self, message: str) -> None:
        try:
            messagebox.showerror("Extraction failed", message)
        finally:
            self._mark_idle()

    def _mark_idle(self) -> None:
        self._set_actions_enabled(True)
        if self._reader is not None:
            self._status_var.set("Ready")
        elif self._reader_error:
            self._status_var.set(f"OCR engine unavailable: {self._reader_error}")

    def _refresh_files(self) -> None:
        self._files.delete(0, "end")
        items = self._batch.items
        if not items:
            self._hint_var.set("No documents yet. Select files or capture a camera frame.")
            return
        self._hint_var.set("Documents in this batch")
        for item in items:
            if item.path is not None:
                self._files.insert("end", str(item.path))
            else:
                self._files.insert("end", f"{item.name} (camera frame)")

    def _set_actions_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for button in self._actions:
            button.configure(state=state)

    def _post_status(self, text: str) -> None:
        self._post(lambda message=text: self._status_var.set(message))

    def _post(self, callback: Callable[[], None]) -> None:
        self._ui_queue.put(callback)

    def _poll_ui_queue(self) -> None:
        while True:
            try:
                callback = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            callback()
        self.after(40, self._poll_ui_queue)
