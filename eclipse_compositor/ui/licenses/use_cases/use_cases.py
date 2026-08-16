"""Master container for the Licenses dialog's use cases."""

from __future__ import annotations

from dataclasses import dataclass, field

from eclipse_compositor.ui.licenses.use_cases.load_dependencies_use_case import LoadDependenciesUseCase
from eclipse_compositor.ui.licenses.use_cases.select_dependency_use_case import SelectDependencyUseCase


@dataclass(frozen=True)
class UseCases:
    """Owning container for all Licenses dialog use cases."""

    load_dependencies: LoadDependenciesUseCase = field(default_factory=LoadDependenciesUseCase)
    select_dependency: SelectDependencyUseCase = SelectDependencyUseCase()
