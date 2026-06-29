# kivyfn/three/parsers/glb/parser/animations.py

from __future__ import annotations

from typing import cast

import numpy as np

from kivyfn.three.animations.channel import AnimationChannel
from kivyfn.three.animations.clip import AnimationClip
from kivyfn.three.animations.keyframe import AnimationKeyframe
from kivyfn.three.animations.library import AnimationLibrary
from kivyfn.three.animations.sampler import AnimationSampler
from kivyfn.three.animations.types import (
    AnimationPath,
    AnimationValue,
    InterpolationMode,
)
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector3
from kivyfn.three.parsers.glb.parser.accessors import GlbAccessor
from kivyfn.three.parsers.glb.parser.context import GlbContext
from kivyfn.three.parsers.glb.parser.data import (
    GlbAnimationChannelData,
    GlbAnimationData,
    GlbAnimationSamplerData,
)

TIME_EPSILON = 1e-6


class GlbAnimations:
    supported_paths = {
        "translation",
        "rotation",
        "scale",
        "weights",
    }

    def __init__(
        self,
        context: GlbContext,
        accessor: GlbAccessor,
    ) -> None:
        self.context = context
        self.accessor = accessor

    def load(
        self,
    ) -> AnimationLibrary | None:
        gltf = self.context.gltf
        raw_animations = list(gltf.animations or [])

        if not raw_animations:
            return None

        library = AnimationLibrary()

        for index, raw_animation in enumerate(raw_animations):
            data = GlbAnimationData(
                raw_animation,
            )

            clip = self.clip(
                index=index,
                data=data,
            )

            if clip is None:
                continue

            library.add(clip)

        if library.is_empty:
            return None

        return library

    def clip(
        self,
        *,
        index: int,
        data: GlbAnimationData,
    ) -> AnimationClip | None:
        name = (
            data.name
            or f"animation_{index}"
        )

        channels: list[AnimationChannel] = []

        for raw_channel in data.channels:
            channel = GlbAnimationChannelData(
                raw_channel,
            )

            loaded = self.channel(
                channel=channel,
                animation=data,
            )

            if loaded is None:
                continue

            channels.append(loaded)

        if not channels:
            return None

        return AnimationClip(
            name=name,
            channels=self.normalize(
                tuple(channels),
            ),
        )


    def channel(
        self,
        *,
        channel: GlbAnimationChannelData,
        animation: GlbAnimationData,
    ) -> AnimationChannel | None:
        if channel.target_node_index is None:
            return None

        if channel.target_path not in self.supported_paths:
            return None

        path = cast(
            AnimationPath,
            channel.target_path,
        )

        if channel.sampler_index < 0:
            return None

        if channel.sampler_index >= len(animation.samplers):
            return None

        sampler = self.sampler(
            data=GlbAnimationSamplerData(
                animation.samplers[channel.sampler_index],
            ),
            path=path,
        )

        if sampler is None:
            return None

        return AnimationChannel(
            target=channel.target_node_index,
            path=path,
            sampler=sampler,
        )

    def sampler(
        self,
        *,
        data: GlbAnimationSamplerData,
        path: AnimationPath,
    ) -> AnimationSampler | None:
        times = self.accessor.read(
            data.input_index,
        )

        values = self.accessor.read(
            data.output_index,
        )

        if times is None or values is None:
            return None

        times = times.reshape(-1).astype(
            np.float32,
            copy=False,
        )

        if len(times) == 0:
            return None

        interpolation_name = data.interpolation.upper()
        interpolation = self.interpolation(
            interpolation_name,
        )

        values = self.values(
            values=values,
            times=times,
            interpolation=interpolation_name,
        )

        if values is None:
            return None

        keyframes: list[AnimationKeyframe] = []

        for index, time in enumerate(times):
            value = self.value(
                row=values[index],
                path=path,
            )

            if value is None:
                continue

            keyframes.append(
                AnimationKeyframe(
                    time=float(time),
                    value=value,
                )
            )

        if not keyframes:
            return None

        return AnimationSampler(
            keyframes=tuple(keyframes),
            interpolation=interpolation,
        )

    def values(
        self,
        *,
        values: np.ndarray,
        times: np.ndarray,
        interpolation: str,
    ) -> np.ndarray | None:
        if interpolation == "CUBICSPLINE":
            if len(values) != len(times) * 3:
                return None

            values = values.reshape(
                len(times),
                3,
                -1,
            )[:, 1, :]

        if len(values) != len(times):
            return None

        return values

    def interpolation(
        self,
        value: str,
    ) -> InterpolationMode:
        match value.upper():
            case "STEP":
                return "step"

            case "LINEAR":
                return "linear"

            case "CUBICSPLINE":
                return "linear"

            case _:
                return "linear"

    def value(
        self,
        *,
        row: np.ndarray,
        path: AnimationPath,
    ) -> AnimationValue | None:
        match path:
            case "translation":
                if row.shape[0] < 3:
                    return None

                return Vector3(
                    float(row[0]),
                    float(row[1]),
                    float(row[2]),
                )

            case "rotation":
                if row.shape[0] < 4:
                    return None

                return Quaternion(
                    float(row[0]),
                    float(row[1]),
                    float(row[2]),
                    float(row[3]),
                ).normalize()

            case "scale":
                if row.shape[0] < 3:
                    return None

                return Vector3(
                    float(row[0]),
                    float(row[1]),
                    float(row[2]),
                )

            case "weights":
                return tuple(
                    float(value)
                    for value in row.reshape(-1)
                )

    def normalize(
        self,
        channels: tuple[AnimationChannel, ...],
    ) -> tuple[AnimationChannel, ...]:
        start = min(
            keyframe.time
            for channel in channels
            for keyframe in channel.sampler.keyframes
        )

        if abs(start) <= TIME_EPSILON:
            return channels

        normalized: list[AnimationChannel] = []

        for channel in channels:
            keyframes = tuple(
                AnimationKeyframe(
                    time=keyframe.time - start,
                    value=keyframe.value,
                )
                for keyframe in channel.sampler.keyframes
            )

            sampler = AnimationSampler(
                keyframes=keyframes,
                interpolation=channel.sampler.interpolation,
            )

            normalized.append(
                AnimationChannel(
                    target=channel.target,
                    path=channel.path,
                    sampler=sampler,
                )
            )

        return tuple(normalized)




__all__ = (
    "GlbAnimations",
)
