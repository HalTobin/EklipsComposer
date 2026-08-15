"""Unit tests for SelectSidebarTabUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState, SidebarTab
from eclipse_compositor.ui.use_cases import SelectSidebarTabUseCase


class TestSelectSidebarTabUseCase:
    """Test suite for SelectSidebarTabUseCase."""

    def test_selects_composite_tab(self) -> None:
        """Test selecting the composite tab."""
        state = ScreenState(sidebar_tab=SidebarTab.COLORIMETRY)

        next_state = SelectSidebarTabUseCase().invoke(state, SidebarTab.COMPOSITE)

        assert next_state.sidebar_tab == SidebarTab.COMPOSITE

    def test_selects_colorimetry_tab(self) -> None:
        """Test selecting the colorimetry tab."""
        state = ScreenState(sidebar_tab=SidebarTab.COMPOSITE)

        next_state = SelectSidebarTabUseCase().invoke(state, SidebarTab.COLORIMETRY)

        assert next_state.sidebar_tab == SidebarTab.COLORIMETRY

    def test_selects_mask_tab(self) -> None:
        """Test selecting the mask tab."""
        state = ScreenState(sidebar_tab=SidebarTab.COMPOSITE)

        next_state = SelectSidebarTabUseCase().invoke(state, SidebarTab.MASK)

        assert next_state.sidebar_tab == SidebarTab.MASK

    def test_selects_canvas_tab(self) -> None:
        """Test selecting the canvas tab."""
        state = ScreenState(sidebar_tab=SidebarTab.COLORIMETRY)

        next_state = SelectSidebarTabUseCase().invoke(state, SidebarTab.CANVAS)

        assert next_state.sidebar_tab == SidebarTab.CANVAS

    def test_tab_switching_returns_unchanged_when_same(self) -> None:
        """Test that selecting the same tab returns unchanged state."""
        state = ScreenState(sidebar_tab=SidebarTab.COMPOSITE)

        next_state = SelectSidebarTabUseCase().invoke(state, SidebarTab.COMPOSITE)

        assert next_state is state
