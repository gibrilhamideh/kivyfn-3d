# kivyfn/three/render/material.py

from __future__ import annotations

from typing import Any

from kivy.event import EventDispatcher
from kivy.properties import ColorProperty, DictProperty, ObjectProperty, StringProperty

from kivyfn.three.render.shader import Shader


class Material(EventDispatcher):
    name = StringProperty("")
    color = ColorProperty([1.0, 0.0, 0.0, 1.0])
    texture = ObjectProperty(None, allownone=True)

    # Optional override shader.
    # If None, renderer should use scene.default_shader.
    shader = ObjectProperty(None, allownone=True)

    # Per-object / per-material values.
    uniforms = DictProperty({})

    def __repr__(self) -> str:
        return (
            f"Material("
            f"name={self.name!r}, "
            f"color={list(self.color)}, "
            f"texture={self.texture is not None}, "
            f"shader={self.shader!r}, "
            f"uniforms={len(self.uniforms)}"
            f")"
        )

    def __init__(
        self,
        name: str = "",
        color=None,
        texture=None,
        shader: Shader | None = None,
        uniforms: dict[str, Any] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.name = name

        if color is not None:
            self.color = color

        self.texture = texture

        if shader is not None:
            self.shader = shader

        if uniforms is not None:
            self.uniforms = dict(uniforms)

        self._sync_color_uniform()

    def _sync_color_uniform(self) -> None:
        self.uniforms["object_color"] = list(self.color)

    def set_uniform(self, name: str, value: Any) -> None:
        self.uniforms[name] = value

    def remove_uniform(self, name: str) -> None:
        self.uniforms.pop(name, None)

    def clear_uniforms(self) -> None:
        self.uniforms.clear()
        self._sync_color_uniform()

    def apply_to(self, render_ctx) -> None:
        """
        Apply material/object-level values only.

        This should NOT activate/change shader programs.
        The renderer decides which shader is active.
        """

        self._sync_color_uniform()

        for name, value in self.uniforms.items():
            render_ctx[name] = value

        if self.texture is not None:
            render_ctx["texture0"] = self.texture


    def on_color(self, instance, value) -> None:
        self._sync_color_uniform()


