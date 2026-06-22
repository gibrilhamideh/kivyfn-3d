# kivyfn/three/render/binder_manager.py

from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias, Literal

from dataclasses import dataclass
from functools import partial
from collections import defaultdict
from collections.abc import Callable

from kivy.graphics import BindTexture
from kivy.graphics.texture import Texture

from kivyfn.three.render.registry import RenderStageRegistry

if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderPass, RenderContext


RenderStage: TypeAlias = "RenderPass | RenderContext"

RenderPassOutput = Literal[
    "color",
    "depth",
    "normal",
    "position",
    "emissive",
    "material",
    "id",
]


RENDER_PASS_TEXTURE_START_SLOT = 10

@dataclass(slots=True)
class RenderTextureBinding:
    record: RenderBindingRecord
    instruction: BindTexture
    callback: Callable


class RenderBinderManager:

    def __init__(
        self,
        *,
        stage_registry: RenderStageRegistry,
        binder_registry: RenderBindingRegistry,
    ) -> None:
        self._stage_registry = stage_registry
        self._binder_registry = binder_registry

        self._texture_bindings: dict[RenderBindingRecord, RenderTextureBinding] = {}

    def attach(
        self,
        *,
        pass_name: str,
        target_name: str,
        index: int | None = None,
    ) -> RenderBindingRecord:
        render_pass = self._stage_registry.require_pass(pass_name)
        target = self._stage_registry.require(target_name)

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
        record: RenderBindingRecord,
    ) -> RenderTextureBinding:
        texture_binding = self._texture_bindings.pop(record)
        return texture_binding


    def _attach_texture_binding(
        self,
        *,
        record: RenderBindingRecord,
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


@dataclass(slots=True, frozen=True)
class RenderBindingRecord:
    source: str
    target: str
    index: int


class RenderBindingRegistry:

    def __init__(self, registry: RenderStageRegistry) -> None:
        self.registry = registry
        self._records: set[RenderBindingRecord] = set()
        self._outgoing: defaultdict[str, set[RenderBindingRecord]] = defaultdict(set)
        self._incoming: defaultdict[str, set[RenderBindingRecord]] = defaultdict(set)

    # =================================== #
    # Registry API
    # =================================== #
    def add(
        self,
        source: str,
        target: str,
        *,
        index: int,
    ) -> RenderBindingRecord:
        self.registry.require(source)
        self.registry.require(target)

        if source == target:
            raise ValueError("A render stage cannot bind to itself.")

        record = RenderBindingRecord(
            source=source,
            target=target,
            index=index,
        )

        if record in self._records:
            return record

        self._records.add(record)
        self._outgoing[source].add(record)
        self._incoming[target].add(record)

        return record

    def remove(
        self,
        record: RenderBindingRecord,
    ) -> RenderBindingRecord:
        if record not in self._records:
            raise KeyError(
                f"Render binder '{record.source}' -> "
                f"'{record.target}' is not registered."
            )

        self._records.remove(record)

        self._outgoing[record.source].discard(record)
        if not self._outgoing[record.source]:
            del self._outgoing[record.source]

        self._incoming[record.target].discard(record)
        if not self._incoming[record.target]:
            del self._incoming[record.target]

        return record

    def outgoing(
        self,
        source: str,
    ) -> set[RenderBindingRecord] | None:
        records = self._outgoing.get(source)

        if not records:
            return None

        return set(records)

    def incoming(
        self,
        target: str,
    ) -> set[RenderBindingRecord] | None:
        records = self._incoming.get(target)

        if not records:
            return None

        return set(records)


    def has_outgoing(
        self,
        source: str,
    ) -> bool:
        return source in self._outgoing

    def has_incoming(
        self,
        target: str,
    ) -> bool:
        return target in self._incoming


    # =================================== #
    # Dependencies API
    # =================================== #
    def dependents(
        self,
        source: str,
    ) -> set[str] | None:
        records = self._outgoing.get(source)

        if not records:
            return None

        return {
            record.target
            for record in records
        }

    def dependencies(
        self,
        target: str,
    ) -> set[str] | None:
        records = self._incoming.get(target)

        if not records:
            return None

        return {
            record.source
            for record in records
        }

    def has_dependency(
        self,
        name: str,
    ) -> bool:
        return self.has_outgoing(name)

    def require_no_dependents(
        self,
        name: str,
    ) -> None:
        dependents = self.dependents(name)

        if dependents is None:
            return

        dependents_text = ", ".join(sorted(dependents))

        raise RuntimeError(
            f"Cannot destroy render stage '{name}' because it is "
            f"required by: {dependents_text}."
        )
