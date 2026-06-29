# kivyfn/three/animations/action.py

from __future__ import annotations

from kivy.event import EventDispatcher

from kivyfn.three.animations.channel import BoundAnimationChannel
from kivyfn.three.animations.clip import AnimationClip


class AnimationAction(EventDispatcher):

    __events__ = (
        "on_play",
        "on_pause",
        "on_resume",
        "on_stop",
        "on_finish",
        "on_destroy",
    )

    def __init__(
        self,
        *,
        clip: AnimationClip,
        channels: tuple[BoundAnimationChannel, ...] = (),
        time: float = 0.0,
        speed: float = 1.0,
        fps: float = 30.0,
        loop: bool = False,
        playing: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.clip = clip
        self.channels = channels

        self.time = time
        self.speed = speed
        self.fps = max(fps, 1.0)
        self.loop = loop

        self.playing = playing
        self.paused = False
        self.finished = False
        self.destroyed = False

        self._accumulator = 0.0

    @property
    def duration(self) -> float:
        return self.clip.duration

    def play(
        self,
        *,
        restart: bool = False,
    ) -> None:
        self._require_alive()

        if restart:
            self.reset()

        if self.playing and not self.paused:
            return

        self.playing = True
        self.paused = False
        self.finished = False

        self.dispatch("on_play")

    def pause(self) -> None:
        self._require_alive()

        if not self.playing:
            return

        if self.paused:
            return

        self.paused = True
        self.dispatch("on_pause")

    def resume(self) -> None:
        self._require_alive()

        if not self.playing:
            return

        if not self.paused:
            return

        self.paused = False
        self.dispatch("on_resume")

    def stop(self) -> None:
        self._require_alive()

        if not self.playing and not self.paused:
            return

        self.playing = False
        self.paused = False
        self.finished = False
        self._accumulator = 0.0

        self.dispatch("on_stop")

    def finish(self) -> None:
        self._require_alive()

        if self.finished:
            return

        self.playing = False
        self.paused = False
        self.finished = True
        self._accumulator = 0.0

        self.dispatch("on_finish")

    def reset(self) -> None:
        self._require_alive()

        self.time = 0.0
        self._accumulator = 0.0
        self.paused = False
        self.finished = False

    def destroy(self) -> None:
        if self.destroyed:
            return

        self.playing = False
        self.paused = False
        self.finished = True
        self._accumulator = 0.0

        self.destroyed = True
        self.dispatch("on_destroy")

        self.unbind()
        self.channels = ()

    def set_fps(
        self,
        fps: float,
    ) -> None:
        self._require_alive()

        self.fps = max(fps, 1.0)
        self._accumulator = 0.0

    def tick(
        self,
        dt: float,
    ) -> None:
        self._require_alive()

        if not self.playing:
            return

        if self.paused:
            return

        if self.finished:
            return

        duration = self.duration

        if duration <= 0.0:
            self.time = 0.0
            self.finish()
            return

        self.time += dt * self.speed

        if self.time > duration:
            if self.loop:
                self.time %= duration
            else:
                self.time = duration
                self.update()
                self.finish()
                return

        self._accumulator += dt

        interval = 1.0 / self.fps

        if self._accumulator < interval:
            return

        self._accumulator %= interval
        self.update()

    def update(self) -> None:
        self._require_alive()

        for channel in self.channels:
            channel.applier(
                channel.node,
                channel.sampler.sample(self.time),
            )

    def _require_alive(self) -> None:
        if not self.destroyed:
            return

        raise RuntimeError(
            f"Animation action was destroyed: {self.clip.name!r}"
        )

    def on_play(self) -> None:
        pass

    def on_pause(self) -> None:
        pass

    def on_resume(self) -> None:
        pass

    def on_stop(self) -> None:
        pass

    def on_finish(self) -> None:
        pass

    def on_destroy(self) -> None:
        pass
