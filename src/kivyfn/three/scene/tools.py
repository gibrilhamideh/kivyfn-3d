# kivyfn/three/scene/tools.py

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any, Literal

from kivy.core.window import Window
from kivy.clock import Clock, ClockEvent
from kivy.graphics import (
    Color,
    InstructionGroup,
    Mesh,
    Rectangle,
    RenderContext,
)
from kivy.uix.label import Label

from kivyfn.three.graphics.gl.context import (
    BindTexture,
    BindUniform,
)
from kivyfn.three.graphics.gl.texture import Texture2D, TextureCube
from kivyfn.three.meshes.quad import Quad
from kivyfn.three.paths import THREE_SHADER_PATH
from kivyfn.three.render.config import TEXTURE_SLOTS
from kivyfn.three.render.shader import Shader
from kivyfn.three.views.rect import ViewRect


if TYPE_CHECKING:
    from kivyfn.three import Scene


TexturePreviewKind = Literal[
    "texture-2d",
    "texture-cube",
]

PreviewAnchor = Literal[
    "bottom-left",
    "bottom-right",
    "top-left",
    "top-right",
]


@dataclass(slots=True)
class TexturePreview:
    name: str
    kind: TexturePreviewKind
    context: RenderContext
    group: InstructionGroup
    mesh: Mesh
    bind_texture: BindTexture
    uniforms: dict[str, BindUniform]
    rect: ViewRect
    size: tuple[int, int]
    pos: tuple[int, int] | None
    anchor: PreviewAnchor
    auto_pos: bool


@dataclass(slots=True)
class FpsDisplay:
    color: Color
    rect: Rectangle
    label: Label
    event: ClockEvent


class SceneTools:
    def __init__(
        self,
        scene: Scene,
    ) -> None:
        self.scene = scene

        self._previews: dict[str, TexturePreview] = {}
        self._fps_display: FpsDisplay | None = None

        self._layout_trigger = Clock.create_trigger(
            self._layout_previews,
            0,
        )

        self.scene.scene_viewport.bind(
            on_dirty=self._schedule_layout,
        )

        Window.bind(
            size=self._schedule_layout,
        )

        self.cube_preview_shader = Shader(
            name="cube",
            directory=THREE_SHADER_PATH / "previews" / "cube",
        )

        self.texture_preview_shader = Shader(
            name="texture2d",
            directory=THREE_SHADER_PATH / "previews" / "texture2d",
        )

    # =================================== #
    # Render Context
    # =================================== #

    def _make_render_context(
        self,
        shader: Shader,
    ) -> RenderContext:
        return RenderContext(
            use_parent_projection=False,
            use_parent_modelview=False,
            vs=shader.vertex_source,
            fs=shader.fragment_source,
        )

    # =================================== #
    # Texture Preview Public API
    # =================================== #

    def display_stage(
        self,
        stage: str,
        *,
        name: str | None = None,
        pos: tuple[int, int] | None = None,
        size: tuple[int, int] | None = None,
        anchor: PreviewAnchor = "bottom-left",
        slot: int | None = None,
    ) -> TexturePreview:
        render_stage = self.scene.stages.registry.require(
            stage,
        )

        texture = self._stage_texture(
            render_stage,
        )

        uniforms: dict[str, Any] = {}

        if isinstance(texture, TextureCube):
            uniforms["shadow_far"] = float(
                getattr(
                    render_stage.view,
                    "far",
                    1.0,
                )
            )

        return self.display_texture(
            texture,
            name=name or f"stage-preview:{stage}",
            pos=pos,
            size=size,
            anchor=anchor,
            slot=slot,
            uniforms=uniforms,
        )

    def display_texture(
        self,
        texture: Texture2D | TextureCube,
        *,
        name: str | None = None,
        pos: tuple[int, int] | None = None,
        size: tuple[int, int] | None = None,
        anchor: PreviewAnchor = "bottom-left",
        slot: int | None = None,
        uniforms: dict[str, Any] | None = None,
        shadow_far: float | None = None,
    ) -> TexturePreview:
        kind = self._texture_kind(
            texture,
        )

        preview_name = name or self._texture_preview_name(
            texture,
        )

        if preview_name in self._previews:
            self.remove_preview(
                preview_name,
            )

        shader = self._preview_shader(
            kind,
        )

        uniform = self._preview_texture_uniform(
            kind,
        )

        texture_slot = self._preview_texture_slot(
            kind,
            slot,
        )

        preview_size = size or self._default_preview_size(
            kind,
        )

        preview_rect = self._preview_rect(
            pos=pos,
            size=preview_size,
            anchor=anchor,
            auto_index=self._auto_preview_count(
                anchor,
            ),
        )

        preview_uniforms = dict(
            uniforms or {},
        )

        if kind == "texture-cube":
            preview_uniforms.setdefault(
                "shadow_far",
                1.0 if shadow_far is None else shadow_far,
            )

        return self._display_texture(
            name=preview_name,
            kind=kind,
            shader=shader,
            texture=texture,
            uniform=uniform,
            slot=texture_slot,
            rect=preview_rect,
            pos=pos,
            size=preview_size,
            anchor=anchor,
            auto_pos=pos is None,
            uniforms=preview_uniforms,
        )

    def update_preview_rect(
        self,
        name: str,
        *,
        pos: tuple[int, int] | None = None,
        size: tuple[int, int] | None = None,
        anchor: PreviewAnchor | None = None,
        auto_pos: bool | None = None,
    ) -> None:
        preview = self._previews[name]

        if pos is not None:
            preview.pos = pos

        if size is not None:
            preview.size = size

        if anchor is not None:
            preview.anchor = anchor

        if auto_pos is not None:
            preview.auto_pos = auto_pos
        elif pos is not None:
            preview.auto_pos = False

        preview.rect = self._preview_rect(
            pos=None if preview.auto_pos else preview.pos,
            size=preview.size,
            anchor=preview.anchor,
            auto_index=self._auto_preview_index(
                preview,
            ),
        )

        self._update_preview_mesh(
            preview,
        )

    def update_preview_uniform(
        self,
        name: str,
        uniform: str,
        value: Any,
    ) -> None:
        preview = self._previews[name]

        binder = preview.uniforms.get(
            uniform,
        )

        if binder is None:
            binder = BindUniform(
                uniform,
                value,
            )

            preview.uniforms[uniform] = binder

            preview.group.remove(
                preview.mesh,
            )
            preview.group.add(
                binder,
            )
            preview.group.add(
                preview.mesh,
            )

            return

        binder.sync(
            value,
        )

    def remove_preview(
        self,
        name: str,
    ) -> None:
        preview = self._previews.pop(
            name,
            None,
        )

        if preview is None:
            return

        self._remove_instruction(
            preview.context,
        )

        preview.group.clear()
        preview.context.clear()

    def clear_previews(
        self,
    ) -> None:
        for name in list(self._previews):
            self.remove_preview(
                name,
            )

    # =================================== #
    # Texture Preview Internal
    # =================================== #

    def _display_texture(
        self,
        *,
        name: str,
        kind: TexturePreviewKind,
        shader: Shader,
        texture: Texture2D | TextureCube,
        uniform: str,
        slot: int,
        rect: ViewRect,
        pos: tuple[int, int] | None,
        size: tuple[int, int],
        anchor: PreviewAnchor,
        auto_pos: bool,
        uniforms: dict[str, Any],
    ) -> TexturePreview:
        context = self._make_render_context(
            shader,
        )

        group = InstructionGroup()

        bind_texture = BindTexture(
            uniform=uniform,
            texture=texture,
            slot=slot,
        )

        group.add(
            bind_texture,
        )

        uniform_binders: dict[str, BindUniform] = {}

        for uniform_name, value in uniforms.items():
            binder = BindUniform(
                uniform_name,
                value,
            )

            uniform_binders[uniform_name] = binder

            group.add(
                binder,
            )

        mesh = Quad.create(
            rect=rect,
            viewport=self._canvas_rect(),
        )

        group.add(
            mesh,
        )

        context.add(
            group,
        )

        self.scene.canvas.after.add(
            context,
        )

        preview = TexturePreview(
            name=name,
            kind=kind,
            context=context,
            group=group,
            mesh=mesh,
            bind_texture=bind_texture,
            uniforms=uniform_binders,
            rect=rect,
            pos=pos,
            size=size,
            anchor=anchor,
            auto_pos=auto_pos,
        )

        self._previews[name] = preview

        return preview

    def _stage_texture(
        self,
        stage: Any,
    ) -> Texture2D | TextureCube:
        if bool(
            getattr(
                stage,
                "is_texture_2d",
                False,
            )
        ):
            return stage.require_target(
                "texture-2d",
            ).texture

        if bool(
            getattr(
                stage,
                "is_texture_cube",
                False,
            )
        ):
            return stage.require_target(
                "texture-cube",
            ).texture

        target = getattr(
            stage,
            "target",
            None,
        )

        texture = getattr(
            target,
            "texture",
            None,
        )

        if isinstance(
            texture,
            (
                Texture2D,
                TextureCube,
            ),
        ):
            return texture

        raise RuntimeError(
            "Cannot display stage preview because the stage target "
            "is not a texture target."
        )

    def _texture_kind(
        self,
        texture: Texture2D | TextureCube,
    ) -> TexturePreviewKind:
        if isinstance(
            texture,
            Texture2D,
        ):
            return "texture-2d"

        if isinstance(
            texture,
            TextureCube,
        ):
            return "texture-cube"

        raise TypeError(
            "Texture preview expected Texture2D or TextureCube, "
            f"not {type(texture).__name__}."
        )

    def _preview_shader(
        self,
        kind: TexturePreviewKind,
    ) -> Shader:
        if kind == "texture-2d":
            return self.texture_preview_shader

        if kind == "texture-cube":
            return self.cube_preview_shader

        raise RuntimeError(
            f"Unknown texture preview kind: {kind!r}"
        )

    def _preview_texture_uniform(
        self,
        kind: TexturePreviewKind,
    ) -> str:
        if kind == "texture-2d":
            return "preview_texture"

        if kind == "texture-cube":
            return "shadow_texture"

        raise RuntimeError(
            f"Unknown texture preview kind: {kind!r}"
        )

    def _preview_texture_slot(
        self,
        kind: TexturePreviewKind,
        slot: int | None,
    ) -> int:
        if slot is not None:
            return slot

        if kind == "texture-2d":
            return TEXTURE_SLOTS.get(
                "preview_texture",
                14,
            )

        if kind == "texture-cube":
            return TEXTURE_SLOTS.get(
                "shadow_texture",
                15,
            )

        raise RuntimeError(
            f"Unknown texture preview kind: {kind!r}"
        )

    def _texture_preview_name(
        self,
        texture: Texture2D | TextureCube,
    ) -> str:
        texture_id = getattr(
            texture,
            "id",
            id(texture),
        )

        return f"texture-preview:{texture_id}"

    def _default_preview_size(
        self,
        kind: TexturePreviewKind,
    ) -> tuple[int, int]:
        if kind == "texture-2d":
            return (
                256,
                256,
            )

        if kind == "texture-cube":
            return (
                384,
                256,
            )

        raise RuntimeError(
            f"Unknown texture preview kind: {kind!r}"
        )

    # =================================== #
    # Layout
    # =================================== #

    def _schedule_layout(
        self,
        *_: Any,
    ) -> None:
        self._layout_trigger()

    def _layout_previews(
        self,
        *_: Any,
    ) -> None:
        auto_indices: dict[PreviewAnchor, int] = {
            "bottom-left": 0,
            "bottom-right": 0,
            "top-left": 0,
            "top-right": 0,
        }

        for preview in self._previews.values():
            if preview.auto_pos:
                index = auto_indices[preview.anchor]

                preview.rect = self._preview_rect(
                    pos=None,
                    size=preview.size,
                    anchor=preview.anchor,
                    auto_index=index,
                )

                auto_indices[preview.anchor] = index + 1

            else:
                preview.rect = self._preview_rect(
                    pos=preview.pos,
                    size=preview.size,
                    anchor=preview.anchor,
                    auto_index=0,
                )

            self._update_preview_mesh(
                preview,
            )

    def _update_preview_mesh(
        self,
        preview: TexturePreview,
    ) -> None:
        Quad.update(
            preview.mesh,
            rect=preview.rect,
            viewport=self._canvas_rect(),
        )

    def _preview_rect(
        self,
        *,
        pos: tuple[int, int] | None,
        size: tuple[int, int],
        anchor: PreviewAnchor,
        auto_index: int,
    ) -> ViewRect:
        width, height = size

        if pos is not None:
            x, y = pos

            return ViewRect(
                x=self.scene.scene_viewport.x + float(x),
                y=self.scene.scene_viewport.y + float(y),
                width=float(width),
                height=float(height),
            )

        return self._auto_preview_rect(
            size=size,
            anchor=anchor,
            index=auto_index,
        )

    def _canvas_rect(
        self,
    ) -> ViewRect:
        return ViewRect(
            x=0.0,
            y=0.0,
            width=float(Window.width),
            height=float(Window.height),
        )

    def _auto_preview_rect(
        self,
        *,
        size: tuple[int, int],
        anchor: PreviewAnchor,
        index: int,
    ) -> ViewRect:
        width, height = size

        margin = 20.0
        gap = 12.0

        viewport = self.scene.scene_viewport.rect

        if anchor == "bottom-left":
            x = viewport.x + margin
            y = viewport.y + margin + index * (height + gap)

        elif anchor == "bottom-right":
            x = viewport.x + viewport.width - margin - width
            y = viewport.y + margin + index * (height + gap)

        elif anchor == "top-left":
            x = viewport.x + margin
            y = viewport.y + viewport.height - margin - height
            y -= index * (height + gap)

        elif anchor == "top-right":
            x = viewport.x + viewport.width - margin - width
            y = viewport.y + viewport.height - margin - height
            y -= index * (height + gap)

        else:
            raise RuntimeError(
                f"Unknown preview anchor: {anchor!r}"
            )

        return ViewRect(
            x=float(x),
            y=float(y),
            width=float(width),
            height=float(height),
        )

    def _auto_preview_count(
        self,
        anchor: PreviewAnchor,
    ) -> int:
        count = 0

        for preview in self._previews.values():
            if not preview.auto_pos:
                continue

            if preview.anchor != anchor:
                continue

            count += 1

        return count

    def _auto_preview_index(
        self,
        preview: TexturePreview,
    ) -> int:
        index = 0

        for other in self._previews.values():
            if other is preview:
                return index

            if not other.auto_pos:
                continue

            if other.anchor != preview.anchor:
                continue

            index += 1

        return index

    # =================================== #
    # FPS / Frame Time
    # =================================== #

    def display_fps(
        self,
        *,
        pos: tuple[int, int] = (20, 20),
        font_size: int = 16,
        interval: float = 1.0,
    ) -> FpsDisplay:
        if self._fps_display is not None:
            return self._fps_display

        label = Label(
            text="FPS: --\nFrame: -- ms",
            font_size=font_size,
            size_hint=(None, None),
        )

        label.texture_update()
        label.width = label.texture_size[0]
        label.height = label.texture_size[1]

        with self.scene.canvas.after:
            color = Color(
                1.0,
                1.0,
                1.0,
                1.0,
            )

            rect = Rectangle(
                pos=pos,
                size=label.size,
                texture=label.texture,
            )

        event = Clock.schedule_interval(
            partial(
                self._update_fps_display,
                label,
                rect,
            ),
            interval,
        )

        display = FpsDisplay(
            color=color,
            rect=rect,
            label=label,
            event=event,
        )

        self._fps_display = display

        return display

    def remove_fps(
        self,
    ) -> None:
        if self._fps_display is None:
            return

        self._fps_display.event.cancel()

        self._remove_instruction(
            self._fps_display.color,
        )
        self._remove_instruction(
            self._fps_display.rect,
        )

        self._fps_display = None

    def _update_fps_display(
        self,
        label: Label,
        rect: Rectangle,
        dt: float,
    ) -> None:
        _ = dt

        frame_ms = Clock.frametime * 1000.0

        label.text = (
            f"FPS: {Clock.get_fps():.1f}\n"
            f"Frame: {frame_ms:.2f} ms"
        )

        label.texture_update()
        rect.texture = label.texture
        rect.size = label.size

    # =================================== #
    # Cleanup
    # =================================== #

    def clear(
        self,
    ) -> None:
        self.clear_previews()
        self.remove_fps()

    def _remove_instruction(
        self,
        instruction,
    ) -> None:
        canvas = self.scene.canvas.after

        if instruction in canvas.children:
            canvas.remove(
                instruction,
            )
