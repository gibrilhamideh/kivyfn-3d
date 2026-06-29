# kivyfn/three/parsers/glb/parser/textures.py

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import ClassVar

import xxhash

from kivyfn.three.graphics.gl.texture import (
    Texture2D,
    TextureWrap,
    TextureMinFilter,
    TextureMagFilter,
)
from kivyfn.three.parsers.glb.parser.accessors import GlbAccessor
from kivyfn.three.parsers.glb.parser.context import GlbContext
from kivyfn.three.parsers.glb.parser.data import (
    GlbTextureData,
    GlbImageData,
    GlbSamplerData,
)


class GlbTextures:
    min_filter_map: ClassVar[dict[int, TextureMinFilter]] = {
        9728: "nearest",
        9729: "linear",
        9984: "nearest_mipmap_nearest",
        9985: "linear_mipmap_nearest",
        9986: "nearest_mipmap_linear",
        9987: "linear_mipmap_linear",
    }

    mag_filter_map: ClassVar[dict[int, TextureMagFilter]] = {
        9728: "nearest",
        9729: "linear",
    }

    wrap_map: ClassVar[dict[int, TextureWrap]] = {
        33071: "clamp_to_edge",
        33648: "mirrored_repeat",
        10497: "repeat",
    }

    def __init__(
        self,
        context: GlbContext,
        accessor: GlbAccessor,
    ) -> None:
        self.context = context
        self.accessor = accessor

    def resolve(
        self,
        info: object,
    ) -> Texture2D | None:
        if info is None:
            return None

        if isinstance(info, dict):
            index = info.get(
                "index",
                None,
            )

        else:
            index = getattr(
                info,
                "index",
                None,
            )

        if index is None:
            return None

        return self.load(
            int(index),
        )

    def load(
        self,
        index: int,
    ) -> Texture2D | None:
        gltf = self.context.gltf

        if (
            not gltf.textures
            or index < 0
            or index >= len(gltf.textures)
        ):
            return None

        cached = self.context.texture_cache.get(index)

        if cached is not None:
            return cached

        data = GlbTextureData(
            gltf.textures[index],
        )

        if data.source_index is None:
            return None

        texture = self.image(
            index=data.source_index,
            sampler=self.sampler(data),
        )

        if texture is None:
            return None

        self.apply(
            texture=texture,
            data=data,
        )

        self.context.texture_cache[index] = texture

        return texture

    def image(
        self,
        *,
        index: int,
        sampler: tuple[
            int | None,
            int | None,
            int | None,
            int | None,
        ],
    ) -> Texture2D | None:
        image_bytes = self.data(index)

        if image_bytes is None:
            return None

        image_hash = xxhash.xxh3_64_hexdigest(image_bytes)

        key = (
            image_hash,
            sampler[0],
            sampler[1],
            sampler[2],
            sampler[3],
        )

        cached = self.context.image_texture_cache.get(key)

        if cached is not None:
            return cached

        texture = Texture2D.from_bytes(
            image_bytes,
            mipmap=True,
            wrap="repeat",
            min_filter="linear_mipmap_linear",
            mag_filter="linear",
        )

        self.context.image_texture_cache[key] = texture

        return texture

    def data(
        self,
        index: int,
    ) -> bytes | None:
        cached = self.context.image_bytes_cache.get(index)

        if cached is not None:
            return cached

        gltf = self.context.gltf

        if (
            not gltf.images
            or index < 0
            or index >= len(gltf.images)
        ):
            return None

        data = GlbImageData(
            gltf.images[index],
        )

        image_bytes = self.bytes(data)

        if image_bytes is None:
            return None

        self.context.image_bytes_cache[index] = image_bytes

        return image_bytes

    def bytes(
        self,
        data: GlbImageData,
    ) -> bytes | None:
        if data.uri:
            if data.uri.startswith("data:"):
                encoded = data.uri.split(",", 1)[1]

                return base64.b64decode(encoded)

            image_path = (
                Path(data.uri)
                if os.path.isabs(data.uri)
                else self.context.base_path / data.uri
            )

            return image_path.read_bytes()

        if data.buffer_view_index is not None:
            return self.accessor.bytes(
                data.buffer_view_index,
            )

        return None

    def sampler(
        self,
        data: GlbTextureData,
    ) -> tuple[
        int | None,
        int | None,
        int | None,
        int | None,
    ]:
        sampler = self.sampler_data(data)

        if sampler is None:
            return (
                None,
                None,
                None,
                None,
            )

        return (
            sampler.min_filter,
            sampler.mag_filter,
            sampler.wrap_s,
            sampler.wrap_t,
        )

    def sampler_data(
        self,
        data: GlbTextureData,
    ) -> GlbSamplerData | None:
        gltf = self.context.gltf
        index = data.sampler_index

        if (
            index is None
            or not gltf.samplers
            or index < 0
            or index >= len(gltf.samplers)
        ):
            return None

        return GlbSamplerData(
            gltf.samplers[index],
        )

    def apply(
        self,
        *,
        texture: Texture2D,
        data: GlbTextureData,
    ) -> None:
        sampler = self.sampler_data(data)

        if sampler is None:
            return

        min_filter = self.min_filter(
            sampler.min_filter,
        )

        mag_filter = self.mag_filter(
            sampler.mag_filter,
        )

        wrap_s = self.wrap(
            sampler.wrap_s,
        )

        wrap_t = self.wrap(
            sampler.wrap_t,
        )

        if min_filter is not None or mag_filter is not None:
            texture.set_filter(
                min_filter=min_filter,
                mag_filter=mag_filter,
            )

        if wrap_s is not None and wrap_t is not None:
            texture.set_wrap(
                wrap_s,
            )

        elif wrap_s is not None:
            texture.set_wrap(
                wrap_s,
            )

        elif wrap_t is not None:
            texture.set_wrap(
                wrap_t,
            )

    def min_filter(
        self,
        value: int | None,
    ) -> TextureMinFilter | None:
        if value is None:
            return None

        return self.min_filter_map.get(value)

    def mag_filter(
        self,
        value: int | None,
    ) -> TextureMagFilter | None:
        if value is None:
            return None

        return self.mag_filter_map.get(value)

    def wrap(
        self,
        value: int | None,
    ) -> TextureWrap | None:
        if value is None:
            return None

        return self.wrap_map.get(value)
