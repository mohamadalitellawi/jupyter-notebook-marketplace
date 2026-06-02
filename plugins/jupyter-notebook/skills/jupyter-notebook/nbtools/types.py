"""Shared types for the nbtools package.

An ``.ipynb`` file is JSON conforming to the Jupyter *nbformat* schema. We use
``nbformat`` rather than parsing the JSON by hand so that the schema, version
migration, and round-tripping are handled by the library Jupyter itself uses.

This module defines the small vocabulary the rest of the package speaks in:
the three legal cell kinds and a couple of lightweight, read-only views used
when inspecting a notebook.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CellType(StrEnum):
    """The three cell kinds defined by the nbformat schema.

    ``StrEnum`` means each member *is* its string value, so ``CellType.CODE``
    compares equal to ``"code"`` and serialises straight into the notebook
    without conversion.
    """

    CODE = "code"
    MARKDOWN = "markdown"
    RAW = "raw"


@dataclass(frozen=True, slots=True)
class CellSummary:
    """A read-only snapshot of one cell, returned by inspection helpers.

    Attributes:
        index: Zero-based position of the cell in the notebook.
        cell_type: The kind of cell (code/markdown/raw).
        source: The full source text of the cell.
        execution_count: Execution number for code cells, ``None`` otherwise
            or if the code cell has not been run.
        output_count: Number of output objects attached to the cell (always 0
            for non-code cells).
    """

    index: int
    cell_type: CellType
    source: str
    execution_count: int | None
    output_count: int


@dataclass(frozen=True, slots=True)
class CellError:
    """A read-only view of one ``error`` output captured by a code cell.

    Returned by :func:`nbtools.inspect.extract_errors`. Lets a caller answer
    "did any cell raise?" without hand-scanning raw output dicts.

    Attributes:
        index: Zero-based position of the cell that produced the error.
        ename: Exception class name, e.g. ``"ValueError"``.
        evalue: Exception message text.
        traceback: Raw traceback lines exactly as stored in the output.
    """

    index: int
    ename: str
    evalue: str
    traceback: list[str]
