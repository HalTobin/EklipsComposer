"""Use case for switching the active sidebar tab."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState, SidebarTab


@dataclass(frozen=True)
class SelectSidebarTabUseCase:
    """Keep the screen state aligned with the selected sidebar tab."""

    def invoke(self, state: ScreenState, value: object) -> ScreenState:
        tab = value if isinstance(value, SidebarTab) else SidebarTab(value)
        if tab == state.sidebar_tab:
            return state
        return replace(state, sidebar_tab=tab)
