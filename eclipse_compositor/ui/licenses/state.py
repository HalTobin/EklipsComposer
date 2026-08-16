"""Immutable UI state for the Licenses dialog (MVI)."""

from __future__ import annotations

from dataclasses import dataclass

from eclipse_compositor.ui.licenses.models import Dependency


@dataclass(frozen=True)
class LicensesState:
    """Complete snapshot of the Licenses dialog UI.

    The view renders exclusively from this object; never mutate in place —
    use ``dataclasses.replace``.
    """

    dependencies: tuple[Dependency, ...] = ()
    selected_index: int | None = None
    loading: bool = False
    error_message: str | None = None


def default_state() -> LicensesState:
    """Factory for the initial empty dialog state."""
    return LicensesState()


def selected_dependency(state: LicensesState) -> Dependency | None:
    """Return the dependency currently highlighted in the list, if any."""
    if state.selected_index is None:
        return None
    if 0 <= state.selected_index < len(state.dependencies):
        return state.dependencies[state.selected_index]
    return None
