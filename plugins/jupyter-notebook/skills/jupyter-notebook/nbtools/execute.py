"""Execute notebooks in-process (optional).

This is the only module in nbtools that *runs* code. It closes the
create/edit -> verify loop without shelling out to ``jupyter nbconvert``, but it
is deliberately opt-in: a kernel is heavy, so the dependencies live behind the
``execute`` extra (``pip install nbtools[execute]``) and ``nbclient`` is
imported lazily inside the function, not at module load.

Like the transforms in :mod:`nbtools.edit`, execution is pure: the input
notebook is deep-copied and the copy is run, so the caller's notebook is never
mutated.
"""

from __future__ import annotations

import copy

from nbformat import NotebookNode

_INSTALL_HINT = "Install the execute extra: pip install nbtools[execute]"


def execute_notebook(
    notebook: NotebookNode,
    *,
    timeout: int = 60,
    kernel_name: str | None = None,
    allow_errors: bool = False,
) -> NotebookNode:
    """Run every code cell and return a NEW notebook with outputs populated.

    Pure: the input is deep-copied and the copy is executed, so the notebook the
    caller passed in is never mutated.

    Requires the optional ``execute`` extra (``nbclient`` + ``ipykernel``). If
    those are not installed, raises ``ImportError`` with an install hint rather
    than failing obscurely.

    Args:
        notebook: The notebook to execute (not modified).
        timeout: Per-cell execution timeout in seconds.
        kernel_name: Kernel to run with. ``None`` (default) lets nbclient use
            the notebook's ``kernelspec`` metadata, falling back to the default
            Python kernel.
        allow_errors: If ``False`` (default), a cell that raises aborts
            execution and the exception propagates. If ``True``, execution
            continues past failures and the error is recorded as an ``error``
            output instead; pair with :func:`nbtools.inspect.extract_errors` to
            find which cells failed.

    Returns:
        A new ``NotebookNode`` with code-cell outputs and execution counts
        populated.

    Raises:
        ImportError: If the ``execute`` extra is not installed.
        nbclient.exceptions.CellExecutionError: If a cell raises and
            ``allow_errors`` is ``False``.
    """
    try:
        from nbclient import NotebookClient
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(_INSTALL_HINT) from exc

    result = copy.deepcopy(notebook)
    client = NotebookClient(
        result,
        timeout=timeout,
        kernel_name=kernel_name or "",
        allow_errors=allow_errors,
    )
    client.execute()
    return result
