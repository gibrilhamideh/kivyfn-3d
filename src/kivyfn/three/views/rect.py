# kivyfn/three/views/rect.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ViewRect:
    x: float
    y: float
    width: float
    height: float

    @property
    def aspect(self) -> float:
        if self.width <= 0 or self.height <= 0:
            raise RuntimeError(
                "Cannot calculate view rect aspect because "
                f"size is invalid: {self.width}x{self.height}."
            )

        return self.width / self.height
