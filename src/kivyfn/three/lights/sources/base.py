# kivyfn/three/lights/sources/base.py

from __future__ import annotations

from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivyfn.three.graph.node import Node3D

class Light3D(Node3D):

    color: list[float] = ListProperty([1.0, 0.95, 0.8])
    intensity: float = NumericProperty(1.0)
    enabled: bool = BooleanProperty(True)

    def __init__(
        self,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.register_event_type("on_light_dirty") # pyright: ignore

        self.bind(
            color=self.mark_light_dirty,
            intensity=self.mark_light_dirty,
            enabled=self.mark_light_dirty,
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(\n"
            f"    name={self.name!r},\n"
            f"    color={tuple(self.color)},\n"
            f"    intensity={self.intensity},\n"
            f"    enabled={self.enabled},\n"
            ")"
        )

    def mark_light_dirty(self, *_) -> None:
        self.dispatch("on_light_dirty")

    def on_light_dirty(self) -> None:
        pass


