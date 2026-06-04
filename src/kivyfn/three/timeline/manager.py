# kivyfn/three/scene/timeline/manager.py

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from kivy.event import EventDispatcher


if TYPE_CHECKING:
    from kivyfn.three.timeline import Timeline


DEFAULT_GROUP = "default"


class TimelineManager(EventDispatcher):
    def __init__(
        self,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.groups: dict[str, list[Timeline]] = {}

    # =================================== #
    # Add / Remove
    # =================================== #

    def add(
        self,
        timeline: Timeline,
        *,
        group: str = DEFAULT_GROUP,
    ) -> Timeline:
        items = self.groups.setdefault(group, [])

        if timeline not in items:
            items.append(timeline)

        return timeline

    def remove(
        self,
        timeline: Timeline,
        *,
        stop: bool = True,
    ) -> bool:
        removed = False

        if stop:
            timeline.stop()

        for group, items in list(self.groups.items()):
            if timeline in items:
                items.remove(timeline)
                removed = True

            if not items:
                del self.groups[group]

        return removed

    def remove_group(
        self,
        group: str,
        *,
        stop: bool = True,
    ) -> list[Timeline]:
        timelines = self.resolve(group)

        if stop:
            self.stop(group)

        if group in self.groups:
            del self.groups[group]

        return timelines

    def clear(
        self,
        *,
        stop: bool = True,
    ) -> None:
        if stop:
            self.stop_all()

        self.groups.clear()

    # =================================== #
    # Start / Stop
    # =================================== #

    def start(
        self,
        group: str = DEFAULT_GROUP,
        *,
        restart: bool = True,
    ) -> None:
        for timeline in self.require(group):
            timeline.start(restart=restart)

    def stop(
        self,
        group: str = DEFAULT_GROUP,
    ) -> None:
        for timeline in self.require(group):
            timeline.stop()

    def pause(
        self,
        group: str = DEFAULT_GROUP,
    ) -> None:
        for timeline in self.require(group):
            timeline.pause()

    def resume(
        self,
        group: str = DEFAULT_GROUP,
    ) -> None:
        for timeline in self.require(group):
            timeline.resume()

    def cancel(
        self,
        group: str = DEFAULT_GROUP,
    ) -> None:
        for timeline in self.require(group):
            timeline.cancel()

    def start_all(
        self,
        *,
        restart: bool = True,
    ) -> None:
        self.start_many(
            self.iter_timelines(),
            restart=restart,
        )

    def stop_all(self) -> None:
        self.stop_many(
            self.iter_timelines(),
        )

    def pause_all(self) -> None:
        for timeline in self.iter_timelines():
            timeline.pause()

    def resume_all(self) -> None:
        for timeline in self.iter_timelines():
            timeline.resume()

    def cancel_all(self) -> None:
        for timeline in self.iter_timelines():
            timeline.cancel()

    def start_many(
        self,
        timelines: Iterable[Timeline],
        *,
        restart: bool = True,
    ) -> None:
        for timeline in timelines:
            timeline.start(restart=restart)

    def stop_many(
        self,
        timelines: Iterable[Timeline],
    ) -> None:
        for timeline in timelines:
            timeline.stop()

    # =================================== #
    # Resolve
    # =================================== #

    def resolve(
        self,
        group: str = DEFAULT_GROUP,
    ) -> list[Timeline]:
        return list(
            self.groups.get(group, [])
        )

    def require(
        self,
        group: str = DEFAULT_GROUP,
    ) -> list[Timeline]:
        timelines = self.resolve(group)

        if not timelines:
            raise ValueError(f"Timeline group not found: {group!r}")

        return timelines

    def has_group(
        self,
        group: str,
    ) -> bool:
        return group in self.groups

    # =================================== #
    # Iteration
    # =================================== #

    def iter_groups(
        self,
    ) -> Iterable[str]:
        return self.groups.keys()

    def iter_timelines(
        self,
    ) -> Iterable[Timeline]:
        seen: set[int] = set()

        for timelines in self.groups.values():
            for timeline in timelines:
                timeline_id = id(timeline)

                if timeline_id in seen:
                    continue

                seen.add(timeline_id)
                yield timeline
