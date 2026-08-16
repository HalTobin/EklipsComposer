"""Use case for highlighting a dependency in the list."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.licenses.state import LicensesState


@dataclass(frozen=True)
class SelectDependencyUseCase:
    """Keep the dialog state aligned with the selected dependency row."""

    def invoke(self, state: LicensesState, index: int) -> LicensesState:
        if index == state.selected_index:
            return state
        if not (0 <= index < len(state.dependencies)):
            return state
        return replace(state, selected_index=index)
