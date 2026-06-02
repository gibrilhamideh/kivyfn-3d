# kivyfn/three/render/link_registry.py

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from kivyfn.three.render.context_registry import RenderRegistry


@dataclass(slots=True, frozen=True)
class RenderLinkRecord:
    source: str
    target: str


class RenderLinkRegistry:

    def __init__(self, registry: RenderRegistry) -> None:
        self.registry = registry
        self._links: set[RenderLinkRecord] = set()
        self._outgoing: defaultdict[str, set[RenderLinkRecord]] = defaultdict(set)
        self._incoming: defaultdict[str, set[RenderLinkRecord]] = defaultdict(set)

    # =================================== #
    # Registry API
    # =================================== #
    def add(
        self,
        source: str,
        target: str,
    ) -> RenderLinkRecord:
        self.registry.require(source)
        self.registry.require(target)

        if source == target:
            raise ValueError("A render stage cannot link to itself.")

        record = RenderLinkRecord(
            source=source,
            target=target,
        )

        if record in self._links:
            return record

        self._links.add(record)
        self._outgoing[source].add(record)
        self._incoming[target].add(record)

        return record

    def remove(
        self,
        source: str,
        target: str,
    ) -> RenderLinkRecord:
        return self.unlink(
            RenderLinkRecord(
                source=source,
                target=target,
            )
        )

    def unlink(
        self,
        record: RenderLinkRecord,
    ) -> RenderLinkRecord:
        if record not in self._links:
            raise KeyError(
                f"Render link '{record.source}' -> '{record.target}' is not registered."
            )

        self._links.remove(record)

        self._outgoing[record.source].discard(record)
        if not self._outgoing[record.source]:
            del self._outgoing[record.source]

        self._incoming[record.target].discard(record)
        if not self._incoming[record.target]:
            del self._incoming[record.target]

        return record

    def unlink_by_source(
        self,
        source: str,
    ) -> set[RenderLinkRecord]:
        records = set(self._outgoing.get(source, set()))

        for record in records:
            self.unlink(record)

        return records

    def unlink_by_target(
        self,
        target: str,
    ) -> set[RenderLinkRecord]:
        records = set(self._incoming.get(target, set()))

        for record in records:
            self.unlink(record)

        return records

    def outgoing(
        self,
        source: str,
    ) -> set[RenderLinkRecord] | None:
        records = self._outgoing.get(source)

        if not records:
            return None

        return set(records)

    def incoming(
        self,
        target: str,
    ) -> set[RenderLinkRecord] | None:
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

    def dependents(
        self,
        source: str,
    ) -> set[str]:
        records = self._outgoing.get(source)

        if not records:
            return set()

        return {
            record.target
            for record in records
        }

    def dependencies(
        self,
        target: str,
    ) -> set[str]:
        records = self._incoming.get(target)

        if not records:
            return set()

        return {
            record.source
            for record in records
        }

    def require_no_dependents(
        self,
        source: str,
    ) -> None:
        dependents = self.dependents(source)

        if not dependents:
            return

        dependents_text = ", ".join(sorted(dependents))

        raise RuntimeError(
            f"Cannot destroy render stage '{source}' because it has "
            f"linked dependents: {dependents_text}."
        )
