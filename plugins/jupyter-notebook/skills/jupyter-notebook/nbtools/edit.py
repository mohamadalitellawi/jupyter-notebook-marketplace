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
