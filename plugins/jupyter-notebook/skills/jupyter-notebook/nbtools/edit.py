"""Edit notebook cells.

Every function here is pure: it deep-copies the input notebook, modifies the
copy, and returns it. The original the caller passed in is never touched. This
makes edits composable and predictable -- there is no hidden state and no
surprise mutation of a notebook held elsewhere.

Indices are zero-based and validated; an out-of-range index raises
``IndexError`` rather than silently doing nothing.
"""

from __future__ import annotations

import copy

from nbformat import NotebookNode

from nbtools.create import make_cell
from nbtools.types import CellType


def _validate_index(notebook: NotebookNode, index: int, *, for_insert: bool) -> None:
    """Raise ``IndexError`` if ``index`` is not addressable.

    For insertion, an index equal to the cell count is allowed (append at end);
    for access/removal it is not.
    """
    upper = len(notebook.cells) if for_insert else len(notebook.cells) - 1
    if not 0 <= index <= upper:
        kind = "insert at" if for_insert else "access"
        raise IndexError(
            f"Cannot {kind} index {index}; notebook has {len(notebook.cells)} cells."
        )


def add_cell(
    notebook: NotebookNode,
    cell_type: CellType,
    source: str,
    index: int | None = None,
) -> NotebookNode:
    """Return a copy with a new cell inserted.

    Args:
        notebook: Source notebook (not modified).
        cell_type: Kind of cell to add.
        source: Source text for the new cell.
        index: Position to insert at. ``None`` appends to the end. An index
            equal to the cell count also appends.

    Returns:
        A new notebook with the cell inserted.

    Raises:
        IndexError: If ``index`` is out of the insertable range.
    """
    result = copy.deepcopy(notebook)
    position = len(result.cells) if index is None else index
    _validate_index(result, position, for_insert=True)
    result.cells.insert(position, make_cell(cell_type, source))
    return result


def remove_cell(notebook: NotebookNode, index: int) -> NotebookNode:
    """Return a copy with the cell at ``index`` removed.

    Args:
        notebook: Source notebook (not modified).
        index: Zero-based index of the cell to remove.

    Returns:
        A new notebook without that cell.

    Raises:
        IndexError: If ``index`` is out of range.
    """
    result = copy.deepcopy(notebook)
    _validate_index(result, index, for_insert=False)
    del result.cells[index]
    return result


def move_cell(notebook: NotebookNode, from_index: int, to_index: int) -> NotebookNode:
    """Return a copy with one cell moved to a new position.

    ``to_index`` is interpreted against the notebook *after* the cell is lifted
    out, matching the intuitive "drag this cell to slot N" behaviour.

    Args:
        notebook: Source notebook (not modified).
        from_index: Current index of the cell to move.
        to_index: Destination index after removal.

    Returns:
        A new notebook with the cell repositioned.

    Raises:
        IndexError: If either index is out of range.
    """
    result = copy.deepcopy(notebook)
    _validate_index(result, from_index, for_insert=False)
    cell = result.cells.pop(from_index)
    _validate_index(result, to_index, for_insert=True)
    result.cells.insert(to_index, cell)
    return result


def update_source(notebook: NotebookNode, index: int, source: str) -> NotebookNode:
    """Return a copy with the source text of one cell replaced.

    The cell's kind is preserved; only its source changes.

    Args:
        notebook: Source notebook (not modified).
        index: Index of the cell to edit.
        source: New source text.

    Returns:
        A new notebook with the updated cell.

    Raises:
        IndexError: If ``index`` is out of range.
    """
    result = copy.deepcopy(notebook)
    _validate_index(result, index, for_insert=False)
    result.cells[index].source = source
    return result


def set_cell_metadata(
    notebook: NotebookNode,
    index: int,
    metadata: dict,
    *,
    merge: bool = True,
) -> NotebookNode:
    """Return a copy with one cell's metadata updated.

    The common use is setting cell *tags* (e.g. ``{"tags": ["remove-input"]}``)
    that notebook-print pipelines such as nbconvert and Quarto act on.

    Merging is *shallow*: with ``merge=True`` each top-level key in ``metadata``
    replaces that key on the cell (like ``dict.update``), leaving other existing
    keys intact. It does not deep-merge nested lists or dicts, so passing
    ``{"tags": [...]}`` swaps the whole ``tags`` list rather than appending to
    it. With ``merge=False`` the cell's metadata is replaced wholesale.

    Args:
        notebook: Source notebook (not modified).
        index: Index of the cell whose metadata to set.
        metadata: Metadata keys to apply.
        merge: If ``True`` (default), update existing metadata key-by-key; if
            ``False``, replace the cell's metadata entirely.

    Returns:
        A new notebook with the cell's metadata updated.

    Raises:
        IndexError: If ``index`` is out of range.
    """
    result = copy.deepcopy(notebook)
    _validate_index(result, index, for_insert=False)
    cell = result.cells[index]
    if merge:
        cell.metadata.update(metadata)
    else:
        cell.metadata = copy.deepcopy(metadata)
    return result


def clear_outputs(notebook: NotebookNode) -> NotebookNode:
    """Return a copy with every code cell's outputs and counts cleared.

    Useful for shipping a notebook without executed outputs: clean diffs, no
    embedded local paths or timestamps, "ships without outputs" templates. Each
    code cell's ``outputs`` is emptied and its ``execution_count`` reset to
    ``None``; markdown and raw cells are untouched.

    Args:
        notebook: Source notebook (not modified).

    Returns:
        A new notebook with all code-cell outputs removed.
    """
    result = copy.deepcopy(notebook)
    for cell in result.cells:
        if cell.cell_type == CellType.CODE:
            cell["outputs"] = []
            cell["execution_count"] = None
    return result
