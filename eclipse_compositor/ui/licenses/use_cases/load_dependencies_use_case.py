"""Use case for (re)loading the dependency catalog."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from eclipse_compositor.ui.licenses.provider import DependencyProvider, StaticDependencyProvider
from eclipse_compositor.ui.licenses.state import LicensesState


@dataclass(frozen=True)
class LoadDependenciesUseCase:
    """Fetch the dependency catalog and select the first entry by default."""

    provider: DependencyProvider = field(default_factory=StaticDependencyProvider)

    def invoke(self, state: LicensesState) -> LicensesState:
        try:
            dependencies = self.provider.fetch()
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI, not fatal
            return replace(state, loading=False, error_message=str(exc))
        selected = 0 if dependencies else None
        return replace(
            state,
            dependencies=dependencies,
            selected_index=selected,
            loading=False,
            error_message=None,
        )
