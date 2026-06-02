# kivyfn/three/render/binder_manager.py

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Callable

from kivy.graphics import BindTexture
from kivy.graphics.texture import Texture

from kivyfn.three.render.context import RenderContext, RenderPass
from kivyfn.three.render.context_registry import RenderRegistry
from kivyfn.three.render.binder_registry import RenderBinderRecord, RenderBinderRegistry


RENDER_PASS_TEXTURE_START_SLOT = 10


@dataclass(slots=True)
class RenderTextureBinding:
    record: RenderBinderRecord
    instruction: BindTexture | None = None
    callback: Callable | None = None


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
        render_pass = self._require_pass(pass_name)
        target = self._require_context(target_name)

        if index is None:
            index = self._next_texture_slot(target_name)

        record = self._binder_registry.add(
            source=pass_name,
            target=target_name,
            index=index,
        )

        if record in self._texture_bindings:
            return record

        texture_binding = RenderTextureBinding(record=record)

        self._texture_bindings[record] = texture_binding

        self._attach_texture_binding(
            texture_binding=texture_binding,
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

    def texture_bindings(self) -> list[RenderTextureBinding]:
        return list(self._texture_bindings.values())

    def texture_binding_for(
        self,
        record: RenderBinderRecord,
    ) -> RenderTextureBinding | None:
        return self._texture_bindings.get(record)

    def texture_bindings_for_target(
        self,
        target_name: str,
    ) -> list[RenderTextureBinding]:
        records = self._binder_registry.incoming(target_name)

        if not records:
            return []

        return [
            texture_binding
            for record in records
            if (texture_binding := self._texture_bindings.get(record)) is not None
        ]

    def texture_bindings_for_source(
        self,
        source_name: str,
    ) -> list[RenderTextureBinding]:
        records = self._binder_registry.outgoing(source_name)

        if not records:
            return []

        return [
            texture_binding
            for record in records
            if (texture_binding := self._texture_bindings.get(record)) is not None
        ]

    def _require_context(
        self,
        name: str,
    ) -> RenderContext:
        stage = self._context_registry.require(name)

        if not isinstance(stage, RenderContext):
            raise TypeError(
                f"Render stage '{name}' is not a RenderContext."
            )

        return stage

    def _require_pass(
        self,
        name: str,
    ) -> RenderPass:
        stage = self._context_registry.require(name)

        if not isinstance(stage, RenderPass):
            raise TypeError(
                f"Render stage '{name}' is not a RenderPass."
            )

        return stage

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

    def _attach_texture_binding(
        self,
        *,
        texture_binding: RenderTextureBinding,
        render_pass: RenderPass,
        target: RenderContext,
    ) -> None:
        if texture_binding.instruction is not None:
            return

        callback = partial(
            self._update_texture,
            texture_binding,
            target,
        )

        render_pass.bind(
            texture_ref=callback,
        )

        texture_binding.callback = callback

    def _update_texture(
        self,
        texture_binding: RenderTextureBinding,
        target: RenderContext,
        render_pass: RenderPass,
        texture: Texture,
    ) -> None:
        if texture_binding.instruction is None:
            return

        texture_binding.instruction.texture = texture
        target.ctx.ask_update()
