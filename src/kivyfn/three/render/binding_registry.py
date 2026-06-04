# kivyfn/three/render/binding_registry.py

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from kivyfn.three.render.stage_registry import RenderStageRegistry


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
