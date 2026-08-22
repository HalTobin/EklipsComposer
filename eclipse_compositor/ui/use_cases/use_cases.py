"""Master container for the screen's use cases."""

from __future__ import annotations

from dataclasses import dataclass

from eclipse_compositor.ui.use_cases.blocking_job_cancelled_use_case import BlockingJobCancelledUseCase
from eclipse_compositor.ui.use_cases.cancel_job_use_case import CancelJobUseCase
from eclipse_compositor.ui.use_cases.clear_images_use_case import ClearImagesUseCase
from eclipse_compositor.ui.use_cases.export_composite_use_case import ExportCompositeUseCase
from eclipse_compositor.ui.use_cases.export_failed_use_case import ExportFailedUseCase
from eclipse_compositor.ui.use_cases.export_finished_use_case import ExportFinishedUseCase
from eclipse_compositor.ui.use_cases.export_progress_use_case import ExportProgressUseCase
from eclipse_compositor.ui.use_cases.import_failed_use_case import ImportFailedUseCase
from eclipse_compositor.ui.use_cases.import_finished_use_case import ImportFinishedUseCase
from eclipse_compositor.ui.use_cases.import_progress_use_case import ImportProgressUseCase
from eclipse_compositor.ui.use_cases.load_images_use_case import LoadImagesUseCase
from eclipse_compositor.ui.use_cases.open_project_failed_use_case import OpenProjectFailedUseCase
from eclipse_compositor.ui.use_cases.open_project_progress_use_case import OpenProjectProgressUseCase
from eclipse_compositor.ui.use_cases.open_project_use_case import OpenProjectUseCase
from eclipse_compositor.ui.use_cases.preview_failed_use_case import PreviewFailedUseCase
from eclipse_compositor.ui.use_cases.preview_finished_use_case import PreviewFinishedUseCase
from eclipse_compositor.ui.use_cases.preview_progress_use_case import PreviewProgressUseCase
from eclipse_compositor.ui.use_cases.project_opened_use_case import ProjectOpenedUseCase
from eclipse_compositor.ui.use_cases.project_saved_use_case import ProjectSavedUseCase
from eclipse_compositor.ui.use_cases.remove_image_use_case import RemoveImageUseCase
from eclipse_compositor.ui.use_cases.reorder_images_use_case import ReorderImagesUseCase
from eclipse_compositor.ui.use_cases.request_preview_use_case import RequestPreviewUseCase
from eclipse_compositor.ui.use_cases.save_project_failed_use_case import SaveProjectFailedUseCase
from eclipse_compositor.ui.use_cases.save_project_progress_use_case import SaveProjectProgressUseCase
from eclipse_compositor.ui.use_cases.save_project_use_case import SaveProjectUseCase
from eclipse_compositor.ui.use_cases.select_image_use_case import SelectImageUseCase
from eclipse_compositor.ui.use_cases.select_sidebar_tab_use_case import SelectSidebarTabUseCase
from eclipse_compositor.ui.use_cases.set_all_enabled_use_case import SetAllEnabledUseCase
from eclipse_compositor.ui.use_cases.toggle_favorite_use_case import ToggleFavoriteUseCase
from eclipse_compositor.ui.use_cases.toggle_image_use_case import ToggleImageUseCase
from eclipse_compositor.ui.use_cases.update_canvas_use_case import UpdateCanvasUseCase
from eclipse_compositor.ui.use_cases.update_gallery_show_only_favorites_use_case import UpdateGalleryShowOnlyFavoritesUseCase
from eclipse_compositor.ui.use_cases.update_gallery_sort_mode_use_case import UpdateGallerySortModeUseCase
from eclipse_compositor.ui.use_cases.update_gallery_view_mode_use_case import UpdateGalleryViewModeUseCase
from eclipse_compositor.ui.use_cases.update_colorimetry_use_case import UpdateColorimetryUseCase
from eclipse_compositor.ui.use_cases.update_layout_use_case import UpdateLayoutUseCase
from eclipse_compositor.ui.use_cases.update_mask_use_case import UpdateMaskUseCase
from eclipse_compositor.ui.use_cases.apply_image_detection_override_use_case import ApplyImageDetectionOverrideUseCase
from eclipse_compositor.ui.use_cases.update_zoom_use_case import UpdateZoomUseCase


@dataclass(frozen=True)
class UseCases:
    """Owning container for all screen-level use cases."""

    blocking_job_cancelled: BlockingJobCancelledUseCase = BlockingJobCancelledUseCase()
    load_images: LoadImagesUseCase = LoadImagesUseCase()
    clear_images: ClearImagesUseCase = ClearImagesUseCase()
    toggle_image: ToggleImageUseCase = ToggleImageUseCase()
    remove_image: RemoveImageUseCase = RemoveImageUseCase()
    reorder_images: ReorderImagesUseCase = ReorderImagesUseCase()
    select_image: SelectImageUseCase = SelectImageUseCase()
    select_sidebar_tab: SelectSidebarTabUseCase = SelectSidebarTabUseCase()
    toggle_favorite: ToggleFavoriteUseCase = ToggleFavoriteUseCase()
    set_all_enabled: SetAllEnabledUseCase = SetAllEnabledUseCase()
    update_gallery_view_mode: UpdateGalleryViewModeUseCase = UpdateGalleryViewModeUseCase()
    update_gallery_sort_mode: UpdateGallerySortModeUseCase = UpdateGallerySortModeUseCase()
    update_gallery_show_only_favorites: UpdateGalleryShowOnlyFavoritesUseCase = UpdateGalleryShowOnlyFavoritesUseCase()
    request_preview: RequestPreviewUseCase = RequestPreviewUseCase()
    export_composite: ExportCompositeUseCase = ExportCompositeUseCase()
    save_project: SaveProjectUseCase = SaveProjectUseCase()
    open_project: OpenProjectUseCase = OpenProjectUseCase()
    cancel_job: CancelJobUseCase = CancelJobUseCase()
    import_finished: ImportFinishedUseCase = ImportFinishedUseCase()
    import_failed: ImportFailedUseCase = ImportFailedUseCase()
    preview_finished: PreviewFinishedUseCase = PreviewFinishedUseCase()
    preview_failed: PreviewFailedUseCase = PreviewFailedUseCase()
    export_finished: ExportFinishedUseCase = ExportFinishedUseCase()
    export_failed: ExportFailedUseCase = ExportFailedUseCase()
    export_progress: ExportProgressUseCase = ExportProgressUseCase()
    project_saved: ProjectSavedUseCase = ProjectSavedUseCase()
    project_opened: ProjectOpenedUseCase = ProjectOpenedUseCase()
    save_project_failed: SaveProjectFailedUseCase = SaveProjectFailedUseCase()
    save_project_progress: SaveProjectProgressUseCase = SaveProjectProgressUseCase()
    open_project_failed: OpenProjectFailedUseCase = OpenProjectFailedUseCase()
    open_project_progress: OpenProjectProgressUseCase = OpenProjectProgressUseCase()
    import_progress: ImportProgressUseCase = ImportProgressUseCase()
    preview_progress: PreviewProgressUseCase = PreviewProgressUseCase()
    update_layout: UpdateLayoutUseCase = UpdateLayoutUseCase()
    update_colorimetry: UpdateColorimetryUseCase = UpdateColorimetryUseCase()
    update_mask: UpdateMaskUseCase = UpdateMaskUseCase()
    update_canvas: UpdateCanvasUseCase = UpdateCanvasUseCase()
    update_zoom: UpdateZoomUseCase = UpdateZoomUseCase()
    apply_image_detection_override: ApplyImageDetectionOverrideUseCase = ApplyImageDetectionOverrideUseCase()
