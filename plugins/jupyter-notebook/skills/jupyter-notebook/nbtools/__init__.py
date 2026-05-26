"""nbtools -- read, edit, create, and convert Jupyter notebooks.

Built on the official ``nbformat`` library so notebooks are always validated
against the Jupyter schema. The public API is re-exported here for convenience.
"""

from __future__ import annotations

from nbtools.convert import (
    from_markdown,
    from_python,
    to_html,
    to_markdown,
    to_python,
)
from nbtools.create import NotebookBuilder, make_cell, new_notebook
from nbtools.edit import add_cell, move_cell, remove_cell, update_source
from nbtools.inspect import extract_source, extract_text_outputs, list_cells
from nbtools.io import read_notebook, write_notebook
from nbtools.types import CellSummary, CellType

__all__ = [
    "CellSummary",
    "CellType",
    "NotebookBuilder",
    "add_cell",
    "extract_source",
    "extract_text_outputs",
    "from_markdown",
    "from_python",
    "list_cells",
    "make_cell",
    "move_cell",
    "new_notebook",
    "read_notebook",
    "remove_cell",
    "to_html",
    "to_markdown",
    "to_python",
    "update_source",
    "write_notebook",
]
