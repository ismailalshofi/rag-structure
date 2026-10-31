import pytest

from app.services import ProcessingService

from .conftest import SAMPLES


def test_pdf_chunks_keep_their_page_numbers():
    chunks = ProcessingService.process(str(SAMPLES / "sports.pdf"), "sports.pdf", chunk_size=500, overlap=50)

    assert len(chunks) > 10
    assert {c.page for c in chunks} == {1, 2, 3}
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert all(len(c.text) <= 500 for c in chunks)


def test_text_file(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("# Title\n\nSome notes about retrieval.", encoding="utf-8")

    chunks = ProcessingService.process(str(path), "notes.md", chunk_size=200, overlap=0)

    assert [c.text for c in chunks] == ["# Title Some notes about retrieval."]
    assert chunks[0].page is None


def test_unsupported_file_type(tmp_path):
    path = tmp_path / "sheet.csv"
    path.write_text("a,b", encoding="utf-8")
    with pytest.raises(ValueError):
        ProcessingService.process(str(path), "sheet.csv", 200, 0)


def test_chunk_ids_are_stable_so_reindexing_replaces():
    first = ProcessingService.process(str(SAMPLES / "music.pdf"), "music.pdf", 500, 50)
    second = ProcessingService.process(str(SAMPLES / "music.pdf"), "music.pdf", 500, 50)
    assert [c.id for c in first] == [c.id for c in second]
