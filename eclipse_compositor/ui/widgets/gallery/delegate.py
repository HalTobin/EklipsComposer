"""Custom item delegate for rendering modern, responsive gallery cards across all view modes."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from eclipse_compositor.ui.state import GalleryViewMode, ImageItem
from eclipse_compositor.ui.theme import COLOR


class GalleryItemDelegate(QStyledItemDelegate):
    """Renders cards with custom thumbnails, status badges, checkboxes, and interactive favorite stars."""

    favorite_toggled = Signal(int)  # visible_row
    enabled_toggled = Signal(int)   # visible_row

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._view_mode = GalleryViewMode.LIST_PREVIEW
        self._hover_row: int = -1

    def set_view_mode(self, mode: GalleryViewMode) -> None:
        self._view_mode = mode

    def item_size_hint(self, mode: GalleryViewMode) -> QSize:
        if mode == GalleryViewMode.ICON:
            return QSize(96, 114)
        if mode == GalleryViewMode.LIST_SIMPLE:
            return QSize(200, 32)
        return QSize(200, 56)

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return self.item_size_hint(self._view_mode)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        item: ImageItem | None = index.data(Qt.ItemDataRole.UserRole)
        if item is None or not isinstance(item, ImageItem):
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        if self._view_mode == GalleryViewMode.ICON:
            self._paint_icon_mode(painter, option.rect, item, is_selected, is_hovered)
        elif self._view_mode == GalleryViewMode.LIST_SIMPLE:
            self._paint_simple_mode(painter, option.rect, item, is_selected, is_hovered)
        else:
            self._paint_preview_mode(painter, option.rect, item, is_selected, is_hovered)

        painter.restore()

    def editorEvent(self, event, model, option: QStyleOptionViewItem, index) -> bool:
        if event.type() == QMouseEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            item: ImageItem | None = index.data(Qt.ItemDataRole.UserRole)
            if item is not None and isinstance(item, ImageItem):
                visible_row = index.row()
                star_rect = self._get_star_rect(option.rect)
                check_rect = self._get_check_rect(option.rect)

                if star_rect.contains(pos):
                    self.favorite_toggled.emit(visible_row)
                    return True
                if check_rect.contains(pos):
                    self.enabled_toggled.emit(visible_row)
                    return True

        return super().editorEvent(event, model, option, index)

    # ---- Rect Calculators for Clicks ----

    def _get_star_rect(self, cell_rect: QRect) -> QRect:
        if self._view_mode == GalleryViewMode.ICON:
            card = cell_rect.adjusted(3, 3, -3, -3)
            return QRect(card.right() - 24, card.top() + 4, 22, 22)
        if self._view_mode == GalleryViewMode.LIST_SIMPLE:
            card = cell_rect.adjusted(2, 1, -2, -1)
            return QRect(card.right() - 26, card.top() + (card.height() - 20) // 2, 22, 20)
        card = cell_rect.adjusted(2, 2, -2, -2)
        return QRect(card.right() - 30, card.top() + (card.height() - 26) // 2, 26, 26)

    def _get_check_rect(self, cell_rect: QRect) -> QRect:
        if self._view_mode == GalleryViewMode.ICON:
            card = cell_rect.adjusted(3, 3, -3, -3)
            return QRect(card.left() + 4, card.top() + 4, 22, 22)
        if self._view_mode == GalleryViewMode.LIST_SIMPLE:
            card = cell_rect.adjusted(2, 1, -2, -1)
            return QRect(card.left() + 6, card.top() + (card.height() - 18) // 2, 18, 18)
        card = cell_rect.adjusted(2, 2, -2, -2)
        return QRect(card.left() + 8, card.top() + (card.height() - 18) // 2, 18, 18)

    # ---- Paint Mode 1: List Preview (Default) ----

    def _paint_preview_mode(
        self,
        painter: QPainter,
        rect: QRect,
        item: ImageItem,
        is_selected: bool,
        is_hovered: bool,
    ) -> None:
        card = rect.adjusted(2, 2, -2, -2)

        # 1. Card Background & Border
        card_path = QPainterPath()
        card_path.addRoundedRect(card, 6, 6)

        if is_selected:
            painter.fillPath(card_path, QColor(COLOR.accent_soft))
            painter.setPen(QPen(QColor(COLOR.accent), 1.2))
            painter.drawPath(card_path)
            # Left accent pill indicator
            pill_rect = QRect(card.left(), card.top() + 8, 3, card.height() - 16)
            pill_path = QPainterPath()
            pill_path.addRoundedRect(pill_rect, 1.5, 1.5)
            painter.fillPath(pill_path, QColor(COLOR.accent))
        elif is_hovered:
            painter.fillPath(card_path, QColor(COLOR.bg_hover))
            painter.setPen(QPen(QColor(COLOR.border_strong), 1))
            painter.drawPath(card_path)
        else:
            painter.fillPath(card_path, QColor(COLOR.bg_panel))
            painter.setPen(QPen(QColor(COLOR.border), 0.8))
            painter.drawPath(card_path)

        # 2. Checkbox
        check_rect = self._get_check_rect(rect)
        self._draw_checkbox(painter, check_rect, item.enabled)

        # 3. Thumbnail
        thumb_rect = QRect(check_rect.right() + 8, card.top() + (card.height() - 42) // 2, 42, 42)
        self._draw_thumbnail(painter, thumb_rect, item)

        # 4. Favorite Star
        star_rect = self._get_star_rect(rect)
        self._draw_star(painter, star_rect, item.favorite, is_hovered)

        # 5. Text Area
        text_left = thumb_rect.right() + 10
        text_right = star_rect.left() - 6
        text_width = max(10, text_right - text_left)

        # Line 1: Filename
        font_title = painter.font()
        font_title.setPointSize(12)
        font_title.setBold(True)
        painter.setFont(font_title)
        painter.setPen(QColor(COLOR.text if item.enabled else COLOR.text_muted))
        fm = QFontMetrics(font_title)
        elided_title = fm.elidedText(item.path.name, Qt.TextElideMode.ElideMiddle, text_width)
        painter.drawText(text_left, card.top() + 20, elided_title)

        # Line 2: Detection / Metadata badge
        font_sub = painter.font()
        font_sub.setPointSize(10)
        font_sub.setBold(False)
        painter.setFont(font_sub)

        if item.detection_ok is False:
            painter.setPen(QColor(COLOR.danger))
            painter.drawText(text_left, card.top() + 38, "⚠ No disc detected")
        elif item.detection_ok is True:
            painter.setPen(QColor(COLOR.success))
            painter.drawText(text_left, card.top() + 38, "● Disc found")
        else:
            painter.setPen(QColor(COLOR.text_faint))
            painter.drawText(text_left, card.top() + 38, "Ready")

    # ---- Paint Mode 2: Compact List ----

    def _paint_simple_mode(
        self,
        painter: QPainter,
        rect: QRect,
        item: ImageItem,
        is_selected: bool,
        is_hovered: bool,
    ) -> None:
        card = rect.adjusted(2, 1, -2, -1)
        card_path = QPainterPath()
        card_path.addRoundedRect(card, 4, 4)

        if is_selected:
            painter.fillPath(card_path, QColor(COLOR.accent_soft))
            painter.setPen(QPen(QColor(COLOR.accent), 1))
            painter.drawPath(card_path)
        elif is_hovered:
            painter.fillPath(card_path, QColor(COLOR.bg_hover))
        else:
            painter.fillPath(card_path, QColor(COLOR.bg_panel))

        # Checkbox
        check_rect = self._get_check_rect(rect)
        self._draw_checkbox(painter, check_rect, item.enabled)

        # Star
        star_rect = self._get_star_rect(rect)
        self._draw_star(painter, star_rect, item.favorite, is_hovered)

        # Status dot
        dot_x = check_rect.right() + 8
        dot_y = card.top() + (card.height() - 6) // 2
        dot_color = (
            QColor(COLOR.danger)
            if item.detection_ok is False
            else (QColor(COLOR.success) if item.detection_ok is True else QColor(COLOR.text_faint))
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)
        painter.drawEllipse(dot_x, dot_y, 6, 6)

        # Filename
        text_left = dot_x + 12
        text_right = star_rect.left() - 6
        text_width = max(10, text_right - text_left)

        font = painter.font()
        font.setPointSize(11)
        painter.setFont(font)
        painter.setPen(QColor(COLOR.text if item.enabled else COLOR.text_muted))
        fm = QFontMetrics(font)
        elided = fm.elidedText(item.path.name, Qt.TextElideMode.ElideMiddle, text_width)
        painter.drawText(
            QRect(text_left, card.top(), text_width, card.height()),
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            elided,
        )

    # ---- Paint Mode 3: Grid / Icons ----

    def _paint_icon_mode(
        self,
        painter: QPainter,
        rect: QRect,
        item: ImageItem,
        is_selected: bool,
        is_hovered: bool,
    ) -> None:
        card = rect.adjusted(3, 3, -3, -3)
        card_path = QPainterPath()
        card_path.addRoundedRect(card, 8, 8)

        if is_selected:
            painter.fillPath(card_path, QColor(COLOR.accent_soft))
            painter.setPen(QPen(QColor(COLOR.accent), 1.4))
            painter.drawPath(card_path)
        elif is_hovered:
            painter.fillPath(card_path, QColor(COLOR.bg_hover))
            painter.setPen(QPen(QColor(COLOR.border_strong), 1))
            painter.drawPath(card_path)
        else:
            painter.fillPath(card_path, QColor(COLOR.bg_raised))
            painter.setPen(QPen(QColor(COLOR.border), 0.8))
            painter.drawPath(card_path)

        # Thumbnail
        thumb_size = card.width() - 8
        thumb_rect = QRect(card.left() + 4, card.top() + 4, thumb_size, thumb_size)
        self._draw_thumbnail(painter, thumb_rect, item)

        # Badges with translucent dark backing
        check_rect = self._get_check_rect(rect)
        self._draw_badge_backing(painter, check_rect)
        self._draw_checkbox(painter, check_rect, item.enabled)

        star_rect = self._get_star_rect(rect)
        self._draw_badge_backing(painter, star_rect)
        self._draw_star(painter, star_rect, item.favorite, is_hovered)

        # Filename
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor(COLOR.text if item.enabled else COLOR.text_muted))
        label_rect = QRect(card.left() + 4, thumb_rect.bottom() + 4, thumb_size, 16)
        fm = QFontMetrics(font)
        elided = fm.elidedText(item.path.name, Qt.TextElideMode.ElideMiddle, thumb_size)
        painter.drawText(label_rect, int(Qt.AlignmentFlag.AlignCenter), elided)

    # ---- Drawing Helpers ----

    def _draw_badge_backing(self, painter: QPainter, rect: QRect) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 160))
        painter.drawRoundedRect(rect, 4, 4)

    def _draw_checkbox(self, painter: QPainter, rect: QRect, checked: bool) -> None:
        box = rect.adjusted(2, 2, -2, -2)
        path = QPainterPath()
        path.addRoundedRect(box, 3, 3)

        if checked:
            painter.fillPath(path, QColor(COLOR.accent))
            # Draw checkmark
            pen = QPen(QColor(COLOR.accent_text), 1.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            x, y, w, h = box.x(), box.y(), box.width(), box.height()
            p1 = QPoint(int(x + w * 0.22), int(y + h * 0.52))
            p2 = QPoint(int(x + w * 0.44), int(y + h * 0.74))
            p3 = QPoint(int(x + w * 0.78), int(y + h * 0.28))
            painter.drawLine(p1, p2)
            painter.drawLine(p2, p3)
        else:
            painter.fillPath(path, QColor(COLOR.bg_sunken))
            painter.setPen(QPen(QColor(COLOR.border_strong), 1.2))
            painter.drawPath(path)

    def _draw_thumbnail(self, painter: QPainter, rect: QRect, item: ImageItem) -> None:
        path = QPainterPath()
        path.addRoundedRect(rect, 4, 4)
        painter.fillPath(path, QColor(COLOR.bg_sunken))

        # Check if thumbnail image exists
        if item.thumbnail_path:
            try:
                from eclipse_compositor.ui.widgets.gallery.list import _pixmap_from_thumb
                pix = _pixmap_from_thumb(item.thumbnail_path)
                if not pix.isNull():
                    scaled = pix.scaled(
                        rect.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    px = rect.x() + (rect.width() - scaled.width()) // 2
                    py = rect.y() + (rect.height() - scaled.height()) // 2
                    painter.save()
                    painter.setClipPath(path)
                    painter.drawPixmap(px, py, scaled)
                    painter.restore()
            except Exception:
                pass

        painter.setPen(QPen(QColor(COLOR.border), 0.8))
        painter.drawPath(path)

    def _draw_star(self, painter: QPainter, rect: QRect, favorite: bool, is_hovered: bool) -> None:
        font = painter.font()
        font.setPointSize(14)
        painter.setFont(font)

        if favorite:
            painter.setPen(QColor(COLOR.accent))
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), "★")
        elif is_hovered:
            painter.setPen(QColor(COLOR.accent_hover))
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), "☆")
        else:
            painter.setPen(QColor(COLOR.text_faint))
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), "☆")
