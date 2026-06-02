# jupyter-notebook skill (`nbtools`)

Read, inspect, edit, create, and convert Jupyter `.ipynb` files from Python.
Built on the official [`nbformat`](https://nbformat.readthedocs.io/) library,
so every notebook is validated against the Jupyter schema on read and write.

**By default this package does not execute notebooks** — the core has no kernel
dependency; it manipulates the notebook *file structure*. In-process execution
is available **opt-in** via the `execute` extra (see below). Without it, run
notebooks yourself in Jupyter/Colab or via `jupyter nbconvert`.

## Install

Requires Python ≥ 3.12.

```bash
uv sync                      # from this folder, using pyproject.toml
# or
pip install nbformat markdown
```

`markdown` is only used by the HTML converter. The `.py` and `.md` converters
are pure standard library.

Execution is optional and pulls in a kernel, so it lives behind the `execute`
extra (`nbclient` + `ipykernel`):

```bash
uv sync --extra execute      # or: pip install nbtools[execute]
```

## Layout

```
jupyter-notebook/
├── SKILL.md            # instructions Claude loads when the skill triggers
├── README.md           # this file
├── pyproject.toml      # deps, python>=3.12
├── nbtools/
│   ├── __init__.py     # public API re-exports
│   ├── types.py        # CellType, CellSummary, CellError
│   ├── io.py           # read_notebook / write_notebook (validated, guarded)
│   ├── inspect.py      # list_cells, extract_source, extract_text_outputs, extract_errors
│   ├── edit.py         # add / remove / move / update_source / clear_outputs / set_cell_metadata (all pure)
│   ├── create.py       # new_notebook, NotebookBuilder
│   ├── convert.py      # to_python/markdown/html + from_python/from_markdown
│   └── execute.py      # execute_notebook (optional, needs the 'execute' extra)
└── tests/
    └── test_nbtools.py # pytest suite (round-trips, guard, edits, converters, errors, execution)
```

## Quick start

```python
from pathlib import Path
from nbtools import NotebookBuilder, write_notebook, read_notebook, add_cell, to_python
from nbtools.types import CellType

# Build from scratch
nb = (
    NotebookBuilder()
    .add_markdown("# Title")
    .add_code("x = 1")
    .build()
)

# Write (validated; won't overwrite without overwrite=True)
write_notebook(nb, Path("demo.ipynb"))

# Read back, edit (returns a new notebook — original untouched)
nb = read_notebook(Path("demo.ipynb"))
nb = add_cell(nb, CellType.CODE, "print(x)")

# Convert to a runnable script
Path("demo.py").write_text(to_python(nb))
```

## Design notes

- **Pure edits.** `add_cell`, `remove_cell`, `move_cell`, `update_source`,
  `clear_outputs`, and `set_cell_metadata` deep-copy the input and return a new
  notebook. No hidden mutation. `execute_notebook` (optional) is pure too.
- **Verify, don't guess.** `extract_errors(nb)` returns one `CellError` per
  `error` output, so `assert not extract_errors(nb)` confirms a notebook ran
  clean. With the `execute` extra, `execute_notebook(nb)` runs it in-process;
  otherwise use `jupyter nbconvert --execute` then re-read and check.
- **Ship clean.** `clear_outputs(nb)` strips code-cell outputs and execution
  counts for tidy diffs; `set_cell_metadata` sets cell tags (e.g.
  `remove-input`) that nbconvert / Quarto act on.
- **Destructive writes are explicit.** `write_notebook` raises `FileExistsError`
  on an existing path unless you pass `overwrite=True`.
- **Lossless round-trips.** For normal content, `from_python(to_python(nb))`
  and `from_markdown(to_markdown(nb))` reproduce cell kinds and sources exactly.
  The Markdown format uses invisible `<!-- cell:TYPE -->` comments as cell
  delimiters, so a markdown cell containing a ```` ```python ```` example
  round-trips as one cell rather than being split on the inner fence. For
  hand-written `.md` without those markers, `from_markdown` falls back to a
  best-effort fenced-block heuristic.
- **Units convention.** When you create code cells, carry units in names
  (`span_mm`, `stress_MPa`) as usual — the package treats source as opaque text
  and won't mangle it.

## Limitations

The text formats can't represent content that collides with their own cell
delimiters. These are properties of the formats (the same class of limit
jupytext has), not defects — the `.ipynb` is the source of truth, so keep it
canonical and use the converters for export/import.

- A code cell whose source contains a line that is exactly `# %%` splits into
  two cells on `from_python`. The marker is indistinguishable from that comment,
  and escaping it would break Jupyter / VS Code compatibility.
- A markdown cell whose body contains a line exactly equal to a marker
  (`<!-- cell:code -->`, etc.) splits on `from_markdown`. Ordinary fenced code
  inside a markdown cell is safe — only the literal marker line collides.
- Empty input (`from_python("")`, `from_markdown("")`) yields a notebook with
  no cells. It is valid and writable.

Each of these is pinned by a test so the behaviour can't change silently.

## Reverse conversion

```python
from pathlib import Path
from nbtools import from_python, from_markdown, write_notebook

# .py (# %% cells) -> notebook
nb = from_python(Path("script.py").read_text())
write_notebook(nb, Path("script.ipynb"))

# .md -> notebook (lossless if produced by to_markdown; heuristic otherwise)
nb = from_markdown(Path("notes.md").read_text())
write_notebook(nb, Path("notes.ipynb"))
```

## Run the tests

```bash
pip install pytest                          # or: uv sync --extra dev
pytest                                      # 31 tests; 2 execution tests skip
uv run --extra dev --extra execute pytest   # 33 tests (runs the execution tests too)
```

## Install as a Claude skill

Drop the `jupyter-notebook/` folder into `~/.claude/skills/` (or a project's
`.claude/skills/`), or upload it via the Claude.ai skills UI. The skill triggers
on mentions of Jupyter notebooks, `.ipynb` files, notebook cells, or
notebook→script/Markdown/HTML conversion.
