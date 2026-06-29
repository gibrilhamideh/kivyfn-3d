# kivyfn/three/animations/controller.py

from __future__ import annotations

from dataclasses import dataclass, field

from kivyfn.three.graph.node import Node3D
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.animations.action import AnimationAction
from kivyfn.three.animations.binding import AnimationBinding
from kivyfn.three.animations.clip import AnimationClip
from kivyfn.three.animations.types import AnimationValue
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector3


@dataclass(slots=True)
class AnimationController:
    binding: AnimationBinding
    clips: dict[str, AnimationClip]
    active: dict[str, AnimationAction] = field(default_factory=dict)

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

    def play(
        self,
        name: str,
        *,
        loop: bool = False,
        speed: float = 1.0,
        restart: bool = True,
    ) -> AnimationAction:
        existing = self.active.get(name)

        if existing is not None and not restart:
            existing.playing = True
            existing.loop = loop
            existing.speed = speed
            return existing

        clip = self.require(name)

        action = AnimationAction(
            clip=clip,
            time=0.0,
            speed=speed,
            loop=loop,
            playing=True,
        )

        self.active[name] = action
        return action

    def stop(
        self,
        name: str,
    ) -> None:
        self.active.pop(name, None)

    def stop_all(self) -> None:
        self.active.clear()

    def is_playing(
        self,
        name: str,
    ) -> bool:
        action = self.active.get(name)
        return action is not None and action.playing

    def update(
        self,
        dt: float,
    ) -> None:
        for name, action in list(self.active.items()):
            if not action.playing:
                self.active.pop(name, None)
                continue

            self._update_action(action, dt)
            self._apply_action(action)

            if not action.playing:
                self.active.pop(name, None)

    def _update_action(
        self,
        action: AnimationAction,
        dt: float,
    ) -> None:

        duration = action.clip.duration

        action.time += dt * action.speed

        if duration <= 0.0:
            action.time = 0.0
            action.playing = False
            return

        if action.time <= duration:
            return

        if action.loop:
            action.time %= duration
            return

        action.time = duration
        action.playing = False

    def _apply_action(
        self,
        action: AnimationAction,
    ) -> None:
        touched: list[Node3D] = []
        seen: set[Node3D] = set()

        for channel in action.clip.channels:
            node = self.binding.get(channel.target)

            if node is None:
                continue

            value = channel.sampler.sample(action.time)

            changed = self._apply_value(
                node=node,
                path=channel.path,
                value=value,
            )

            if not changed:
                continue

            if node in seen:
                continue

            seen.add(node)
            touched.append(node)

        for node in self._topmost_nodes(touched):
            node.mark_transform_dirty()

    def _apply_value(
        self,
        *,
        node: Node3D,
        path: str,
        value: AnimationValue,
    ) -> bool:
        match path:
            case "translation":
                if not isinstance(value, Vector3):
                    raise TypeError(
                        "Translation animation value must be Vector3."
                    )

                node.set_translation(value, dirty=False)
                return True

            case "rotation":
                if not isinstance(value, Quaternion):
                    raise TypeError(
                        "Rotation animation value must be Quaternion."
                    )

                node.set_rotation(value, dirty=False)
                return True

            case "scale":
                if not isinstance(value, Vector3):
                    raise TypeError(
                        "Scale animation value must be Vector3."
                    )

                node.set_scale(value, dirty=False)
                return True

            case "weights":
                if not isinstance(value, tuple):
                    raise TypeError(
                        "Weights animation value must be tuple[float, ...]."
                    )

                self._apply_morph_weights(
                    node=node,
                    weights=value,
                )
                return False

            case _:
                raise ValueError(
                    f"Unsupported animation path: {path!r}"
                )

    def _apply_morph_weights(
        self,
        node,
        weights: tuple[float, ...],
    ) -> None:
        if isinstance(node, Object3D):
            node.set_morph_weights(weights)
            return

        for child in node.children:
            if isinstance(child, Object3D):
                child.set_morph_weights(weights)

    def _topmost_nodes(
        self,
        nodes: list[Node3D],
    ) -> list[Node3D]:
        node_set = set(nodes)
        roots: list[Node3D] = []

        for node in nodes:
            parent = node.parent

            while parent is not None:
                if parent in node_set:
                    break

                parent = parent.parent
            else:
                roots.append(node)

        return roots
