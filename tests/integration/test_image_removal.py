import os
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PIL import Image
from PySide6.QtWidgets import QApplication

from eclipse_compositor.ui.actions import RemoveImage
from eclipse_compositor.ui.state import ImageItem
from eclipse_compositor.ui.viewmodel import ScreenViewModel
from eclipse_compositor.ui.widgets.frame_preview import read_image_properties


def test_remove_image_updates_state_and_selection():
    app = QApplication.instance() or QApplication([])
    vm = ScreenViewModel()
    vm._state = replace(
        vm.state,
        images=(
            ImageItem(path=Path("/tmp/first.jpg")),
            ImageItem(path=Path("/tmp/second.jpg")),
            ImageItem(path=Path("/tmp/third.jpg")),
        ),
        selected_index=1,
        proxy_ready=True,
        preview_bgr=np.zeros((16, 16, 3), dtype=np.uint8),
    )

    vm.dispatch(RemoveImage((0, 2)))

    assert [item.path for item in vm.state.images] == [Path("/tmp/second.jpg")]
    assert vm.state.selected_index == 0
    assert vm.state.preview_bgr is not None
    assert app is not None


def test_read_image_properties_extracts_resolution_and_exif(tmp_path):
    image_path = tmp_path / "eclipse.jpg"
    image = Image.new("RGB", (2000, 1500), "white")
    exif = image.getexif()
    exif[270] = "Totality over the ridge"
    exif[306] = "2024:05:17 12:34:56"
    image.save(image_path, exif=exif)

    props = read_image_properties(image_path)

    assert props["Resolution"] == "2000 × 1500"
    assert props["Date"] == "2024-05-17 12:34:56"
    assert props["Comment"] == "Totality over the ridge"
