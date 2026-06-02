# kivyfn/three/render/binder_registry.py

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from kivyfn.three.render.context_registry import RenderRegistry


@dataclass(slots=True, frozen=True)
class RenderBinderRecord:
    source: str
    target: str
    index: int


class RenderBinderRegistry:

    def __init__(self, registry: RenderRegistry) -> None:
        self.registry = registry
        self._binders: set[RenderBinderRecord] = set()
        self._outgoing: defaultdict[str, set[RenderBinderRecord]] = defaultdict(set)
        self._incoming: defaultdict[str, set[RenderBinderRecord]] = defaultdict(set)

    # =================================== #
    # Registry API
    # =================================== #
    def add(
        self,
        source: str,
        target: str,
        *,
        index: int,
    ) -> RenderBinderRecord:
        self.registry.require(source)
        self.registry.require(target)

        if source == target:
            raise ValueError("A render stage cannot bind to itself.")

        record = RenderBinderRecord(
            source=source,
            target=target,
            index=index,
        )

        if record in self._binders:
            return record

        self._binders.add(record)
        self._outgoing[source].add(record)
        self._incoming[target].add(record)

        return record

    def remove(
        self,
        record: RenderBinderRecord,
    ) -> RenderBinderRecord:
        if record not in self._binders:
            raise KeyError(
                f"Render binder '{record.source}' -> "
                f"'{record.target}' is not registered."
            )

        self._binders.remove(record)

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
    ) -> set[RenderBinderRecord] | None:
        records = self._outgoing.get(source)

        if not records:
            return None

        return set(records)

    def incoming(
        self,
        target: str,
    ) -> set[RenderBinderRecord] | None:
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
