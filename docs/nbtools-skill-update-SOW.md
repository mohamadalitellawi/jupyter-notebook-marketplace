# Scope of Work — `jupyter-notebook` (nbtools) skill update

> **For:** the skill maintainer, to hand to Claude Code running inside the skill's repo.
> **Package:** `nbtools` (a thin, schema-validated wrapper over `nbformat`).
> **Repo layout (paths below are relative to the skill package root):**
> `nbtools/` (the package), `tests/test_nbtools.py`, `SKILL.md`, `pyproject.toml`.

---

## 1. Context & motivation

`nbtools` is the engine behind the `jupyter-notebook` skill: it reads, creates, edits,
inspects, and converts `.ipynb` files, validating every notebook against the nbformat
schema on the way in and out. It is deliberately scoped to **not execute** notebooks (no
kernel).

This SOW comes from real usage: an agent used the skill to author a multi-cell teaching
notebook and then verify it. The skill did the authoring well, but four friction points
showed up that this work item addresses. None require breaking changes; all are additive or
internal.

**Design principles to preserve (do not violate):**

- Every notebook entering/leaving goes through `io.py`, the single place validation and the
  overwrite guard live. Keep it that way.
- Edit/transform functions are **pure**: deep-copy input, return a new notebook, never
  mutate (see `edit.py`). Any new transform must follow this.
- Inspect functions are read-only and return plain values / frozen dataclasses.
- Pure-stdlib where possible; a third-party dep is added **only** for a job stdlib can't do
  (today that's `markdown`, used solely by `to_html`).

---

## 2. Goals (prioritized)

| # | Item | Priority | Type |
|---|------|----------|------|
| A | `read_notebook` accepts `str` as well as `Path` | P0 | bugfix/ergonomics |
| B | `extract_text_outputs` no longer silently drops error tracebacks; add `extract_errors` | P0 | bugfix |
| C | Add pure `clear_outputs` transform | P0 | feature |
| D | SKILL.md: document `NotebookBuilder(metadata=...)` + add a "verify it runs" section | P0 | docs |
| E | Optional `execute_notebook` via `nbclient` behind an extra | P1 | feature |
| F | Add `set_cell_metadata` pure transform (cell tags) | P1 | feature |

Ship A–D together (low risk, high value). E–F can follow in the same PR or a second one.

---

## 3. Work items

### A. `read_notebook` should accept `str | Path` (P0)

**Problem.** `read_notebook(path)` calls `path.exists()` directly (`nbtools/io.py:34`). Passing
a string — the natural thing in a quick script — raises
`AttributeError: 'str' object has no attribute 'exists'` instead of working or giving a clear
error. This was hit in real use.

**Change.** Coerce at the top of `read_notebook`:

```python
def read_notebook(path: str | Path) -> NotebookNode:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No notebook at: {path}")
    ...
```

Do the same coercion in `write_notebook` (`path: str | Path`, `path = Path(path)` first line)
for symmetry.

**Files.** `nbtools/io.py`.

**Tests.** Add to `tests/test_nbtools.py`: round-trip a notebook passing **string** paths to
both `write_notebook` and `read_notebook`; assert equality of cell sources. Keep the existing
`Path` tests.

**Acceptance.** `read_notebook("some.ipynb")` and `write_notebook(nb, "some.ipynb")` work with
strings; type hints updated; docstrings mention `str | Path`.

---

### B. Stop silently dropping error outputs; add `extract_errors` (P0)

**Problem.** `extract_text_outputs` (`nbtools/inspect.py:59-85`) handles `stream`,
`execute_result`, and `display_data` but **ignores `error` outputs entirely**. An executed
notebook that raised an exception therefore looks output-empty to this helper — a real
footgun when the helper is used to verify a notebook ran cleanly. (In real use the agent had
to hand-roll a scan for `output_type == "error"`.)

**Change (two parts):**

1. Add a new read-only helper `extract_errors(notebook) -> list[CellError]`, where `CellError`
   is a frozen dataclass in `types.py`:

   ```python
   @dataclass(frozen=True, slots=True)
   class CellError:
       index: int          # zero-based cell index
       ename: str          # exception name, e.g. "ValueError"
       evalue: str         # exception message
       traceback: list[str]  # raw traceback lines from the output
   ```

   Implementation walks code cells, collects outputs where
   `output.get("output_type") == "error"`.

2. Give `extract_text_outputs` an opt-in flag to include error text without changing the
   default behavior (avoid surprising existing callers):

   ```python
   def extract_text_outputs(notebook, *, include_errors: bool = False) -> list[str]:
       ...
       elif output_type == "error" and include_errors:
           texts.append("\n".join(output.get("traceback", [])))
   ```

**Files.** `nbtools/inspect.py`, `nbtools/types.py`, export `CellError` + `extract_errors`
from `nbtools/__init__.py` (`__all__` too).

**Tests.** Build a notebook, attach a synthetic `error` output to a code cell
(`output_type="error"`, `ename`, `evalue`, `traceback`), assert `extract_errors` returns one
`CellError` with the right `index`/`ename`; assert `extract_text_outputs` excludes it by
default and includes it when `include_errors=True`.

**Acceptance.** A caller can detect "did any cell error?" with `extract_errors(nb)` in one
line.

---

### C. Add a pure `clear_outputs` transform (P0)

**Problem.** A very common need is shipping a notebook **without** executed outputs (clean
diffs, no embedded local paths/timestamps, "ships without outputs" templates). Today you must
rebuild the notebook from scratch or hand-edit JSON. There's no helper.

**Change.** Add to `nbtools/edit.py` (pure, deep-copy like its neighbors):

```python
def clear_outputs(notebook: NotebookNode) -> NotebookNode:
    """Return a copy with all code-cell outputs and execution_counts cleared."""
    result = copy.deepcopy(notebook)
    for cell in result.cells:
        if cell.cell_type == CellType.CODE:
            cell["outputs"] = []
            cell["execution_count"] = None
    return result
```

**Files.** `nbtools/edit.py`; export from `nbtools/__init__.py` + `__all__`.

**Tests.** Take a notebook with a code cell that has outputs + a non-None `execution_count`;
assert `clear_outputs` returns a copy with empty `outputs` and `execution_count is None`, and
that the **original is unmodified** (purity, matching the existing edit-purity tests).

**Acceptance.** `write_notebook(clear_outputs(nb), path)` yields an output-free notebook.

---

### D. SKILL.md documentation fixes (P0)

**Problem.** The "Create" section of `SKILL.md` shows `NotebookBuilder().add_markdown(...)`
but never mentions that the constructor takes `metadata=` (it does — `create.py:73`,
`new_notebook(metadata=...)`). In real use the agent missed this and set `nb["metadata"]`
manually to get kernelspec/`language_info`. There's also no guidance on the
create→**verify** loop, which is the skill's biggest gap.

**Changes to `SKILL.md`:**

1. In **Create**, add a worked example that seeds kernel metadata via the builder:

   ```python
   nb = NotebookBuilder(metadata={
       "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
       "language_info": {"name": "python", "pygments_lexer": "ipython3"},
   }).add_markdown("# Title").add_code("x = 1").build()
   ```

2. Add a new short section **"Verifying a notebook runs"** stating plainly that this skill
   does **not** execute notebooks, and giving the supported verification path:
   - If item E ships: `from nbtools import execute_notebook; nb = execute_notebook(nb)` then
     `extract_errors(nb)`.
   - Always-available fallback (no kernel dependency in nbtools):
     `jupyter nbconvert --to notebook --execute --inplace path.ipynb`, then
     `read_notebook` + `extract_errors` to confirm zero errors.

3. Document `clear_outputs` (item C) and `extract_errors` (item B) in the Edit/Inspect
   sections.

**Files.** `SKILL.md` only.

**Acceptance.** A reader can (1) set kernel metadata without touching raw JSON, (2) know
exactly how to prove a notebook executes, and (3) know how to strip outputs before shipping.

---

### E. Optional `execute_notebook` via `nbclient` (P1)

**Problem.** The skill covers create/edit but not the verify half of the loop, so users shell
out to `jupyter nbconvert` by hand. Closing this in-process makes the skill end-to-end while
keeping execution **opt-in** (heavy deps stay optional).

**Change.** New module `nbtools/execute.py`:

```python
def execute_notebook(
    notebook: NotebookNode,
    *,
    timeout: int = 60,
    kernel_name: str | None = None,
    allow_errors: bool = False,
) -> NotebookNode:
    """Run every code cell and return a NEW notebook with outputs populated.

    Pure (deep-copies input). Requires the optional 'execute' extra
    (nbclient + ipykernel); raises a clear ImportError with install hint if absent.
    """
```

- Implement with `nbclient.NotebookClient`. Import `nbclient` **lazily inside the function**;
  if missing, raise `ImportError("Install the execute extra: pip install nbtools[execute]")`.
- Deep-copy input, execute the copy, return it (purity — never mutate caller's notebook).
- `allow_errors=False` (default) should surface a failing cell as an exception; document
  pairing with `extract_errors` when `allow_errors=True`.

**pyproject.toml.** Add an optional extra:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
execute = ["nbclient>=0.9", "ipykernel>=6"]
```

**Files.** `nbtools/execute.py`, `nbtools/__init__.py` (+ `__all__`), `pyproject.toml`.

**Tests.** Mark with `pytest.importorskip("nbclient")` so the suite still passes without the
extra. Execute a notebook whose cell sets `x = 2 + 2; print(x)`; assert an output containing
`4` via `extract_text_outputs`. Add a negative test: a raising cell with `allow_errors=True`
produces an `error` output that `extract_errors` finds.

**Acceptance.** With the extra installed, `execute_notebook` runs a notebook in-process; the
suite skips cleanly without it; SKILL.md (item D.2) references it.

---

### F. `set_cell_metadata` pure transform (P1)

**Problem.** Notebook-print pipelines (nbconvert / Quarto) rely on **cell tags** (e.g.
`"remove-input"`, `"hide-cell"`). There's no way to set them with nbtools today.

**Change.** Add to `nbtools/edit.py` (pure):

```python
def set_cell_metadata(notebook, index, metadata: dict, *, merge: bool = True) -> NotebookNode:
    """Return a copy with cell metadata updated (merged by default, else replaced)."""
```

Validate `index` with the existing `_validate_index(..., for_insert=False)`.

**Files.** `nbtools/edit.py`; export + `__all__`.

**Tests.** Set a `tags` list on a cell; assert merge vs. replace semantics; assert purity.

---

## 4. Non-goals

- No change to the converter round-trip semantics or the documented delimiter-collision
  limitations.
- No new always-on dependencies (execution deps stay behind the `execute` extra).
- Don't change default behavior of `extract_text_outputs` (item B keeps the default; errors
  are opt-in).
- Don't alter the overwrite guard or move validation out of `io.py`.

---

## 5. Definition of done

- [ ] All new public functions exported in `nbtools/__init__.py` and listed in `__all__`.
- [ ] Full type hints and docstrings matching the existing house style (Args/Returns/Raises).
- [ ] `pytest` green. The current suite has 23 tests — keep them all passing and add the new
      ones described above; execution tests must `importorskip` so they skip without the extra.
- [ ] `SKILL.md` updated for items B, C, D (and E if shipped).
- [ ] Version bumped in `pyproject.toml`; add/update a CHANGELOG entry if the repo keeps one.
- [ ] No mutation of caller-provided notebooks in any new transform (purity verified by test).

## 6. How to verify locally

```bash
# from the skill package root (where pyproject.toml lives)
uv sync                      # or: pip install -e ".[dev]"
uv run pytest                # full suite, must be green
uv run pytest -q -k execute  # if item E shipped and extra installed
# Optional manual smoke test of the create->verify loop:
uv run --extra execute python - <<'PY'
from nbtools import NotebookBuilder, execute_notebook, extract_errors
nb = NotebookBuilder().add_code("print(2+2)").build()
nb = execute_notebook(nb)
assert not extract_errors(nb)
print("ok")
PY
```

---

## 7. How to feed this to Claude Code on the maintainer's laptop

1. **Get the file onto the laptop** alongside the skill repo. Easiest: copy this
   `nbtools-skill-update-SOW.md` into the skill repo root (it does not need to be committed).

2. **Open a terminal in the skill repo root** (the directory containing `nbtools/`,
   `SKILL.md`, `pyproject.toml`) so all the relative paths above resolve.

3. **Recommended — interactive, with a plan-review checkpoint:**
   ```bash
   claude
   ```
   Then, at the prompt, press **Shift+Tab** to enter *plan mode* (so it proposes before
   editing) and send:
   > Read `nbtools-skill-update-SOW.md` in this repo and implement it. Start with items A–D
   > (P0). Work item by item: make the change, add the tests it specifies, and run `uv run
   > pytest` after each item before moving on. Show me a plan first.

   Review the plan, approve, and let it execute. It will run the tests itself per item.

4. **Alternative — headless / one-shot** (no interactive review):
   ```bash
   claude -p "Read nbtools-skill-update-SOW.md and implement items A through D, adding the specified tests and running 'uv run pytest' after each. Then summarize the diff."
   ```
   Add `--permission-mode acceptEdits` if you want it to apply file edits without prompting
   (it will still ask before anything riskier). Omit it to approve edits as they happen.

5. **Scope control.** To stage the work, tell it explicitly: *"Only do items A–D in this PR;
   leave E and F for a follow-up."* To do everything: *"Implement all items A–F."*

6. **Before committing**, ask it: *"Run `uv run pytest` once more and show `git diff --stat`."*
   Then commit/PR yourself (don't have it push unless you intend to).

> Tip: this SOW is self-contained and cites exact files and line numbers, so the agent
> shouldn't need extra context. If it asks where the package root is, point it at the folder
> holding `pyproject.toml`.
