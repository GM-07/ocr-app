"""ExtractText with a fake reader writes text and keeps going after a bad file."""

from pathlib import Path

from PIL import Image

from ocr_app.application.extract_text import InputDocument
from ocr_app.domain.models import BBox, ExportFormat, TextBlock
from tests.helpers import FakeReader, ScriptedReader, build_use_case, docx_text, pdf_text


def _white_png(path: Path) -> None:
    Image.new("RGB", (32, 24), "white").save(path)


def test_extract_writes_expected_text_and_drops_low_confidence(tmp_path: Path) -> None:
    source = tmp_path / "note.png"
    _white_png(source)
    reader = FakeReader(
        [
            TextBlock("world", 0.92, BBox(40, 0, 90, 12)),
            TextBlock("Hello", 0.95, BBox(0, 1, 30, 12)),
            TextBlock("secret", 0.39, BBox(0, 40, 40, 52)),
            TextBlock("kept", 0.4, BBox(0, 40, 30, 52)),
        ]
    )
    use_case = build_use_case(reader)
    output_dir = tmp_path / "out"

    pdf_result = use_case.execute(
        [InputDocument(name="note", path=source)],
        output_dir,
        ExportFormat.PDF,
    )
    docx_result = use_case.execute(
        [InputDocument(name="note", path=source)],
        output_dir,
        ExportFormat.DOCX,
    )

    assert pdf_result.failures == []
    assert docx_result.failures == []
    assert reader.shapes and all(shape[2] == 3 for shape in reader.shapes)
    expected = "Hello world\nkept"
    assert docx_text(docx_result.successes[0].output_path) == expected
    assert pdf_text(pdf_result.successes[0].output_path).replace("\r", "") == expected
    assert pdf_result.successes[0].output_path.suffix == ".pdf"
    assert docx_result.successes[0].output_path.suffix == ".docx"


def test_multipage_gif_becomes_one_document_in_frame_order(tmp_path: Path) -> None:
    path = tmp_path / "clip.gif"
    frames = [
        Image.new("RGB", (16, 12), (255, 0, 0)),
        Image.new("RGB", (16, 12), (0, 0, 255)),
    ]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=40, loop=0)
    reader = ScriptedReader(
        [
            [TextBlock("Hello", 0.99, BBox(0, 0, 20, 10))],
            [TextBlock("café", 0.88, BBox(0, 0, 20, 10))],
        ]
    )
    result = build_use_case(reader).execute(
        [InputDocument(name="clip", path=path)],
        tmp_path / "out",
        ExportFormat.DOCX,
    )

    assert result.failures == []
    assert len(list((tmp_path / "out").glob("*.docx"))) == 1
    assert len(reader.shapes) == 2
    assert docx_text(result.successes[0].output_path) == "Hello\n\ncafé"


def test_unreadable_path_is_recorded_and_batch_continues(tmp_path: Path) -> None:
    good = tmp_path / "ok.png"
    _white_png(good)
    missing = tmp_path / "missing.png"
    not_a_file = tmp_path / "folder"
    not_a_file.mkdir()
    reader = FakeReader([TextBlock("Hello", 0.99, BBox(0, 0, 10, 10))])

    result = build_use_case(reader).execute(
        [
            InputDocument(name="missing", path=missing),
            InputDocument(name="folder", path=not_a_file),
            InputDocument(name="ok", path=good),
        ],
        tmp_path / "out",
        ExportFormat.DOCX,
    )

    assert len(result.outcomes) == 3
    assert result.outcomes[0].error
    assert "missing.png" in result.outcomes[0].error
    assert result.outcomes[1].error
    assert result.outcomes[2].error is None
    assert docx_text(result.outcomes[2].output_path) == "Hello"
    assert result.outcomes[2].output_path.is_file()
