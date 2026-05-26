"""Inspect notebooks without modifying them.

These helpers answer "what is in this notebook?" questions. They never mutate
the notebook they are given; they return new strings, lists, or read-only
``CellSummary`` views.
"""

from __future__ import annotations

from nbformat import NotebookNode

from nbtools.types import CellSummary, CellType


def list_cells(notebook: NotebookNode) -> list[CellSummary]:
    """Summarise every cell in order.

    Args:
        notebook: The notebook to inspect.

    Returns:
        One ``CellSummary`` per cell, in notebook order.
    """
    summaries: list[CellSummary] = []
    for index, cell in enumerate(notebook.cells):
        outputs = cell.get("outputs", [])
        summaries.append(
            CellSummary(
                index=index,
                cell_type=CellType(cell.cell_type),
                source=cell.source,
                execution_count=cell.get("execution_count"),
                output_count=len(outputs),
            )
        )
    return summaries


def extract_source(
    notebook: NotebookNode, cell_type: CellType | None = None
) -> list[str]:
    """Pull the source text of cells, optionally filtered by kind.

    Args:
        notebook: The notebook to read.
        cell_type: If given, only return sources of cells of this kind;
            if ``None``, return every cell's source.

    Returns:
        The source strings, in notebook order.
    """
    return [
        cell.source
        for cell in notebook.cells
        if cell_type is None or cell.cell_type == cell_type
    ]


def extract_text_outputs(notebook: NotebookNode) -> list[str]:
    """Collect plain-text outputs from all code cells.

    Handles the three text-bearing output kinds in the nbformat schema:
    ``stream`` (stdout/stderr), ``execute_result`` and ``display_data`` (which
    carry a ``text/plain`` representation). Image and other rich outputs are
    skipped, since this returns text only.

    Args:
        notebook: The notebook to read.

    Returns:
        One string per text output found, in notebook order.
    """
    texts: list[str] = []
    for cell in notebook.cells:
        if cell.cell_type != CellType.CODE:
            continue
        for output in cell.get("outputs", []):
            output_type = output.get("output_type")
            if output_type == "stream":
                texts.append(output.get("text", ""))
            elif output_type in ("execute_result", "display_data"):
                plain = output.get("data", {}).get("text/plain")
                if plain is not None:
                    texts.append(plain)
    return texts
