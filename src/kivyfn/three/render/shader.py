# kivyfn/three/render/shader.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from kivy.event import EventDispatcher
from kivy.properties import DictProperty, ObjectProperty


class Shader(EventDispatcher):
    path = ObjectProperty(None, allownone=True)
    uniforms = DictProperty({})

    def __init__(
        self,
        path: Path | None = None,
        uniforms: dict[str, Any] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if path is not None:
            self.path = Path(path)

        if uniforms is not None:
            self.uniforms = dict(uniforms)

    def apply_to(self, render_ctx) -> None:
        """
        Apply the shader program and shader-level uniforms.

        Shader uniforms should be scene/pass/global values:
        camera position, light position, projection matrix, etc.
        """
        source = str(self.path) if self.path is not None else None

        if source is not None and render_ctx.shader.source != source:
            render_ctx.shader.source = source

        for name, value in self.uniforms.items():
            render_ctx[name] = value

    def set_uniform(self, name: str, value: Any) -> None:
        self.uniforms[name] = value

    def remove_uniform(self, name: str) -> None:
        self.uniforms.pop(name, None)

    def clear_uniforms(self) -> None:
        self.uniforms.clear()

    def reload(self) -> None:
        """
        Re-apply/reload support can be added later by the renderer.
        For now this exists as API placeholder.
        """
        pass

    def __repr__(self) -> str:
        return (
            f"Shader("
            f"path={self.path!r}, "
            f"uniforms={len(self.uniforms)}"
            f")"
        )
