"""Licenses dialog ViewModel — single state, unidirectional flow.

No user-facing intents are complex enough to warrant a ``ScreenAction``
hierarchy here, so the view model exposes direct methods that each delegate
to a use case and emit the resulting state.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from eclipse_compositor.ui.licenses.state import LicensesState, default_state
from eclipse_compositor.ui.licenses.use_cases import UseCases


class LicensesViewModel(QObject):
    """Owns ``LicensesState`` and exposes it via ``state_changed``."""

    state_changed = Signal(LicensesState)

    def __init__(self, use_cases: UseCases | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._use_cases = use_cases or UseCases()
        self._state = default_state()

    @property
    def state(self) -> LicensesState:
        """Current dialog state."""
        return self._state

    def load(self) -> None:
        """Fetch the dependency catalog and select the first entry."""
        self._state = self._use_cases.load_dependencies.invoke(self._state)
        self.state_changed.emit(self._state)

    def select_dependency(self, index: int) -> None:
        """Highlight a dependency row by its position in the list."""
        self._state = self._use_cases.select_dependency.invoke(self._state, index)
        self.state_changed.emit(self._state)
