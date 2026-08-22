"""Master container for the Adjust Circle feature's use cases."""

from __future__ import annotations

from dataclasses import dataclass, field

from eclipse_compositor.ui.feature.adjust_circle.use_cases.apply_adjust_circle_use_case import (
    ApplyAdjustCircleUseCase,
)
from eclipse_compositor.ui.feature.adjust_circle.use_cases.load_adjust_circle_use_case import (
    LoadAdjustCircleUseCase,
)
from eclipse_compositor.ui.feature.adjust_circle.use_cases.update_adjust_circle_use_case import (
    UpdateAdjustCircleUseCase,
)


@dataclass(frozen=True)
class AdjustCircleUseCases:
    """Owning container for all adjust circle use cases."""

    load_adjust_circle: LoadAdjustCircleUseCase = field(default_factory=LoadAdjustCircleUseCase)
    update_adjust_circle: UpdateAdjustCircleUseCase = field(default_factory=UpdateAdjustCircleUseCase)
    apply_adjust_circle: ApplyAdjustCircleUseCase = field(default_factory=ApplyAdjustCircleUseCase)

    @property
    def load(self) -> LoadAdjustCircleUseCase:
        return self.load_adjust_circle

    @property
    def update(self) -> UpdateAdjustCircleUseCase:
        return self.update_adjust_circle

    @property
    def apply(self) -> ApplyAdjustCircleUseCase:
        return self.apply_adjust_circle