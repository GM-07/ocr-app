"""Extract text from a batch of documents and write one file each."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ocr_app.application.ports import DocumentLoader, Exporter, Preprocessor, Reader
from ocr_app.domain.models import Document, ExportFormat, Page, TextBlock
from ocr_app.domain.reading_order import ordered_blocks
from ocr_app.rgb import ensure_rgb_uint8
from ocr_app.settings import DEFAULT_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass
class InputDocument:
    """A file path or an in-memory camera frame waiting to be read."""

    name: str
    path: Path | None = None
    image: np.ndarray | None = None

    @property
    def label(self) -> str:
        if self.path is not None:
            return str(self.path)
        return self.name


@dataclass(frozen=True)
class FileOutcome:
    """What happened to one input. `error` is set when that file failed."""

    source_name: str
    output_path: Path | None
    error: str | None

    @property
    def ok(self) -> bool:
        return self.error is None and self.output_path is not None


@dataclass
class BatchResult:
    """Outcomes in the same order as the inputs. Failures do not abort the batch."""

    outcomes: list[FileOutcome]

    @property
    def failures(self) -> list[FileOutcome]:
        return [item for item in self.outcomes if item.error]

    @property
    def successes(self) -> list[FileOutcome]:
        return [item for item in self.outcomes if item.error is None]


class ExtractText:
    """Load, preprocess, recognize, order, and export each document."""

    def __init__(
        self,
        reader: Reader,
        preprocessor: Preprocessor,
        loader: DocumentLoader,
        exporters: Mapping[ExportFormat, Exporter],
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        self._reader = reader
        self._preprocessor = preprocessor
        self._loader = loader
        self._exporters = dict(exporters)
        self._confidence_threshold = confidence_threshold

    def execute(
        self,
        documents: Sequence[InputDocument],
        output_dir: Path,
        export_format: ExportFormat,
        on_progress: Callable[[str], None] | None = None,
    ) -> BatchResult:
        exporter = self._exporters.get(export_format)
        if exporter is None:
            raise ValueError(f"Unsupported export format: {export_format.value}")
        output_dir.mkdir(parents=True, exist_ok=True)
        outcomes: list[FileOutcome] = []
        for item in documents:
            try:
                outcomes.append(
                    self._process_one(item, output_dir, export_format, exporter, on_progress)
                )
            except Exception as exc:
                logger.warning("Failed to extract %s: %s", item.label, exc)
                outcomes.append(
                    FileOutcome(source_name=item.label, output_path=None, error=str(exc))
                )
        return BatchResult(outcomes)

    def _process_one(
        self,
        item: InputDocument,
        output_dir: Path,
        export_format: ExportFormat,
        exporter: Exporter,
        on_progress: Callable[[str], None] | None,
    ) -> FileOutcome:
        if on_progress is not None:
            on_progress(f"Extracting {item.label}…")
        document = self._open(item)
        page_blocks: list[list[TextBlock]] = []
        for page in document.pages:
            prepared = self._preprocessor.process(page.image)
            if prepared.ndim != 3 or prepared.shape[2] != 3:
                raise RuntimeError("Preprocessing did not return a 3-channel image")
            recognized = self._reader.read(prepared)
            kept = [
                block
                for block in recognized
                if block.confidence >= self._confidence_threshold
            ]
            page.blocks = ordered_blocks(kept)
            page_blocks.append(page.blocks)
        destination = allocate_output_path(output_dir, document.name, export_format)
        exporter.export(page_blocks, destination)
        return FileOutcome(
            source_name=item.label,
            output_path=destination,
            error=None,
        )

    def _open(self, item: InputDocument) -> Document:
        if item.image is not None:
            image = ensure_rgb_uint8(item.image)
            return Document(
                name=_output_stem(item.name),
                source=item.label,
                pages=[Page(index=0, image=image)],
            )
        if item.path is None:
            raise ValueError(f"No file or image was provided for {item.name}")
        return self._loader.load(item.path)


def allocate_output_path(directory: Path, stem: str, export_format: ExportFormat) -> Path:
    """Pick a free file name. A second document with the same stem gets `-2`."""
    cleaned = _output_stem(stem)
    extension = export_format.extension
    candidate = directory / f"{cleaned}{extension}"
    suffix = 2
    while candidate.exists():
        candidate = directory / f"{cleaned}-{suffix}{extension}"
        suffix += 1
        if suffix > 10_000:
            raise RuntimeError(f"Too many existing files named {cleaned}{extension}")
    return candidate


def _output_stem(name: str) -> str:
    cleaned = _INVALID_FILENAME.sub("_", name).strip().rstrip(".")
    return cleaned or "document"
