"""Licenses feature: dependency catalog dialog (MVI)."""

from eclipse_compositor.ui.licenses.models import Dependency, License
from eclipse_compositor.ui.licenses.provider import (
    DependencyProvider,
    ReportFileDependencyProvider,
    StaticDependencyProvider,
)
from eclipse_compositor.ui.licenses.state import LicensesState, default_state, selected_dependency
from eclipse_compositor.ui.licenses.view import LicensesDialog, show_licenses_dialog
from eclipse_compositor.ui.licenses.viewmodel import LicensesViewModel

__all__ = [
    "Dependency",
    "License",
    "DependencyProvider",
    "ReportFileDependencyProvider",
    "StaticDependencyProvider",
    "LicensesState",
    "default_state",
    "selected_dependency",
    "LicensesDialog",
    "LicensesViewModel",
    "show_licenses_dialog",
]
