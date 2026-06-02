# kivyfn/three/render/binder_manager.py

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Callable

from kivy.graphics import BindTexture
from kivy.graphics.texture import Texture

from kivyfn.three.types import RenderStage
from kivyfn.three.render.context import RenderPass
from kivyfn.three.render.context_registry import RenderRegistry
from kivyfn.three.render.binder_registry import RenderBinderRecord, RenderBinderRegistry


RENDER_PASS_TEXTURE_START_SLOT = 10


@dataclass(slots=True)
class RenderTextureBinding:
    record: RenderBinderRecord
    instruction: BindTexture
    callback: Callable


class RenderBinderManager:

    def __init__(
        self,
        *,
        context_registry: RenderRegistry,
        binder_registry: RenderBinderRegistry,
    ) -> None:
        self._context_registry = context_registry
        self._binder_registry = binder_registry

        self._texture_bindings: dict[RenderBinderRecord, RenderTextureBinding] = {}

    def attach(
        self,
        *,
        pass_name: str,
        target_name: str,
        index: int | None = None,
    ) -> RenderBinderRecord:
        render_pass = self._context_registry.require_pass(pass_name)
        target = self._context_registry.require(target_name)

        if index is None:
            index = self._next_texture_slot(target_name)

        record = self._binder_registry.add(
            source=pass_name,
            target=target_name,
            index=index,
        )

        self._attach_texture_binding(
            record=record,
            render_pass=render_pass,
            target=target,
        )

        return record

    def detach(
        self,
        record: RenderBinderRecord,
    ) -> RenderTextureBinding:
        texture_binding = self._texture_bindings.pop(record)
        return texture_binding


    def _attach_texture_binding(
        self,
        *,
        record: RenderBinderRecord,
        render_pass: RenderPass,
        target: RenderStage,
    ) -> None:

        instruction = target.create_texture_binder(
            output_uniform=render_pass.output_uniform,
            texture=render_pass.texture,
            slot=record.index,
        )

        callback = partial(
            self._update_texture,
            instruction,
            target
        )

        render_pass.bind(texture_ref=callback)

        self._texture_bindings[record] = RenderTextureBinding(
            record=record,
            instruction=instruction,
            callback=callback
        )



    def _update_texture(
        self,
        instruction: BindTexture,
        target: RenderStage,
        render_pass: RenderPass,
        texture: Texture,
    ) -> None:
        instruction.texture = texture

    def _next_texture_slot(
        self,
        target_name: str,
    ) -> int:
        used_slots = {
            record.index
            for record in self._binder_registry.incoming(target_name) or ()
        }

        index = RENDER_PASS_TEXTURE_START_SLOT

        while index in used_slots:
            index += 1

        return index
