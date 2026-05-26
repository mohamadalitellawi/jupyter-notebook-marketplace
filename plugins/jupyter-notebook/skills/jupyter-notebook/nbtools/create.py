"""Create notebooks from scratch.

``new_notebook`` gives an empty, valid notebook. ``NotebookBuilder`` is a thin
fluent wrapper for assembling one cell at a time when that reads more clearly
than a list comprehension. Both produce standard ``nbformat`` objects that the
rest of the package can edit, inspect, convert, or write.
"""

from __future__ import annotations

from typing import Self

import nbformat
from nbformat import NotebookNode
from nbformat.v4 import new_code_cell, new_markdown_cell, new_raw_cell

from nbtools.io import NBFORMAT_VERSION
from nbtools.types import CellType

# Maps each cell kind to the nbformat constructor that builds it.
_CELL_FACTORIES = {
    CellType.CODE: new_code_cell,
    CellType.MARKDOWN: new_markdown_cell,
    CellType.RAW: new_raw_cell,
}


def new_notebook(metadata: dict | None = None) -> NotebookNode:
    """Create an empty, schema-valid notebook.

    Args:
        metadata: Optional notebook-level metadata (e.g. kernel spec). Defaults
            to empty.

    Returns:
        A new ``NotebookNode`` with no cells.
    """
    notebook = nbformat.v4.new_notebook()
    notebook.nbformat = NBFORMAT_VERSION
    if metadata:
        notebook.metadata.update(metadata)
    return notebook


def make_cell(cell_type: CellType, source: str) -> NotebookNode:
    """Build a single cell of the given kind.

    Args:
        cell_type: The kind of cell to create.
        source: The cell's source text.

    Returns:
        A new cell node.
    """
    return _CELL_FACTORIES[cell_type](source)


class NotebookBuilder:
    """Assemble a notebook one cell at a time.

    Each ``add_*`` method appends a cell and returns ``self``, so calls chain.
    ``build`` returns the accumulated notebook.

    Example:
        notebook = (
            NotebookBuilder()
            .add_markdown("# Title")
            .add_code("x = 1")
            .build()
        )
    """

    def __init__(self, metadata: dict | None = None) -> None:
        """Start an empty builder, optionally seeding notebook metadata."""
        self._notebook = new_notebook(metadata)

    def add_code(self, source: str) -> Self:
        """Append a code cell and return self for chaining."""
        self._notebook.cells.append(make_cell(CellType.CODE, source))
        return self

    def add_markdown(self, source: str) -> Self:
        """Append a markdown cell and return self for chaining."""
        self._notebook.cells.append(make_cell(CellType.MARKDOWN, source))
        return self

    def add_raw(self, source: str) -> Self:
        """Append a raw cell and return self for chaining."""
        self._notebook.cells.append(make_cell(CellType.RAW, source))
        return self

    def build(self) -> NotebookNode:
        """Return the assembled notebook."""
        return self._notebook
