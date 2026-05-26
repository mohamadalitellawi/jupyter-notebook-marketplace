---
name: jupyter-notebook
description: Read, inspect, edit, create, and convert Jupyter notebook (.ipynb) files using the nbtools Python package. Use this skill whenever the user mentions a Jupyter notebook, an .ipynb file, "notebook cells", or asks to extract code/markdown/outputs from a notebook, add/remove/reorder cells, build a notebook from scratch, or convert a notebook to a Python script, Markdown, or HTML — even if they don't say "Jupyter" explicitly. Does NOT execute notebooks; it manipulates the file structure only.
---

# Jupyter Notebook (nbtools)

This skill manipulates `.ipynb` files through the bundled `nbtools` Python
package. An `.ipynb` is JSON conforming to the Jupyter *nbformat* schema; the
package is built on the official `nbformat` library so every notebook read or
written is validated against that schema.

**Scope:** read/inspect, edit, create, and convert. This skill does **not**
execute notebooks — there is no kernel. If the user wants real cell outputs,
tell them to run the notebook themselves in Jupyter or Colab.

## Setup

Dependencies are `nbformat` and `markdown` (the latter only for HTML output).

```bash
cd <skill-dir> && uv sync        # or: pip install nbformat markdown
```

Import the package and call functions directly. The full public API is
re-exported from `nbtools`:

```python
from pathlib import Path
from nbtools import read_notebook, write_notebook, NotebookBuilder
from nbtools.types import CellType
```

## Core rules

- **Paths come from the user or CLI.** Wrap them in `pathlib.Path`. Never
  hardcode a path.
- **Writing is validated and guarded.** `write_notebook` validates against the
  schema and refuses to clobber an existing file unless `overwrite=True` is
  passed. Before overwriting any existing notebook, confirm with the user.
- **Edits are pure.** `add_cell`, `remove_cell`, `move_cell`, and
  `update_source` return a *new* notebook and never mutate the input. Chain
  them or reassign the result; the original is unchanged.
- **Indices are zero-based** and validated — an out-of-range index raises
  `IndexError` rather than failing silently.

## Operations

### Read & inspect (`nbtools.inspect`)
- `read_notebook(path)` → validated notebook.
- `list_cells(nb)` → list of `CellSummary(index, cell_type, source,
  execution_count, output_count)`.
- `extract_source(nb, cell_type=None)` → source strings, optionally filtered to
  one `CellType`.
- `extract_text_outputs(nb)` → plain-text outputs (stream, execute_result,
  display_data) from code cells. Image/rich outputs are skipped.

### Create (`nbtools.create`)
- `new_notebook(metadata=None)` → empty valid notebook.
- `NotebookBuilder().add_markdown(...).add_code(...).add_raw(...).build()` →
  assemble cell by cell; each `add_*` returns `self` so calls chain.

### Edit (`nbtools.edit`)
- `add_cell(nb, cell_type, source, index=None)` — `index=None` appends.
- `remove_cell(nb, index)`
- `move_cell(nb, from_index, to_index)` — `to_index` is read against the
  notebook *after* the cell is lifted out ("drag to slot N").
- `update_source(nb, index, source)` — replaces text, preserves cell kind.

### Convert (`nbtools.convert`)

Forward (notebook → string):
- `to_python(nb)` → `.py` using `# %%` cell markers (Jupyter / VS Code /
  jupytext compatible). Markdown and raw cells become commented blocks so the
  script stays valid Python.
- `to_markdown(nb)` → `.md`. Each cell is preceded by an invisible
  `<!-- cell:TYPE -->` marker (not rendered by Markdown viewers) so the format
  round-trips losslessly; code cells are also shown as fenced ```python blocks.
- `to_html(nb, title=...)` → standalone HTML page. Markdown cells are rendered;
  code cells are HTML-escaped and shown literally (never executed).

Reverse (string → notebook):
- `from_python(text)` → notebook. Recognises `# %%` / `# %% [markdown]` /
  `# %% [raw]`, tolerating spacing variants (`#%%`) and VS Code style. Content
  before the first marker, or a script with no markers, becomes a code cell.
- `from_markdown(text)` → notebook. Uses `<!-- cell:TYPE -->` markers for an
  exact reconstruction when present (including markdown cells whose body
  contains ``` fences). For hand-written Markdown without markers, falls back to
  a best-effort heuristic: fenced blocks → code, prose between → markdown.

All converters take/return strings. Read and write with normal file I/O:
`nb = from_python(Path("script.py").read_text())`;
`Path("out.py").write_text(to_python(nb))`.

Round-trip guarantee: for normal content, `from_python(to_python(nb))` and
`from_markdown(to_markdown(nb))` reproduce cell kinds and sources exactly. See
**Limitations** below for the delimiter-collision edge cases where this does not
hold.

## Worked example

```python
from pathlib import Path
from nbtools import NotebookBuilder, write_notebook, add_cell, to_markdown
from nbtools.types import CellType

nb = (
    NotebookBuilder()
    .add_markdown("# Analysis")
    .add_code("import numpy as np")
    .build()
)
nb = add_cell(nb, CellType.CODE, "print(np.pi)")          # pure: returns new nb
write_notebook(nb, Path("analysis.ipynb"))                 # validated, no clobber
Path("analysis.md").write_text(to_markdown(nb))            # export to Markdown
```

## Limitations

The text formats (`.py`, `.md`) cannot represent cell content that collides
with their own cell delimiters. These are inherent to the formats, not bugs;
the `.ipynb` file is the source of truth, so keep it as the canonical store and
treat the converters as export/import when content might contain a delimiter.

- **`from_python`**: a code cell whose source contains a line that is exactly a
  cell marker (e.g. a literal `# %%` comment) is split into two cells on the
  reverse trip. The marker is textually indistinguishable from that comment;
  escaping it would break compatibility with Jupyter / VS Code, which is the
  point of the `# %%` convention.
- **`from_markdown`**: a markdown cell whose body contains a line exactly equal
  to a marker (`<!-- cell:code -->`, etc.) is likewise split. Ordinary fenced
  code inside a markdown cell is safe — only the literal marker line collides.
- **Empty input**: `from_python("")` and `from_markdown("")` return a notebook
  with no cells (a valid, writable notebook).

## Verifying changes

The package ships with a pytest suite (`tests/test_nbtools.py`) covering
round-trips, the overwrite guard, edit purity, each converter, and the
limitations above (pinned as known behaviour). Run `pytest` after any
modification to the package.
