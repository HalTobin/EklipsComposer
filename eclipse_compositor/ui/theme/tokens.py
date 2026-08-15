"""Design tokens for the EklipsComposer UI.

Colours follow the app icon: near-black totality and a diamond-ring gold.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorTokens:
    """Hex / rgba colours used by the palette, QSS, and painted widgets."""

    bg_app: str = "#0A0A0C"
    bg_panel: str = "#12141A"
    bg_raised: str = "#1A1D26"
    bg_sunken: str = "#08090C"
    bg_hover: str = "#22262F"
    bg_viewport: str = "#2A2E36"
    border: str = "#2A2F3A"
    border_strong: str = "#3D4454"
    text: str = "#EEEDE8"
    text_muted: str = "#8B919E"
    text_faint: str = "#6A7080"
    accent: str = "#FFC94A"
    accent_hover: str = "#FFD56A"
    accent_pressed: str = "#E8B43C"
    accent_soft: str = "rgba(255, 201, 74, 0.16)"
    accent_text: str = "#1A1408"
    danger: str = "#E07070"
    danger_bg: str = "rgba(224, 112, 112, 0.12)"
    success: str = "#6DCA8F"
    overlay: str = "rgba(10, 10, 12, 0.82)"


@dataclass(frozen=True)
class SpaceTokens:
    """Spacing scale in pixels."""

    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    panel: int = 16


@dataclass(frozen=True)
class RadiusTokens:
    """Corner radii in pixels."""

    sm: int = 6
    md: int = 8
    lg: int = 12
    pill: int = 999


@dataclass(frozen=True)
class TypeTokens:
    """UI type sizes in pixels (set on QFont / QSS)."""

    ui: int = 13
    title: int = 17
    subtitle: int = 12
    caption: int = 11


COLOR = ColorTokens()
SPACE = SpaceTokens()
RADIUS = RadiusTokens()
TYPE = TypeTokens()
