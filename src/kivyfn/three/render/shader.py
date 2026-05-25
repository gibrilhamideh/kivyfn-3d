# kivyfn/three/render/shader.py

from __future__ import annotations

from pathlib import Path

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, StringProperty


# TODO: ADD observable file for shader to get event on shader change for hot reload
class Shader(EventDispatcher):
    name = StringProperty("")
    path = ObjectProperty(None, allownone=True)

    def __init__(
        self,
        path: str | Path | None = None,
        name: str = "",
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.name = name

        if path is not None:
            self.path = Path(path)

    def reload(self) -> None:
        pass

    def __repr__(self) -> str:
        return (
            f"Shader("
            f"name={self.name!r}, "
            f"path={self.path!r}"
            f")"
        )
