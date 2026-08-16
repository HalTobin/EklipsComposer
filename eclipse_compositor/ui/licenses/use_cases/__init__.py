"""Application use cases for the Licenses dialog."""

from eclipse_compositor.ui.licenses.use_cases.load_dependencies_use_case import LoadDependenciesUseCase
from eclipse_compositor.ui.licenses.use_cases.select_dependency_use_case import SelectDependencyUseCase
from eclipse_compositor.ui.licenses.use_cases.use_cases import UseCases

__all__ = [
    "LoadDependenciesUseCase",
    "SelectDependencyUseCase",
    "UseCases",
]
