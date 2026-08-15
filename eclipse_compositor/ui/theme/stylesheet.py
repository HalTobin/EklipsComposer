"""Global Fusion stylesheet generated from design tokens."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from eclipse_compositor.ui.theme.tokens import COLOR, RADIUS, TYPE


def build_palette() -> QPalette:
    """Return a dark QPalette so unstyled native widgets stay on-theme."""
    palette = QPalette()
    bg = QColor(COLOR.bg_app)
    panel = QColor(COLOR.bg_panel)
    raised = QColor(COLOR.bg_raised)
    text = QColor(COLOR.text)
    muted = QColor(COLOR.text_muted)
    accent = QColor(COLOR.accent)
    accent_text = QColor(COLOR.accent_text)
    danger = QColor(COLOR.danger)
    sunken = QColor(COLOR.bg_sunken)

    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, sunken)
    palette.setColor(QPalette.ColorRole.AlternateBase, panel)
    palette.setColor(QPalette.ColorRole.ToolTipBase, raised)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, raised)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, danger)
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, accent_text)
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.PlaceholderText, muted)
    palette.setColor(QPalette.ColorRole.Light, QColor(COLOR.border_strong))
    palette.setColor(QPalette.ColorRole.Mid, QColor(COLOR.border))
    palette.setColor(QPalette.ColorRole.Dark, sunken)
    palette.setColor(QPalette.ColorRole.Shadow, bg)
    return palette


def build_stylesheet() -> str:
    """Return the application QSS. Values are interpolated from tokens."""
    c = COLOR
    r = RADIUS
    t = TYPE
    return f"""
    * {{
        font-size: {t.ui}px;
    }}

    QMainWindow, QDialog, QMessageBox {{
        background: {c.bg_app};
        color: {c.text};
    }}

    QMenuBar {{
        background: {c.bg_panel};
        color: {c.text};
        border-bottom: 1px solid {c.border};
        padding: 2px 6px;
    }}
    QMenuBar::item {{
        padding: 4px 10px;
        border-radius: {r.sm}px;
    }}
    QMenuBar::item:selected {{
        background: {c.bg_hover};
    }}
    QMenu {{
        background: {c.bg_raised};
        color: {c.text};
        border: 1px solid {c.border_strong};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: {r.sm}px;
    }}
    QMenu::item:selected {{
        background: {c.accent_soft};
        color: {c.text};
    }}
    QMenu::separator {{
        height: 1px;
        background: {c.border};
        margin: 4px 8px;
    }}

    QToolTip {{
        background: {c.bg_raised};
        color: {c.text};
        border: 1px solid {c.border_strong};
        padding: 4px 8px;
        border-radius: {r.sm}px;
    }}

    QLabel {{
        color: {c.text};
        background: transparent;
    }}
    QLabel#brandTitle {{
        font-size: {t.title}px;
        font-weight: 600;
        letter-spacing: 0.2px;
    }}
    QLabel#brandSubtitle {{
        color: {c.text_muted};
        font-size: {t.subtitle}px;
    }}
    QLabel#fieldLabel {{
        font-weight: 600;
        font-size: {t.caption}px;
        color: {c.text_muted};
        letter-spacing: 0.3px;
    }}
    QLabel#sectionTitle {{
        font-weight: 600;
        font-size: {t.ui}px;
        color: {c.text};
    }}
    QLabel#hintLabel, QLabel#captionLabel {{
        color: {c.text_faint};
        font-size: {t.caption}px;
    }}
    QLabel#emptyTitle {{
        font-size: 16px;
        font-weight: 600;
        color: {c.text};
    }}
    QLabel#aboutAppName {{
        font-size: 20px;
        font-weight: 600;
        color: {c.text};
        letter-spacing: 0.2px;
    }}
    QLabel#aboutMeta {{
        color: {c.text_muted};
        font-size: {t.ui}px;
    }}
    QLabel#aboutLink {{
        font-size: {t.caption}px;
    }}
    QLabel[banner="muted"] {{
        color: {c.text_muted};
        font-size: {t.caption}px;
        padding: 4px 2px;
        background: transparent;
        border: none;
    }}
    QLabel[banner="error"] {{
        color: {c.danger};
        font-size: {t.caption}px;
        padding: 8px 10px;
        background: {c.danger_bg};
        border: 1px solid {c.danger};
        border-radius: {r.md}px;
    }}
    QLabel[banner="success"] {{
        color: {c.success};
        font-size: {t.caption}px;
        padding: 8px 10px;
        background: rgba(109, 202, 143, 0.12);
        border: 1px solid {c.success};
        border-radius: {r.md}px;
    }}

    QFrame#section {{
        background: {c.bg_raised};
        border: 1px solid {c.border};
        border-radius: {r.lg}px;
    }}
    QFrame#segmentedControl {{
        background: {c.bg_sunken};
        border: 1px solid {c.border};
        border-radius: {r.md}px;
    }}
    QFrame#zoomHud {{
        background: {c.overlay};
        border: 1px solid {c.border_strong};
        border-radius: {r.md}px;
    }}
    QFrame#dropOverlay {{
        background: {c.accent_soft};
        border: 2px dashed {c.accent};
        border-radius: {r.lg}px;
    }}

    QWidget#jobOverlay {{
        background: {c.overlay};
    }}
    QFrame#jobCard {{
        background: {c.bg_panel};
        border: 1px solid {c.border_strong};
        border-radius: {r.lg}px;
    }}
    QLabel#jobTitle {{
        font-size: 16px;
        font-weight: 600;
        color: {c.text};
    }}
    QLabel#jobFile {{
        color: {c.text_muted};
        font-size: {t.ui}px;
    }}
    QLabel#jobPercent {{
        color: {c.text};
    }}
    QProgressBar {{
        background: {c.bg_sunken};
        border: 1px solid {c.border};
        border-radius: {r.sm}px;
        height: 16px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: {c.accent};
        border-radius: {r.sm}px;
    }}

    QWidget#sidebar, QWidget#gallery {{
        background: {c.bg_panel};
    }}
    QWidget#viewportPane, QWidget#fullscreenPreview {{
        background: {c.bg_viewport};
    }}

    QPushButton {{
        background: {c.bg_raised};
        color: {c.text};
        border: 1px solid {c.border_strong};
        border-radius: {r.md}px;
        padding: 7px 12px;
        min-height: 30px;
    }}
    QPushButton:hover {{
        background: {c.bg_hover};
        border-color: {c.accent};
    }}
    QPushButton:pressed {{
        background: {c.bg_sunken};
    }}
    QPushButton:disabled {{
        color: {c.text_faint};
        background: {c.bg_raised};
        border-color: {c.border};
    }}
    QPushButton[variant="primary"] {{
        background: {c.accent};
        color: {c.accent_text};
        border: none;
        font-weight: 600;
    }}
    QPushButton[variant="primary"]:hover {{
        background: {c.accent_hover};
        border: none;
    }}
    QPushButton[variant="primary"]:pressed {{
        background: {c.accent_pressed};
    }}
    QPushButton[variant="primary"]:disabled {{
        background: {c.border_strong};
        color: {c.text_faint};
    }}
    QPushButton[variant="secondary"] {{
        background: {c.bg_raised};
        color: {c.text};
        border: 1px solid {c.border_strong};
    }}
    QPushButton[variant="ghost"] {{
        background: transparent;
        color: {c.text_muted};
        border: 1px solid {c.border};
    }}
    QPushButton[variant="ghost"]:hover {{
        color: {c.danger};
        border-color: {c.danger};
        background: {c.danger_bg};
    }}
    QPushButton[variant="segment"] {{
        background: transparent;
        color: {c.text_muted};
        border: none;
        border-radius: {r.sm}px;
        padding: 6px 8px;
        min-height: 26px;
        font-size: {t.caption}px;
    }}
    QPushButton[variant="segment"]:hover {{
        color: {c.text};
        background: {c.bg_hover};
        border: none;
    }}
    QPushButton[variant="segment"]:checked {{
        background: {c.accent};
        color: {c.accent_text};
        font-weight: 600;
        border: none;
    }}
    QPushButton[variant="hud"] {{
        background: transparent;
        color: {c.text};
        border: none;
        padding: 2px 8px;
        min-height: 22px;
        border-radius: {r.sm}px;
        font-size: {t.caption}px;
    }}
    QPushButton[variant="hud"]:hover {{
        background: {c.accent_soft};
        border: none;
        color: {c.accent};
    }}

    QComboBox {{
        background: {c.bg_sunken};
        color: {c.text};
        border: 1px solid {c.border_strong};
        border-radius: {r.md}px;
        padding: 4px 8px;
        min-height: 28px;
    }}
    QComboBox:hover {{
        border-color: {c.accent};
    }}
    QComboBox:disabled {{
        color: {c.text_faint};
        border-color: {c.border};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}
    QComboBox QAbstractItemView {{
        background: {c.bg_raised};
        color: {c.text};
        border: 1px solid {c.border_strong};
        selection-background-color: {c.accent};
        selection-color: {c.accent_text};
        padding: 4px;
        outline: none;
    }}

    QSpinBox, QDoubleSpinBox {{
        background: {c.bg_sunken};
        color: {c.text};
        border: 1px solid {c.border_strong};
        border-radius: {r.sm}px;
        padding: 3px 6px;
        min-height: 26px;
    }}
    QSpinBox:hover, QDoubleSpinBox:hover {{
        border-color: {c.accent};
    }}
    QSpinBox:disabled, QDoubleSpinBox:disabled {{
        color: {c.text_faint};
        border-color: {c.border};
    }}
    QSpinBox#compactSpin, QDoubleSpinBox#compactSpin {{
        min-height: 24px;
        padding: 2px 6px;
    }}

    QCheckBox {{
        color: {c.text};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {c.border_strong};
        background: {c.bg_sunken};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c.accent};
    }}
    QCheckBox::indicator:checked {{
        background: {c.accent};
        border-color: {c.accent};
    }}
    QCheckBox:disabled {{
        color: {c.text_faint};
    }}

    QSlider::groove:horizontal {{
        height: 4px;
        background: {c.border};
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {c.accent};
        border-radius: 2px;
    }}
    QSlider::add-page:horizontal {{
        background: {c.border};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {c.accent};
        width: 14px;
        height: 14px;
        margin: -6px 0;
        border-radius: 7px;
        border: 2px solid {c.accent_text};
    }}
    QSlider::handle:horizontal:hover {{
        background: {c.accent_hover};
    }}
    QSlider:disabled {{
        opacity: 0.45;
    }}
    QSlider[tall="true"]::groove:horizontal {{
        height: 6px;
    }}
    QSlider[tall="true"]::handle:horizontal {{
        width: 18px;
        height: 18px;
        margin: -7px 0;
        border-radius: 9px;
    }}

    QListWidget {{
        background: {c.bg_sunken};
        color: {c.text};
        border: 1px solid {c.border};
        border-radius: {r.md}px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 6px 8px;
        border-radius: {r.sm}px;
        min-height: 52px;
    }}
    QListWidget::item:hover {{
        background: {c.bg_hover};
    }}
    QListWidget::item:selected {{
        background: {c.accent_soft};
        color: {c.text};
    }}

    QScrollArea {{
        background: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
        background: {c.border_strong};
        border-radius: 4px;
        min-height: 24px;
        min-width: 24px;
    }}
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
        background: {c.text_faint};
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0;
        height: 0;
    }}
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
    }}

    QSplitter::handle {{
        background: {c.border};
    }}
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    QSplitter::handle:vertical {{
        height: 1px;
    }}
    QSplitter::handle:hover {{
        background: {c.accent};
    }}

    QStackedWidget {{
        background: transparent;
    }}

    QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
        background: transparent;
        border: none;
        width: 16px;
    }}

    QDialogButtonBox QPushButton {{
        min-width: 88px;
    }}
    """


def apply_theme(app: QApplication) -> None:
    """Apply Fusion, the dark palette, and QSS. Call once after QApplication exists."""
    app.setStyle("Fusion")
    app.setPalette(build_palette())
    font = app.font()
    font.setPointSize(13)
    app.setFont(font)
    app.setStyleSheet(build_stylesheet())
