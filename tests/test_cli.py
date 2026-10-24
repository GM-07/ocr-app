"""The file command writes PDF by default and does not need the window."""

from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas

from ocr_app.cli import run
from ocr_app.domain.models import BBox, TextBlock
from tests.helpers import FakeReader, build_use_case, docx_text, pdf_text


def _reader() -> FakeReader:
    return FakeReader([TextBlock("Hello", 0.99, BBox(0, 0, 12, 10))])


def _jpeg(path: Path) -> None:
    Image.new("RGB", (24, 16), "white").save(path, format="JPEG")


def _png(path: Path) -> None:
    Image.new("RGB", (24, 16), "white").save(path)


def _gif(path: Path) -> None:
    Image.new("RGB", (16, 12), (255, 0, 0)).save(path, format="GIF")


def _pdf(path: Path) -> None:
    writer = canvas.Canvas(str(path), pagesize=(72, 72))
    writer.drawString(18, 36, "page")
    writer.save()


def test_output_dir_is_required() -> None:
    assert run(["scan.jpg"]) == 2


def test_unknown_format_is_rejected(tmp_path: Path) -> None:
    assert run(["scan.jpg", "--output-dir", str(tmp_path), "--format", "txt"]) == 2


def test_cli_writes_pdf_for_jpg_png_gif_and_pdf(tmp_path: Path, capsys) -> None:
    jpeg = tmp_path / "scan.jpg"
    png = tmp_path / "diagram.png"
    gif = tmp_path / "frames.gif"
    pdf = tmp_path / "report.pdf"
    _jpeg(jpeg)
    _png(png)
    _gif(gif)
    _pdf(pdf)
    output_dir = tmp_path / "out"

    code = run(
        [
            str(jpeg),
            str(png),
            str(gif),
            str(pdf),
            "--output-dir",
            str(output_dir),
        ],
        reader_factory=_reader,
        extract_factory=build_use_case,
    )

    assert code == 0
    written = sorted(path.name for path in output_dir.iterdir())
    assert written == ["diagram.pdf", "frames.pdf", "report.pdf", "scan.pdf"]
    assert "Hello" in pdf_text(output_dir / "scan.pdf")
    captured = capsys.readouterr()
    assert str(output_dir) in captured.out
    assert captured.err == ""


def test_cli_docx_format_writes_word(tmp_path: Path) -> None:
    source = tmp_path / "diagram.png"
    _png(source)
    output_dir = tmp_path / "out"

    code = run(
        [str(source), "--output-dir", str(output_dir), "--format", "docx"],
        reader_factory=_reader,
        extract_factory=build_use_case,
    )

    assert code == 0
    assert docx_text(output_dir / "diagram.docx") == "Hello"
    assert list(output_dir.glob("*.pdf")) == []


def test_cli_reports_unreadable_paths_and_continues(tmp_path: Path, capsys) -> None:
    good = tmp_path / "ok.png"
    _png(good)
    missing = tmp_path / "missing.png"
    output_dir = tmp_path / "out"

    code = run(
        [str(missing), str(good), "--output-dir", str(output_dir)],
        reader_factory=_reader,
        extract_factory=build_use_case,
    )

    assert code == 1
    assert pdf_text(output_dir / "ok.pdf") == "Hello"
    captured = capsys.readouterr()
    assert "missing.png" in captured.err
    assert "1 file(s) failed." in captured.err
    assert str(output_dir) in captured.out
