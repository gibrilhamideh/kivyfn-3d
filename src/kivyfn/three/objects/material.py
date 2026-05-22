# kivyfn/three/render/material.py

from __future__ import annotations

from typing import Any

from kivy.event import EventDispatcher
from kivy.properties import DictProperty, StringProperty


class Material(EventDispatcher):
    name = StringProperty("")
    uniforms = DictProperty({})

    def __repr__(self) -> str:
        uniforms = ", ".join(
            f"{k}={v!r}"
            for k, v in self.uniforms.items()
        )

        return (
            f"Material("
            f"name={self.name!r}, "
            f"{uniforms}"
            f")"
        )

    def __init__(
        self,
        name: str = "",
        uniforms: dict[str, Any] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.name = name
        if uniforms is not None:
            self.uniforms = dict(uniforms)

    def set_uniform(self, name: str, value: Any) -> None:
        self.uniforms[name] = value

    def remove_uniform(self, name: str) -> None:
        self.uniforms.pop(name, None)

    def clear_uniforms(self) -> None:
        self.uniforms.clear()


