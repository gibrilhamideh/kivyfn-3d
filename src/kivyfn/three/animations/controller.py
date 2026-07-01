# kivyfn/three/animations/controller.py

from __future__ import annotations

from dataclasses import dataclass, field

from kivy.clock import Clock, ClockEvent

from kivyfn.three.animations.action import AnimationAction
from kivyfn.three.animations.binding import AnimationBinding
from kivyfn.three.animations.clip import AnimationClip
from kivyfn.three.animations.channel import BoundAnimationChannel


@dataclass(slots=True, weakref_slot=True)
class AnimationController:
    binding: AnimationBinding
    clips: dict[str, AnimationClip]
    actions: dict[str, AnimationAction] = field(default_factory=dict)

    _event: ClockEvent | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def get(
        self,
        name: str,
    ) -> AnimationClip | None:
        return self.clips.get(name)

    def require(
        self,
        name: str,
    ) -> AnimationClip:
        clip = self.get(name)

        if clip is None:
            raise ValueError(
                f"Animation clip not found: {name!r}"
            )

        return clip

    def create(
        self,
        name: str,
        *,
        loop: bool = False,
        speed: float = 1.0,
        fps: float = 30.0,
        replace: bool = True,
    ) -> AnimationAction:
        existing = self.actions.get(name)

        if existing is not None:
            if not replace:
                return existing

            existing.destroy()

        clip = self.require(name)

        action = AnimationAction(
            clip=clip,
            channels=self._bind_channels(clip),
            time=0.0,
            speed=speed,
            fps=fps,
            loop=loop,
            playing=False,
        )

        self.actions[name] = action

        action.bind(
            on_destroy=lambda *_: self.actions.pop(name, None),
        )

        return action

    def play(
        self,
        name: str,
        *,
        loop: bool = False,
        speed: float = 1.0,
        fps: float = 30.0,
        restart: bool = True,
        replace: bool = True,
    ) -> AnimationAction:
        action = self.create(
            name,
            loop=loop,
            speed=speed,
            fps=fps,
            replace=replace,
        )

        action.play(
            restart=restart,
        )

        self._ensure_event()
        return action

    def tick(
        self,
        dt: float,
    ) -> None:
        alive = False

        for action in tuple(self.actions.values()):
            if action.destroyed:
                continue

            action.tick(dt)

            if action.playing and not action.paused and not action.finished:
                alive = True

        if not alive:
            self._cancel_event()

    def stop(
        self,
        name: str,
    ) -> None:
        action = self.actions.get(name)

        if action is None:
            return

        action.stop()

    def remove(
        self,
        name: str,
    ) -> None:
        action = self.actions.pop(name, None)

        if action is None:
            return

        action.destroy()

    def pause_all(self) -> None:
        for action in tuple(self.actions.values()):
            action.pause()

    def resume_all(self) -> None:
        for action in tuple(self.actions.values()):
            action.resume()

        self._ensure_event()

    def stop_all(self) -> None:
        for action in tuple(self.actions.values()):
            action.stop()

        self._cancel_event()

    def clear(self) -> None:
        for action in tuple(self.actions.values()):
            action.destroy()

        self.actions.clear()
        self._cancel_event()

    def is_playing(
        self,
        name: str,
    ) -> bool:
        action = self.actions.get(name)

        return (
            action is not None
            and action.playing
            and not action.paused
            and not action.finished
            and not action.destroyed
        )

    def _ensure_event(self) -> None:
        if self._event is not None:
            return

        self._event = Clock.schedule_interval(
            self.tick,
            0.0,
        )

    def _cancel_event(self) -> None:
        if self._event is None:
            return

        self._event.cancel()
        self._event = None

    def _bind_channels(
        self,
        clip: AnimationClip,
    ) -> tuple[BoundAnimationChannel, ...]:
        channels: list[BoundAnimationChannel] = []

        for channel in clip.channels:
            target = self.binding.get(
                channel.target,
            )

            if target is None:
                continue

            channels.append(
                BoundAnimationChannel(
                    target=target,
                    path=channel.path,
                    sampler=channel.sampler,

                )
            )

        return tuple(channels)






