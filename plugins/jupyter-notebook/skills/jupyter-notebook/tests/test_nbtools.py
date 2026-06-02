"""Tests proving the core guarantees: validated round-trips, pure edits,
correct creation, and faithful conversion.

Run with: pytest
"""

from __future__ import annotations

import copy
from pathlib import Path

import nbformat
import pytest

from nbtools import (
    NotebookBuilder,
    add_cell,
    clear_outputs,
    extract_errors,
    extract_source,
    extract_text_outputs,
    from_markdown,
    from_python,
    list_cells,
    move_cell,
    new_notebook,
    read_notebook,
    remove_cell,
    set_cell_metadata,
    to_html,
    to_markdown,
    to_python,
    update_source,
    write_notebook,
)
from nbtools.types import CellType


def _code_cell_with_error():
    """A code cell carrying a synthetic ``error`` output."""
    cell = nbformat.v4.new_code_cell("raise ValueError('boom')")
    cell.outputs = [
        nbformat.v4.new_output(
            "error",
            ename="ValueError",
            evalue="boom",
            traceback=["Traceback (most recent call last):", "ValueError: boom"],
        )
    ]
    return cell


@pytest.fixture
def sample_notebook():
    """A small notebook with one markdown and two code cells."""
    return (
        NotebookBuilder()
        .add_markdown("# Demo")
        .add_code("x = 1")
        .add_code("print(x)")
        .build()
    )


# --- io: round-trip and overwrite guard -----------------------------------


def test_write_then_read_round_trips(sample_notebook, tmp_path: Path):
    path = tmp_path / "nb.ipynb"
    write_notebook(sample_notebook, path)
    reloaded = read_notebook(path)
    assert extract_source(reloaded) == extract_source(sample_notebook)


def test_write_refuses_silent_overwrite(sample_notebook, tmp_path: Path):
    path = tmp_path / "nb.ipynb"
    write_notebook(sample_notebook, path)
    with pytest.raises(FileExistsError):
        write_notebook(sample_notebook, path)
    # Explicit overwrite succeeds.
    assert write_notebook(sample_notebook, path, overwrite=True) == path


def test_read_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        read_notebook(tmp_path / "absent.ipynb")


def test_round_trips_with_string_paths(sample_notebook, tmp_path: Path):
    # The natural thing in a quick script is to pass a str, not a Path.
    path = str(tmp_path / "nb.ipynb")
    written = write_notebook(sample_notebook, path)
    assert isinstance(written, Path)
    reloaded = read_notebook(path)
    assert extract_source(reloaded) == extract_source(sample_notebook)


# --- inspect ----------------------------------------------------------------


def test_list_cells_reports_types_in_order(sample_notebook):
    summaries = list_cells(sample_notebook)
    assert [s.cell_type for s in summaries] == [
        CellType.MARKDOWN,
        CellType.CODE,
        CellType.CODE,
    ]


def test_extract_source_filters_by_type(sample_notebook):
    code = extract_source(sample_notebook, CellType.CODE)
    assert code == ["x = 1", "print(x)"]


def test_extract_text_outputs_reads_stream_and_result(tmp_path: Path):
    nb = new_notebook()
    cell = nbformat.v4.new_code_cell("print('hi')")
    cell.outputs = [
        nbformat.v4.new_output("stream", name="stdout", text="hi\n"),
        nbformat.v4.new_output(
            "execute_result", data={"text/plain": "42"}, execution_count=1
        ),
    ]
    nb.cells.append(cell)
    assert extract_text_outputs(nb) == ["hi\n", "42"]


def test_extract_errors_finds_error_outputs():
    nb = new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell("x = 1"))  # no error
    nb.cells.append(_code_cell_with_error())
    errors = extract_errors(nb)
    assert len(errors) == 1
    assert errors[0].index == 1
    assert errors[0].ename == "ValueError"
    assert errors[0].evalue == "boom"
    assert "ValueError: boom" in errors[0].traceback


def test_extract_errors_empty_when_clean(sample_notebook):
    assert extract_errors(sample_notebook) == []


def test_extract_text_outputs_excludes_errors_by_default():
    nb = new_notebook()
    nb.cells.append(_code_cell_with_error())
    assert extract_text_outputs(nb) == []
    included = extract_text_outputs(nb, include_errors=True)
    assert len(included) == 1
    assert "ValueError: boom" in included[0]


# --- edit: purity and correctness ------------------------------------------


def test_edits_do_not_mutate_original(sample_notebook):
    before = len(sample_notebook.cells)
    add_cell(sample_notebook, CellType.CODE, "y = 2")
    remove_cell(sample_notebook, 0)
    update_source(sample_notebook, 0, "changed")
    move_cell(sample_notebook, 0, 1)
    assert len(sample_notebook.cells) == before
    assert sample_notebook.cells[0].source == "# Demo"


def test_add_cell_appends_and_inserts(sample_notebook):
    appended = add_cell(sample_notebook, CellType.CODE, "y = 2")
    assert appended.cells[-1].source == "y = 2"
    inserted = add_cell(sample_notebook, CellType.RAW, "raw", index=0)
    assert inserted.cells[0].source == "raw"


def test_remove_and_move(sample_notebook):
    removed = remove_cell(sample_notebook, 0)
    assert [c.cell_type for c in removed.cells] == ["code", "code"]
    moved = move_cell(sample_notebook, 0, 2)
    assert moved.cells[2].source == "# Demo"


def test_clear_outputs_strips_outputs_without_mutating(sample_notebook):
    # Give a code cell some outputs and an execution_count to clear.
    nb = copy.deepcopy(sample_notebook)
    nb.cells[1].outputs = [
        nbformat.v4.new_output("stream", name="stdout", text="hi\n")
    ]
    nb.cells[1].execution_count = 7

    cleared = clear_outputs(nb)
    assert cleared.cells[1].outputs == []
    assert cleared.cells[1].execution_count is None
    # Purity: the original is untouched.
    assert nb.cells[1].outputs != []
    assert nb.cells[1].execution_count == 7


def test_set_cell_metadata_merges_by_default(sample_notebook):
    seeded = set_cell_metadata(sample_notebook, 1, {"scrolled": True})
    merged = set_cell_metadata(seeded, 1, {"tags": ["hide-cell"]})
    # Merge keeps the previously-set key alongside the new one.
    assert merged.cells[1].metadata["scrolled"] is True
    assert merged.cells[1].metadata["tags"] == ["hide-cell"]


def test_set_cell_metadata_replace_drops_existing_keys(sample_notebook):
    seeded = set_cell_metadata(sample_notebook, 1, {"scrolled": True})
    replaced = set_cell_metadata(seeded, 1, {"tags": ["x"]}, merge=False)
    assert "scrolled" not in replaced.cells[1].metadata
    assert replaced.cells[1].metadata["tags"] == ["x"]


def test_set_cell_metadata_is_pure(sample_notebook):
    set_cell_metadata(sample_notebook, 1, {"tags": ["x"]})
    assert "tags" not in sample_notebook.cells[1].metadata


def test_out_of_range_index_raises(sample_notebook):
    with pytest.raises(IndexError):
        remove_cell(sample_notebook, 99)
    with pytest.raises(IndexError):
        add_cell(sample_notebook, CellType.CODE, "z", index=99)


# --- execute (optional; skipped without the 'execute' extra) ---------------


def test_execute_notebook_populates_outputs():
    pytest.importorskip("nbclient")
    from nbtools import execute_notebook

    nb = NotebookBuilder().add_code("x = 2 + 2\nprint(x)").build()
    executed = execute_notebook(nb)
    assert "4" in "".join(extract_text_outputs(executed))
    # Purity: the original notebook gained no outputs.
    assert nb.cells[0].get("outputs", []) == []


def test_execute_notebook_records_errors_when_allowed():
    pytest.importorskip("nbclient")
    from nbtools import execute_notebook

    nb = NotebookBuilder().add_code("raise ValueError('boom')").build()
    executed = execute_notebook(nb, allow_errors=True)
    errors = extract_errors(executed)
    assert len(errors) == 1
    assert errors[0].ename == "ValueError"


# --- convert ----------------------------------------------------------------


def test_to_python_marks_cells(sample_notebook):
    script = to_python(sample_notebook)
    assert "# %% [markdown]" in script
    assert "# %%\nx = 1" in script
    # Markdown content is commented so the script stays valid Python.
    assert "# # Demo" in script


def test_to_markdown_fences_code(sample_notebook):
    md = to_markdown(sample_notebook)
    assert "# Demo" in md
    assert "```python\nx = 1\n```" in md


def test_to_html_escapes_code_and_renders_markdown(sample_notebook):
    edited = update_source(sample_notebook, 1, "a < b and c > d")
    out = to_html(edited, title="T")
    assert "<title>T</title>" in out
    assert "<h1>Demo</h1>" in out  # markdown rendered
    assert "a &lt; b and c &gt; d" in out  # code escaped, not executed


# --- reverse conversion: round-trips ---------------------------------------


def _kinds_and_sources(nb):
    """Helper: list of (cell_type, source) for comparison."""
    return [(c.cell_type, c.source) for c in nb.cells]


def test_python_round_trip_is_lossless(sample_notebook):
    restored = from_python(to_python(sample_notebook))
    assert _kinds_and_sources(restored) == _kinds_and_sources(sample_notebook)


def test_markdown_round_trip_is_lossless(sample_notebook):
    restored = from_markdown(to_markdown(sample_notebook))
    assert _kinds_and_sources(restored) == _kinds_and_sources(sample_notebook)


def test_markdown_round_trip_survives_fence_inside_markdown_cell():
    # The previously-lossy case: a markdown cell whose body contains a ```python
    # fence. The explicit cell markers must keep it as ONE markdown cell.
    nb = (
        NotebookBuilder()
        .add_markdown("Example:\n```python\ny = 2\n```\ndone")
        .add_code("z = 3")
        .build()
    )
    restored = from_markdown(to_markdown(nb))
    assert _kinds_and_sources(restored) == _kinds_and_sources(nb)
    assert len(restored.cells) == 2


def test_from_python_tolerates_marker_variants():
    script = "#%%\nx = 1\n\n#%% [markdown]\n# Title\n\n# %%   \ny = 2\n"
    nb = from_python(script)
    kinds = [c.cell_type for c in nb.cells]
    assert kinds == ["code", "markdown", "code"]
    assert nb.cells[0].source == "x = 1"
    assert nb.cells[1].source == "Title"
    assert nb.cells[2].source == "y = 2"


def test_from_python_no_markers_is_single_code_cell():
    nb = from_python("import numpy as np\nprint(np.pi)\n")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "code"


def test_from_markdown_heuristic_fallback_without_markers():
    md = "# Heading\n\n```python\nx = 1\n```\n\nmore text\n"
    nb = from_markdown(md)
    kinds = [c.cell_type for c in nb.cells]
    assert kinds == ["markdown", "code", "markdown"]
    assert nb.cells[1].source == "x = 1"


def test_reverse_converters_return_validated_notebooks(tmp_path):
    # A reconstructed notebook must be writable (i.e. schema-valid).
    nb = from_python("# %%\nx = 1\n")
    assert write_notebook(nb, tmp_path / "out.ipynb").exists()


# --- documented limitations (pinned so they cannot regress silently) -------
# These are inherent to the text formats: cell content that collides with the
# format's own delimiter cannot be represented. The .ipynb file is the source
# of truth. See SKILL.md / README "Limitations".


def test_known_limit_marker_like_line_in_code_cell_splits():
    # A code cell whose source is literally a `# %%` marker line cannot survive
    # the .py round-trip: the marker is indistinguishable from the comment.
    nb = NotebookBuilder().add_code("# %%\nx = 1").build()
    restored = from_python(to_python(nb))
    assert len(restored.cells) == 2  # documented split, not a single cell


def test_known_limit_marker_like_line_in_markdown_cell_splits():
    # A markdown cell whose body contains the literal cell marker splits.
    nb = NotebookBuilder().add_markdown("text\n<!-- cell:code -->\nmore").build()
    restored = from_markdown(to_markdown(nb))
    assert len(restored.cells) == 2  # documented split


def test_known_limit_empty_input_yields_no_cells():
    assert len(from_python("").cells) == 0
    assert len(from_markdown("").cells) == 0
