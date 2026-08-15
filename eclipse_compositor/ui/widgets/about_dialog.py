"""About dialog: app name, version, developer, and repository link."""

from __future__ import annotations

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor import APP_NAME, GITHUB_URL, __author__, __version__
from eclipse_compositor.resources import app_mark_path
from eclipse_compositor.ui.theme import COLOR, SPACE, EclipseMark, qicon_from_path

_MIT_LICENSE = """MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

_BSD_3_CLAUSE = """BSD 3-Clause License

Copyright (c) [year], [fullname]
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

_LGPL_V3 = """GNU LESSER GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
Everyone is permitted to copy and distribute verbatim copies of this license
document, but changing it is not allowed.

This version of the GNU Lesser General Public License incorporates the terms
and conditions of version 3 of the GNU General Public License, supplemented
by the additional permissions listed below.

0. Additional Definitions.

The terms "covered work," "special exception," and "library" are defined in
this License.

A "covered work" means either the unmodified Library as distributed by the
licensor, or a work based on the Library.

A "special exception" is a permission given by the copyright holder that
allows a user to link or otherwise combine the Library with a work that is
not a Library.

The "Library" refers to a covered work governed by this License, other than
an application or a combined work as defined below.

A "combined work" is a work produced by combining or linking the Library with
other code not covered by this License.

The precise terms and conditions for copying, distribution and modification
follow. Pay close attention to the difference between a "work based on the
Library" and a "combined work" that includes the Library. The former is
covered by this License, while the latter is governed by the terms and
conditions of the other code, not by this License.

To qualify as a combined work with the Library, the terms of this License
must allow the user to link or otherwise combine the Library with the code
not covered by this License.

The GNU General Public License version 3, with the additional permissions
listed in section 7, is the version of the GNU General Public License that
applies to the combined work as a whole. The combined work is not a work
based on the Library, but is a separate work. It must be distributed under
this License, and the additional permissions in section 7 are applicable to
that work.

When you distribute a copy of the covered work, you may not impose any
further restrictions on the recipients' exercise of the rights granted or
ensured by this License.

This License is intended to guarantee your freedom to share and change all
versions of a library that is free software. It is designed to make sure the
library stays free software for all its users.

The precise terms and conditions for copying, distribution and modification
follow. Pay close attention to the difference between the "Library" and the
"Application" which is the work that uses the library.

The terms of the GNU General Public License are a set of conditions for the
complete redistribution of the work and the Library, and any combined work
that uses the Library.

This license is compatible with the GNU General Public License version 3, and
is designed to apply to a library when there are no additional restrictions on
its use.

See the full GNU LGPL v3 text for exact legal terms.
"""

_LICENSES_TEXT = """EklipsComposer bundles or depends on open-source projects for rendering,
image processing, packaging, and UI functionality. The in-app projects below
include direct repository links when available and the full license notices
embedded here for convenience.

Project links:
- PySide6: https://github.com/pyside/pyside-setup
- Qt: https://github.com/qt/qtbase
- NumPy: https://github.com/numpy/numpy
- Pillow: https://github.com/python-pillow/Pillow
- piexif: https://github.com/hMatoba/piexif
- FFmpeg: https://github.com/FFmpeg/FFmpeg
- EklipsComposer: https://github.com/HalTobin/EklipsComposer

MIT License
------------
{mit}

BSD 3-Clause License
--------------------
{bsd}

GNU Lesser General Public License v3.0
--------------------------------------
{lgpl}

FFmpeg notice
-------------
FFmpeg is licensed under the GNU Lesser General Public License version 2.1 or
later, or under the GNU General Public License version 2 or later depending on
how it is built and used. See the upstream repository and the bundled source in
this project for the exact legal notices for your distribution.
""".format(
    mit=escape(_MIT_LICENSE),
    bsd=escape(_BSD_3_CLAUSE),
    lgpl=escape(_LGPL_V3),
)


class LicensesDialog(QDialog):
    """Display the project and bundled dependency license references."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("licensesDialog")
        self.setWindowTitle("Licenses")
        self.setModal(True)
        self.setMinimumWidth(640)
        self.setMinimumHeight(420)

        self._license_text = _LICENSES_TEXT

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE.xl, SPACE.xl, SPACE.xl, SPACE.lg)
        layout.setSpacing(SPACE.md)

        title = QLabel("Open-source licenses")
        title.setObjectName("aboutAppName")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        intro = QLabel(
            "<p><a href=\"https://github.com/HalTobin/EklipsComposer\" "
            "style=\"color: {color};\">EklipsComposer on GitHub</a></p>"
            "<p><a href=\"https://github.com/pyside/pyside-setup\" "
            "style=\"color: {color};\">PySide6</a> &nbsp; "
            "<a href=\"https://github.com/numpy/numpy\" style=\"color: {color};\">NumPy</a> &nbsp; "
            "<a href=\"https://github.com/python-pillow/Pillow\" style=\"color: {color};\">Pillow</a> &nbsp; "
            "<a href=\"https://github.com/hMatoba/piexif\" style=\"color: {color};\">piexif</a> &nbsp; "
            "<a href=\"https://github.com/FFmpeg/FFmpeg\" style=\"color: {color};\">FFmpeg</a></p>"
            .format(color=COLOR.accent)
        )
        intro.setOpenExternalLinks(True)
        intro.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(intro)

        text = QTextBrowser()
        text.setReadOnly(True)
        text.setOpenExternalLinks(True)
        text.setHtml(
            "<pre style='white-space: pre-wrap; font-family: monospace;'>"
            + self._license_text
            + "</pre>"
        )
        layout.addWidget(text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class AboutDialog(QDialog):
    """Credits and version for EklipsComposer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setWindowTitle(f"About {APP_NAME}")
        self.setModal(True)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE.xl, SPACE.xl, SPACE.xl, SPACE.lg)
        layout.setSpacing(SPACE.sm)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        icon = qicon_from_path(app_mark_path(), size=96)
        if not icon.isNull():
            mark = QLabel()
            mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mark.setPixmap(icon.pixmap(96, 96))
            layout.addWidget(mark, alignment=Qt.AlignmentFlag.AlignHCenter)
        else:
            layout.addWidget(EclipseMark(size=96), alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel(APP_NAME)
        title.setObjectName("aboutAppName")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel(f"Version {__version__}")
        version.setObjectName("aboutMeta")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        developer = QLabel(f"Developed by {__author__}")
        developer.setObjectName("aboutMeta")
        developer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(developer)

        repo = QLabel(
            f'<a href="{GITHUB_URL}" style="color: {COLOR.accent};">'
            f"{GITHUB_URL.removeprefix('https://')}</a>"
        )
        repo.setObjectName("aboutLink")
        repo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        repo.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        repo.setOpenExternalLinks(True)
        layout.addWidget(repo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        licenses = buttons.addButton("Licenses", QDialogButtonBox.ButtonRole.ActionRole)
        licenses.clicked.connect(self._show_licenses)
        buttons.rejected.connect(self.reject)
        layout.addSpacing(SPACE.md)
        layout.addWidget(buttons)

    def _show_licenses(self) -> None:
        show_licenses_dialog(self)


def show_about_dialog(parent: QWidget | None = None) -> None:
    """Open the About dialog modally."""
    dialog = AboutDialog(parent)
    dialog.exec()


def show_licenses_dialog(parent: QWidget | None = None) -> None:
    """Open the implicit runtime license references dialog."""
    dialog = LicensesDialog(parent)
    dialog.exec()
