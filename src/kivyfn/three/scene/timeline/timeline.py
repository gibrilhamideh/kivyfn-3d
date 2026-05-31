# kivyfn/three/scene/timeline/timeline.py
from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from kivy.clock import Clock
from kivy.clock import ClockEvent
from kivy.event import EventDispatcher


TimelineMode = Literal[
    "loop",
    "tween",
]

TimelineState = Literal[
    "idle",
    "running",
    "paused",
    "completed",
]


Transition = str | Callable[[float], float]
TimelineCallback = Callable[[float], None]


class TimelineTransition:
    @staticmethod
    def linear(t: float) -> float:
        return t

    @staticmethod
    def in_quad(t: float) -> float:
        return t * t

    @staticmethod
    def out_quad(t: float) -> float:
        return -t * (t - 2.0)

    @staticmethod
    def in_out_quad(t: float) -> float:
        t *= 2.0

        if t < 1.0:
            return 0.5 * t * t

        t -= 1.0

        return -0.5 * (t * (t - 2.0) - 1.0)

    @staticmethod
    def in_cubic(t: float) -> float:
        return t * t * t

    @staticmethod
    def out_cubic(t: float) -> float:
        t -= 1.0
        return t * t * t + 1.0

    @staticmethod
    def in_out_cubic(t: float) -> float:
        t *= 2.0

        if t < 1.0:
            return 0.5 * t * t * t

        t -= 2.0

        return 0.5 * (t * t * t + 2.0)


class Timeline(EventDispatcher):
    __events__ = (
        "on_start",
        "on_update",
        "on_complete",
        "on_stop",
    )

    def __init__(
        self,
        callback: TimelineCallback,
        *,
        name: str = "",
        mode: TimelineMode = "loop",
        duration: float = 1.0,
        interval: float = 0.0,
        speed: float = 1.0,
        transition: Transition = "linear",
        repeat: bool = False,
        yoyo: bool = False,
    ) -> None:
        super().__init__()

        if duration <= 0.0:
            raise ValueError("Timeline duration must be greater than 0.")

        if interval < 0.0:
            raise ValueError("Timeline interval cannot be negative.")

        self.name = name
        self.callback = callback
        self.mode = mode
        self.duration = duration
        self.interval = interval
        self.speed = speed
        self.repeat = repeat
        self.yoyo = yoyo

        self.state: TimelineState = "idle"
        self.elapsed = 0.0
        self.direction = 1.0

        self._event: ClockEvent | None = None
        self._transition = self._resolve_transition(transition)

    @classmethod
    def loop(
        cls,
        callback: TimelineCallback,
        *,
        name: str = "",
        interval: float = 0.0,
        speed: float = 1.0,
    ) -> Timeline:
        return cls(
            callback=callback,
            name=name,
            mode="loop",
            interval=interval,
            speed=speed,
            repeat=True,
        )

    @classmethod
    def tween(
        cls,
        callback: TimelineCallback,
        *,
        name: str = "",
        duration: float = 1.0,
        interval: float = 0.0,
        speed: float = 1.0,
        transition: Transition = "linear",
        repeat: bool = False,
        yoyo: bool = False,
    ) -> Timeline:
        return cls(
            callback=callback,
            name=name,
            mode="tween",
            duration=duration,
            interval=interval,
            speed=speed,
            transition=transition,
            repeat=repeat,
            yoyo=yoyo,
        )

    def start(
        self,
        *,
        restart: bool = True,
    ) -> None:
        if restart:
            self.elapsed = 0.0
            self.direction = 1.0

        self.stop(dispatch_event=False)

        self.state = "running"
        self._event = Clock.schedule_interval(
            self._tick,
            self.interval,
        )

        self.dispatch("on_start")

    def stop(
        self,
        *,
        dispatch_event: bool = True,
    ) -> None:
        if self._event is not None:
            self._event.cancel()
            self._event = None

        was_running = self.state == "running"

        self.state = "idle"

        if dispatch_event and was_running:
            self.dispatch("on_stop")

    def pause(self) -> None:
        if self.state != "running":
            return

        if self._event is not None:
            self._event.cancel()
            self._event = None

        self.state = "paused"

    def resume(self) -> None:
        if self.state != "paused":
            return

        self.state = "running"
        self._event = Clock.schedule_interval(
            self._tick,
            self.interval,
        )

    def cancel(self) -> None:
        self.stop(dispatch_event=False)
        self.elapsed = 0.0
        self.direction = 1.0
        self.state = "idle"

    def is_running(self) -> bool:
        return self.state == "running"

    def is_paused(self) -> bool:
        return self.state == "paused"

    def _tick(
        self,
        dt: float,
    ) -> bool:
        if self.state != "running":
            return False

        scaled_dt = dt * self.speed

        if self.mode == "loop":
            self.callback(scaled_dt)
            self.dispatch("on_update", scaled_dt)
            return True

        self.elapsed += scaled_dt * self.direction

        raw_progress = self.elapsed / self.duration
        raw_progress = max(0.0, min(1.0, raw_progress))

        progress = self._transition(raw_progress)

        self.callback(progress)
        self.dispatch("on_update", progress)

        if self.direction > 0.0 and self.elapsed >= self.duration:
            self._finish_tween()

        elif self.direction < 0.0 and self.elapsed <= 0.0:
            self._finish_tween()

        return True

    def _finish_tween(self) -> None:
        if self.repeat:
            if self.yoyo:
                self.direction *= -1.0
            else:
                self.elapsed = 0.0

            return

        self.state = "completed"

        if self._event is not None:
            self._event.cancel()
            self._event = None

        self.dispatch("on_complete")

    def _resolve_transition(
        self,
        transition: Transition,
    ) -> Callable[[float], float]:
        if callable(transition):
            return transition

        method = getattr(
            TimelineTransition,
            transition,
            None,
        )

        if method is None:
            raise ValueError(
                f"Unknown timeline transition: {transition!r}"
            )

        return method

    def on_start(self) -> None:
        pass

    def on_update(
        self,
        value: float,
    ) -> None:
        pass

    def on_complete(self) -> None:
        pass

    def on_stop(self) -> None:
        pass
