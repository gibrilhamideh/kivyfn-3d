# kivyfn/three/animations/controller.py

from __future__ import annotations

from dataclasses import dataclass, field

from kivyfn.three.animations.action import AnimationAction
from kivyfn.three.animations.binding import AnimationBinding
from kivyfn.three.animations.channel import BoundAnimationChannel
from kivyfn.three.animations.clip import AnimationClip
from kivyfn.three.time import Scheduler


@dataclass(slots=True, weakref_slot=True)
class AnimationController:
    binding: AnimationBinding
    clips: dict[str, AnimationClip]
    actions: dict[str, AnimationAction] = field(default_factory=dict)

    # =================================== #
    # Clips
    # =================================== #

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

    # =================================== #
    # Actions
    # =================================== #

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
        self._bind_action(action)

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

        self._sync_scheduler()

        return action

    def stop(
        self,
        name: str,
    ) -> None:
        action = self.actions.get(name)

        if action is None:
            return

        action.stop()
        self._sync_scheduler()

    def remove(
        self,
        name: str,
    ) -> None:
        action = self.actions.pop(name, None)

        if action is None:
            return

        action.destroy()
        self._sync_scheduler()

    # =================================== #
    # Group actions
    # =================================== #

    def pause_all(self) -> None:
        for action in tuple(self.actions.values()):
            action.pause()

        self._sync_scheduler()

    def resume_all(self) -> None:
        for action in tuple(self.actions.values()):
            action.resume()

        self._sync_scheduler()

    def stop_all(self) -> None:
        for action in tuple(self.actions.values()):
            action.stop()

        self._sync_scheduler()

    def clear(self) -> None:
        for action in tuple(self.actions.values()):
            action.destroy()

        self.actions.clear()
        Scheduler.unregister(self)

    # =================================== #
    # State
    # =================================== #

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

    def _has_active_actions(self) -> bool:
        return any(
            action.playing
            and not action.paused
            and not action.finished
            and not action.destroyed
            for action in self.actions.values()
        )

    # =================================== #
    # Scheduling
    # =================================== #

    def tick(
        self,
        dt: float,
    ) -> bool:
        for action in tuple(self.actions.values()):
            if action.destroyed:
                continue

            action.tick(dt)

        return self._has_active_actions()

    def _sync_scheduler(self) -> None:
        if self._has_active_actions():
            Scheduler.register(self)
        else:
            Scheduler.unregister(self)

    # =================================== #
    # Action events
    # =================================== #

    def _bind_action(
        self,
        action: AnimationAction,
    ) -> None:
        action.bind(
            on_play=self._on_action_started,
            on_resume=self._on_action_started,
            on_pause=self._on_action_state_changed,
            on_stop=self._on_action_state_changed,
            on_finish=self._on_action_state_changed,
            on_destroy=self._on_action_destroyed,
        )

    def _on_action_started(
        self,
        *_: object,
    ) -> None:
        Scheduler.register(self)

    def _on_action_state_changed(
        self,
        *_: object,
    ) -> None:
        self._sync_scheduler()

    def _on_action_destroyed(
        self,
        action: AnimationAction,
        *_: object,
    ) -> None:
        for name, current in tuple(self.actions.items()):
            if current is not action:
                continue

            self.actions.pop(name, None)
            break

        self._sync_scheduler()

    # =================================== #
    # Channel binding
    # =================================== #

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




