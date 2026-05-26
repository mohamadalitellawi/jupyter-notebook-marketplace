"""Convert notebooks to and from other formats.

Forward (notebook -> text):

* ``to_python``  -- a runnable ``.py`` using the ``# %%`` cell-marker
  convention (readable by Jupyter, VS Code, and jupytext). Pure stdlib.
* ``to_markdown`` -- a ``.md`` document. Each cell is preceded by an invisible
  ``<!-- cell:TYPE -->`` HTML comment so the format round-trips losslessly;
  code cells are also shown as fenced blocks for readability. Pure stdlib.
* ``to_html``     -- a standalone HTML page. Markdown cells are rendered with
  the ``markdown`` library (stdlib has no markdown renderer); code cells are
  HTML-escaped and wrapped in ``<pre>``.

Reverse (text -> notebook):

* ``from_python``   -- parse a ``# %%``-delimited script back into cells.
  Tolerant of marker variants (``#%%``, ``# %%``, VS Code style). Pure stdlib.
* ``from_markdown`` -- parse a document produced by ``to_markdown`` back into
  cells using its ``<!-- cell:TYPE -->`` markers. Falls back to a best-effort
  fenced-block heuristic for hand-written Markdown with no markers. Pure stdlib.

Only ``to_html`` pulls in a third-party dependency, and only for the one job
stdlib cannot do.
"""

from __future__ import annotations

import html
import re

import markdown as markdown_lib
from nbformat import NotebookNode

from nbtools.create import make_cell, new_notebook
from nbtools.types import CellType

# Invisible cell-boundary marker emitted by ``to_markdown``. HTML comments are
# not rendered by Markdown viewers, so the document still reads cleanly while
# giving ``from_markdown`` an unambiguous delimiter that survives even when a
# Markdown cell's own body contains ``` fences.
_MD_CELL_MARKER = "<!-- cell:{cell_type} -->"
_MD_MARKER_RE = re.compile(r"^<!--\s*cell:(code|markdown|raw)\s*-->$")

# A ``# %%`` cell marker in a Python script. Tolerates optional space after the
# ``#``, and an optional ``[markdown]`` / ``[raw]`` tag. Matches ``# %%``,
# ``#%%``, ``# %% [markdown]``, ``#%%[raw]``, etc.
_PY_MARKER_RE = re.compile(r"^\s*#\s*%%(?P<tag>.*)$")


def to_python(notebook: NotebookNode) -> str:
    """Render the notebook as a ``# %%``-delimited Python script.

    Code cells are emitted verbatim under a ``# %%`` marker. Markdown and raw
    cells are emitted as commented blocks under ``# %% [markdown]`` / ``[raw]``
    so the script stays valid Python and round-trips back to cells.

    Args:
        notebook: The notebook to convert.

    Returns:
        The script as a single string.
    """
    blocks: list[str] = []
    for cell in notebook.cells:
        if cell.cell_type == CellType.CODE:
            blocks.append(f"# %%\n{cell.source}")
        else:
            tag = "markdown" if cell.cell_type == CellType.MARKDOWN else "raw"
            commented = "\n".join(f"# {line}" for line in cell.source.splitlines())
            blocks.append(f"# %% [{tag}]\n{commented}")
    return "\n\n".join(blocks) + "\n"


def to_markdown(notebook: NotebookNode) -> str:
    """Render the notebook as a Markdown document.

    Each cell is preceded by an invisible ``<!-- cell:TYPE -->`` marker. The
    marker is what ``from_markdown`` uses to recover cell boundaries, so a
    Markdown cell whose body itself contains ``` fences round-trips correctly.
    Markdown viewers do not render HTML comments, so the document still reads
    cleanly. Code cells are shown as fenced ``python`` blocks; raw cells as
    plain fenced blocks.

    Args:
        notebook: The notebook to convert.

    Returns:
        The Markdown document as a single string.
    """
    blocks: list[str] = []
    for cell in notebook.cells:
        marker = _MD_CELL_MARKER.format(cell_type=cell.cell_type)
        if cell.cell_type == CellType.MARKDOWN:
            body = cell.source
        elif cell.cell_type == CellType.CODE:
            body = f"```python\n{cell.source}\n```"
        else:
            body = f"```\n{cell.source}\n```"
        blocks.append(f"{marker}\n{body}")
    return "\n\n".join(blocks) + "\n"


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ max-width: 50rem; margin: 2rem auto; padding: 0 1rem;
        font-family: system-ui, sans-serif; line-height: 1.5; }}
pre {{ background: #f5f5f5; padding: 0.75rem; border-radius: 4px;
       overflow-x: auto; }}
code {{ font-family: ui-monospace, monospace; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def to_html(notebook: NotebookNode, title: str = "Notebook") -> str:
    """Render the notebook as a standalone HTML page.

    Markdown cells are converted to HTML via the ``markdown`` library with the
    fenced-code and tables extensions. Code cells are HTML-escaped and wrapped
    in ``<pre><code>`` so their contents are shown literally, never executed.

    Args:
        notebook: The notebook to convert.
        title: Page title used in ``<title>`` and document head.

    Returns:
        A complete HTML document as a single string.
    """
    parts: list[str] = []
    for cell in notebook.cells:
        if cell.cell_type == CellType.MARKDOWN:
            parts.append(
                markdown_lib.markdown(
                    cell.source, extensions=["fenced_code", "tables"]
                )
            )
        else:
            escaped = html.escape(cell.source)
            parts.append(f"<pre><code>{escaped}</code></pre>")
    body = "\n".join(parts)
    return _HTML_TEMPLATE.format(title=html.escape(title), body=body)


def _trim_blank_edges(lines: list[str]) -> list[str]:
    """Drop leading and trailing all-whitespace lines (cells are joined with a
    blank line, so each segment picks up padding that is not part of source)."""
    out = list(lines)
    while out and out[0].strip() == "":
        out.pop(0)
    while out and out[-1].strip() == "":
        out.pop()
    return out


def _uncomment(line: str) -> str:
    """Reverse the ``# `` prefix that ``to_python`` adds to markdown/raw lines.

    ``"# # Heading"`` -> ``"# Heading"``; ``"# "`` or ``"#"`` -> ``""``.
    """
    if line.startswith("# "):
        return line[2:]
    if line == "#":
        return ""
    return line


def from_python(text: str) -> NotebookNode:
    """Parse a ``# %%``-delimited Python script back into a notebook.

    Recognises ``# %%`` (code), ``# %% [markdown]``, and ``# %% [raw]`` cell
    markers, tolerating spacing variants (``#%%``) and VS Code style. Markdown
    and raw cell bodies are un-commented (the inverse of ``to_python``). Any
    content before the first marker becomes a leading code cell. A script with
    no markers at all becomes a single code cell.

    Args:
        text: The Python script source.

    Returns:
        A validated notebook reconstructed from the script.
    """
    notebook = new_notebook()
    segments: list[tuple[CellType, list[str]]] = []
    preamble: list[str] = []
    current: tuple[CellType, list[str]] | None = None

    for line in text.splitlines():
        match = _PY_MARKER_RE.match(line)
        if match:
            if current is not None:
                segments.append(current)
            elif any(token.strip() for token in preamble):
                segments.append((CellType.CODE, preamble))
            tag = match.group("tag").strip().lower()
            if "[markdown]" in tag:
                cell_type = CellType.MARKDOWN
            elif "[raw]" in tag:
                cell_type = CellType.RAW
            else:
                cell_type = CellType.CODE
            current = (cell_type, [])
        elif current is not None:
            current[1].append(line)
        else:
            preamble.append(line)

    if current is not None:
        segments.append(current)
    elif any(token.strip() for token in preamble):
        segments.append((CellType.CODE, preamble))

    for cell_type, raw_lines in segments:
        body_lines = _trim_blank_edges(raw_lines)
        if cell_type in (CellType.MARKDOWN, CellType.RAW):
            source = "\n".join(_uncomment(line) for line in body_lines)
        else:
            source = "\n".join(body_lines)
        notebook.cells.append(make_cell(cell_type, source))
    return notebook


def _strip_fence(body: str) -> str:
    """Remove an opening ```` ``` ```` line and its closing fence from a block."""
    lines = body.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)


def _from_markdown_with_markers(text: str) -> NotebookNode:
    """Parse Markdown produced by ``to_markdown`` using its cell markers."""
    notebook = new_notebook()
    segments: list[tuple[CellType, list[str]]] = []
    current: tuple[CellType, list[str]] | None = None

    for line in text.splitlines():
        match = _MD_MARKER_RE.match(line.strip())
        if match:
            if current is not None:
                segments.append(current)
            current = (CellType(match.group(1)), [])
        elif current is not None:
            current[1].append(line)
    if current is not None:
        segments.append(current)

    for cell_type, raw_lines in segments:
        body = "\n".join(_trim_blank_edges(raw_lines))
        source = body if cell_type == CellType.MARKDOWN else _strip_fence(body)
        notebook.cells.append(make_cell(cell_type, source))
    return notebook


_FENCE_OPEN_RE = re.compile(r"^```(?P<lang>\w*)\s*$")


def _from_markdown_heuristic(text: str) -> NotebookNode:
    """Best-effort parse of hand-written Markdown that lacks cell markers.

    Fenced ``python`` blocks become code cells, bare fenced blocks become raw
    cells, and the prose between them becomes markdown cells. This cannot be
    lossless -- a fence inside prose is indistinguishable from a real code
    block -- which is exactly why ``to_markdown`` emits explicit markers.
    """
    notebook = new_notebook()
    lines = text.splitlines()
    prose: list[str] = []

    def flush_prose() -> None:
        source = "\n".join(_trim_blank_edges(prose))
        if source.strip():
            notebook.cells.append(make_cell(CellType.MARKDOWN, source))
        prose.clear()

    index = 0
    while index < len(lines):
        fence = _FENCE_OPEN_RE.match(lines[index])
        if fence:
            flush_prose()
            index += 1
            body: list[str] = []
            while index < len(lines) and not lines[index].startswith("```"):
                body.append(lines[index])
                index += 1
            index += 1  # skip the closing fence
            cell_type = CellType.RAW if fence.group("lang") == "" else CellType.CODE
            notebook.cells.append(make_cell(cell_type, "\n".join(body)))
        else:
            prose.append(lines[index])
            index += 1
    flush_prose()
    return notebook


def from_markdown(text: str) -> NotebookNode:
    """Parse a Markdown document back into a notebook.

    If the document carries ``<!-- cell:TYPE -->`` markers (as produced by
    ``to_markdown``), they are used for an exact, lossless reconstruction --
    including Markdown cells whose bodies contain ``` fences. Otherwise this
    falls back to a best-effort heuristic that treats fenced blocks as code and
    the text between them as Markdown.

    Args:
        text: The Markdown document source.

    Returns:
        A validated notebook reconstructed from the document.
    """
    if any(_MD_MARKER_RE.match(line.strip()) for line in text.splitlines()):
        return _from_markdown_with_markers(text)
    return _from_markdown_heuristic(text)
