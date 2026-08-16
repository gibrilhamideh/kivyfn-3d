# kivyfn/three/time/scheduler.py

"""
Schedule time-driven three-dimensional systems.

The scheduler coordinates animations, timelines, and other systems requiring
elapsed time. Event-driven rendering and scene synchronization remain
independent.
"""

from __future__ import annotations

import math
from typing import ClassVar, Protocol

from kivy.clock import Clock, ClockEvent

from kivyfn.logging import get_logger


logger = get_logger(__name__)


class Tickable(Protocol):
    """
    Define an object driven by the global scheduler.
    """

    def tick(
        self,
        dt: float,
    ) -> bool:
        """
        Advance by ``dt`` seconds.

        Return True to remain registered or False to be removed.
        """
        ...


class Scheduler:
    """
    Globally schedule time-driven three-dimensional systems.

    This class cannot be instantiated. All state and operations belong to the
    global three-dimensional scheduling domain.
    """

    _tickables: ClassVar[dict[int, Tickable]] = {}
    _event: ClassVar[ClockEvent | None] = None

    _paused: ClassVar[bool] = False
    _time_scale: ClassVar[float] = 1.0

    def __new__(
        cls,
    ) -> Scheduler:
        raise TypeError(
            "Scheduler cannot be instantiated."
        )

    # =================================== #
    # State
    # =================================== #

    @classmethod
    def is_paused(cls) -> bool:
        return cls._paused

    @classmethod
    def is_running(cls) -> bool:
        return cls._event is not None

    @classmethod
    def get_time_scale(cls) -> float:
        return cls._time_scale

    @classmethod
    def set_time_scale(
        cls,
        value: float,
    ) -> None:
        value = float(value)

        if not math.isfinite(value):
            raise ValueError(
                "Three-dimensional time scale must be finite."
            )

        if value < 0.0:
            raise ValueError(
                "Three-dimensional time scale cannot be negative."
            )

        if value == cls._time_scale:
            return

        cls._time_scale = value

        if value == 0.0:
            cls._cancel_event()
        else:
            cls._ensure_event()

    @classmethod
    def count(cls) -> int:
        return len(cls._tickables)

    # =================================== #
    # Registration
    # =================================== #

    @classmethod
    def register(
        cls,
        tickable: Tickable,
    ) -> None:
        cls._tickables[id(tickable)] = tickable
        cls._ensure_event()

    @classmethod
    def unregister(
        cls,
        tickable: Tickable,
    ) -> None:
        tickable_id = id(tickable)

        if cls._tickables.get(tickable_id) is tickable:
            cls._tickables.pop(
                tickable_id,
                None,
            )

        if not cls._tickables:
            cls._cancel_event()

    @classmethod
    def clear(cls) -> None:
        cls._tickables.clear()
        cls._cancel_event()

    @classmethod
    def reset(cls) -> None:
        """
        Restore the scheduler to its initial state.

        This is primarily useful for application teardown and isolated tests.
        """
        cls.clear()

        cls._paused = False
        cls._time_scale = 1.0

    # =================================== #
    # Pause and resume
    # =================================== #

    @classmethod
    def pause(cls) -> None:
        if cls._paused:
            return

        cls._paused = True
        cls._cancel_event()

    @classmethod
    def resume(cls) -> None:
        if not cls._paused:
            return

        cls._paused = False
        cls._ensure_event()

    # =================================== #
    # Tick
    # =================================== #

    @classmethod
    def _tick(
        cls,
        dt: float,
    ) -> None:
        scaled_dt = dt * cls._time_scale

        for tickable in tuple(cls._tickables.values()):
            tickable_id = id(tickable)

            if cls._tickables.get(tickable_id) is not tickable:
                continue

            try:
                active = tickable.tick(
                    scaled_dt,
                )

            except Exception:
                logger.exception(
                    "A three-dimensional scheduler item failed: %r",
                    tickable,
                )

                cls.unregister(
                    tickable,
                )
                continue

            if not active:
                cls.unregister(
                    tickable,
                )

        if not cls._tickables:
            cls._cancel_event()

    # =================================== #
    # Kivy scheduling
    # =================================== #

    @classmethod
    def _ensure_event(cls) -> None:
        if cls._event is not None:
            return

        if cls._paused:
            return

        if cls._time_scale == 0.0:
            return

        if not cls._tickables:
            return

        cls._event = Clock.schedule_interval(
            cls._tick,
            0.0,
        )

    @classmethod
    def _cancel_event(cls) -> None:
        event = cls._event

        if event is None:
            return

        cls._event = None
        event.cancel()
