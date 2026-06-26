# kivyfn/three/render/binder_manager.py

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TypeAlias

from kivyfn.three.graphics.gl import BindTexture
from kivyfn.three.render.context import RenderPass2D, RenderPassCube
from kivyfn.three.render.registry import RenderStageRegistry

RenderPassLike: TypeAlias = "RenderPass2D | RenderPassCube"

RENDER_PASS_TEXTURE_START_SLOT = 10


@dataclass(slots=True, frozen=True)
class RenderBindingGraph:
    target: str
    dependencies: list[str]
    dependents: list[str]


@dataclass(slots=True, frozen=True)
class RenderBindingRecord:
    source: str
    target: str
    index: int


class RenderBinderManager:
    def __init__(
        self,
        *,
        stage_registry: RenderStageRegistry,
        binding_registry: RenderBindingRegistry,
    ) -> None:
        self._stage_registry = stage_registry
        self._binding_registry = binding_registry

        self._texture_bindings: dict[RenderBindingRecord, BindTexture] = {}

    def attach(
        self,
        *,
        pass_name: str,
        target_name: str,
        index: int | None = None,
    ) -> RenderBindingRecord:
        render_pass = self._require_output_stage(pass_name)
        target = self._stage_registry.require(target_name)

        if index is None:
            index = self._next_texture_slot(target_name)

        record = self._binding_registry.add(
            source=pass_name,
            target=target_name,
            index=index,
        )

        instruction = target.bind_texture(
            uniform=render_pass.output_uniform,
            texture=render_pass.texture,
            slot=record.index,
        )

        self._texture_bindings[record] = instruction

        return record

    def detach(
        self,
        record: RenderBindingRecord,
    ) -> BindTexture:
        instruction = self._texture_bindings.pop(record)

        target = self._stage_registry.require(record.target)
        target.texture_group.remove(instruction)
        target.ask_update()

        return instruction

    def _next_texture_slot(
        self,
        target_name: str,
    ) -> int:
        used_slots = {
            record.index
            for record in self._binding_registry.incoming(target_name) or ()
        }

        index = RENDER_PASS_TEXTURE_START_SLOT

        while index in used_slots:
            index += 1

        return index

    def _require_output_stage(
        self,
        name: str,
    ) -> RenderPassLike:
        stage = self._stage_registry.require(name)

        if not isinstance(stage, (RenderPass2D, RenderPassCube)):
            raise TypeError(
                f"Render stage {name!r} is not attachable as an output stage."
            )

        return stage



class RenderBindingRegistry:
    def __init__(
        self,
        registry: RenderStageRegistry,
    ) -> None:
        self._registry = registry
        self._records: set[RenderBindingRecord] = set()
        self._outgoing: defaultdict[str, set[RenderBindingRecord]] = defaultdict(set)
        self._incoming: defaultdict[str, set[RenderBindingRecord]] = defaultdict(set)
        self._links: set[tuple[str, str]] = set()

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
        self._registry.require(source)
        self._registry.require(target)

        if source == target:
            raise ValueError(
                "A render stage cannot bind to itself."
            )

        link = (
            source,
            target,
        )

        if link in self._links:
            raise ValueError(
                f"Render pass {source!r} is already attached "
                f"to render stage {target!r}."
            )

        record = RenderBindingRecord(
            source=source,
            target=target,
            index=index,
        )

        self._records.add(record)
        self._links.add(link)
        self._outgoing[source].add(record)
        self._incoming[target].add(record)

        return record

    def remove(
        self,
        record: RenderBindingRecord,
    ) -> RenderBindingRecord:
        if record not in self._records:
            raise KeyError(
                f"Render binder {record.source!r} -> "
                f"{record.target!r} is not registered."
            )

        self._records.remove(record)
        self._links.discard(
            (
                record.source,
                record.target,
            )
        )

        self._outgoing[record.source].discard(record)
        if not self._outgoing[record.source]:
            del self._outgoing[record.source]

        self._incoming[record.target].discard(record)
        if not self._incoming[record.target]:
            del self._incoming[record.target]

        return record

    def outgoing(
        self,
        name: str,
    ) -> set[RenderBindingRecord] | None:
        records = self._outgoing.get(name)

        if not records:
            return None

        return set(records)

    def incoming(
        self,
        name: str,
    ) -> set[RenderBindingRecord] | None:
        records = self._incoming.get(name)

        if not records:
            return None

        return set(records)

    def has_outgoing(
        self,
        name: str,
    ) -> bool:
        return name in self._outgoing

    def has_incoming(
        self,
        name: str,
    ) -> bool:
        return name in self._incoming

    # =================================== #
    # Dependencies API
    # =================================== #
    def dependents_of(
        self,
        name: str,
    ) -> set[str]:
        records = self._outgoing.get(name)

        if not records:
            return set()

        return {
            record.target
            for record in records
        }

    def dependencies_of(
        self,
        name: str,
    ) -> set[str]:
        records = self._incoming.get(name)

        if not records:
            return set()

        return {
            record.source
            for record in records
        }

    def graph_of(
        self,
        name: str,
    ) -> RenderBindingGraph:
        self._registry.require(name)

        return RenderBindingGraph(
            target=name,
            dependencies=self._walk_graph(
                name,
                next_of=self.dependencies_of,
            ),
            dependents=self._walk_graph(
                name,
                next_of=self.dependents_of,
            ),
        )

    def _walk_graph(
        self,
        name: str,
        *,
        next_of,
    ) -> list[str]:
        visited: set[str] = {
            name,
        }
        result: list[str] = []
        current: set[str] = {
            name,
        }

        while current:
            next_level: set[str] = set()

            for stage_name in current:
                for next_name in next_of(stage_name):
                    if next_name in visited:
                        continue

                    visited.add(next_name)
                    next_level.add(next_name)

            if not next_level:
                break

            result.extend(next_level)
            current = next_level

        return result



