"""Unit tests for BlockingJobCancelledUseCase."""

from pathlib import Path

from eclipse_compositor.ui.state import BlockingJob, ImageItem, JobStatus, ScreenState
from eclipse_compositor.ui.use_cases import BlockingJobCancelledUseCase


class TestBlockingJobCancelledUseCase:
    """Test suite for BlockingJobCancelledUseCase."""

    def test_clears_blocking_job_state(self) -> None:
        state = ScreenState(
            blocking_job=BlockingJob.OPEN,
            blocking_job_path=Path("/tmp/project.vlt"),
            blocking_job_cancelling=True,
            import_status=JobStatus.RUNNING,
            export_status=JobStatus.RUNNING,
            progress=0.8,
            error_message="previous error",
        )

        next_state = BlockingJobCancelledUseCase().invoke(state)

        assert next_state.blocking_job is None
        assert next_state.blocking_job_path is None
        assert next_state.blocking_job_cancelling is False
        assert next_state.import_status == JobStatus.IDLE
        assert next_state.export_status == JobStatus.IDLE
        assert next_state.progress == 0.0
        assert next_state.status_message == "Cancelled."
        assert next_state.error_message is None

    def test_preserves_unrelated_screen_state(self) -> None:
        image = ImageItem(path=Path("/tmp/eclipse.jpg"))
        project_path = Path("/tmp/project.vlt")
        state = ScreenState(
            images=(image,),
            selected_index=0,
            last_project_path=project_path,
            blocking_job=BlockingJob.EXPORT,
        )

        next_state = BlockingJobCancelledUseCase().invoke(state)

        assert next_state.images == (image,)
        assert next_state.selected_index == 0
        assert next_state.last_project_path == project_path
