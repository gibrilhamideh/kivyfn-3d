# kivyfn/three/lights/registry.py

from __future__ import annotations
from typing import TYPE_CHECKING

from collections import defaultdict
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from kivyfn.three.lights.shadow import LightShadow
    from kivyfn.three.lights.sources.base import Light3D


@dataclass(slots=True)
class LightRecord:
    light: Light3D
    shadow: LightShadow | None = None
    tags: set[str] = field(default_factory=set)


class LightRegistry:

    def __init__(self) -> None:
        self._records: dict[str, LightRecord] = {}
        self._tags: defaultdict[str, set[str]] = defaultdict(set)

    def __len__(self) -> int:
        return len(self._records)

    # =================================== #
    # Registry API
    # =================================== #

    def add(
        self,
        light: Light3D,
        tags: set[str] | None = None,
    ) -> LightRecord:
        name = light.name

        if name in self._records:
            raise ValueError(
                f"Light {name!r} is already registered."
            )

        record = LightRecord(
            light=light,
            tags=set(tags or ()),
        )

        self._records[name] = record

        for tag in record.tags:
            self._tags[tag].add(name)

        return record

    def remove(
        self,
        name: str,
    ) -> LightRecord:
        record = self.require(name)

        del self._records[name]

        for tag in record.tags:
            self._tags[tag].discard(name)

            if not self._tags[tag]:
                del self._tags[tag]

        return record

    def get(
        self,
        name: str,
    ) -> LightRecord | None:
        return self._records.get(name)

    def require(
        self,
        name: str,
    ) -> LightRecord:
        record = self.get(name)

        if record is None:
            raise ValueError(
                f"Light {name!r} is not registered."
            )

        return record

    def values(self) -> list[LightRecord]:
        return list(self._records.values())

    # =================================== #
    # Tags
    # =================================== #

    def add_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        record = self.require(name)

        if tag in record.tags:
            return

        record.tags.add(tag)
        self._tags[tag].add(name)

    def remove_tag(
        self,
        name: str,
        tag: str,
    ) -> None:
        record = self.require(name)

        if tag not in record.tags:
            return

        record.tags.remove(tag)
        self._tags[tag].discard(name)

        if not self._tags[tag]:
            del self._tags[tag]

    def get_by_tag(
        self,
        tag: str,
    ) -> list[LightRecord]:
        return [
            self._records[name]
            for name in self._tags.get(tag, ())
        ]
