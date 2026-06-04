# kivyfn/three/lights/sources/base.py

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty

from kivyfn.three.graph.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three.lights.template import LightConfig


LightKind = Literal["light"]


class Light3D(Node3D):

    color: list[float] = ListProperty([1.0, 0.95, 0.8])
    intensity: float = NumericProperty(1.0)
    enabled: bool = BooleanProperty(True)

    config: LightConfig = ObjectProperty()

    def __init__(
        self,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.register_event_type("on_light_dirty")  # pyright: ignore

        self.bind(
            color=self.mark_light_dirty,
            intensity=self.mark_light_dirty,
            enabled=self.mark_light_dirty,
            config=self.mark_light_dirty,
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(\n"
            f"    name={self.name!r},\n"
            f"    color={tuple(self.color)},\n"
            f"    intensity={self.intensity},\n"
            f"    enabled={self.enabled},\n"
            f"    config={self.config!r},\n"
            ")"
        )

    @property
    def kind(self) -> LightKind:
        return "light"

    def set_config(
        self,
        config: LightConfig,
    ) -> None:
        self.config = config
        self.mark_light_dirty()

    def mark_light_dirty(self, *_) -> None:
        self.dispatch("on_light_dirty")

    def on_light_dirty(self) -> None:
        pass


