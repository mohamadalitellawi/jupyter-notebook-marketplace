"""Read and write ``.ipynb`` files, always validated against the schema.

Every notebook that enters or leaves the program passes through here, so this
is the single place where validation and the overwrite guard live. Keeping it
in one module means the rest of the package can assume any notebook object it
holds is already schema-valid.
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat import NotebookNode

# nbformat major version we read/write. v4 is the current, long-stable format
# used by every modern Jupyter install.
NBFORMAT_VERSION = 4


def read_notebook(path: Path) -> NotebookNode:
    """Read and validate a notebook from disk.

    Args:
        path: Path to an existing ``.ipynb`` file.

    Returns:
        The parsed notebook as an ``nbformat`` ``NotebookNode``.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        nbformat.ValidationError: If the file is not a valid notebook.
    """
    if not path.exists():
        raise FileNotFoundError(f"No notebook at: {path}")
    notebook = nbformat.read(path, as_version=NBFORMAT_VERSION)
    nbformat.validate(notebook)
    return notebook


def write_notebook(
    notebook: NotebookNode, path: Path, *, overwrite: bool = False
) -> Path:
    """Validate a notebook and write it to disk.

    Writing over an existing file is destructive, so it must be requested
    explicitly via ``overwrite=True``; otherwise an existing target raises.

    Args:
        notebook: The notebook to write.
        path: Destination ``.ipynb`` path.
        overwrite: Must be ``True`` to replace an existing file.

    Returns:
        The path written to.

    Raises:
        FileExistsError: If ``path`` exists and ``overwrite`` is ``False``.
        nbformat.ValidationError: If the notebook is not schema-valid.
    """
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing file without overwrite=True: {path}"
        )
    nbformat.validate(notebook)
    path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, path)
    return path
