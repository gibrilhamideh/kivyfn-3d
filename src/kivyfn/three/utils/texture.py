# kivyfn/three/utils/texture.py

from __future__ import annotations

from pathlib import Path
from typing import Literal

from kivy.core.image import Image
from kivy.graphics.texture import Texture

from kivyfn.three.render.resources.texture import CubeTexture, Rgba


TextureWrap = Literal[
    "repeat",
    "mirrored_repeat",
    "clamp_to_edge",
]

TextureMinFilter = Literal[
    "nearest",
    "linear",
    "nearest_mipmap_nearest",
    "linear_mipmap_nearest",
    "nearest_mipmap_linear",
    "linear_mipmap_linear",
]

TextureMagFilter = Literal[
    "nearest",
    "linear",
]


class Texture2D:
    @staticmethod
    def from_rgba(
        rgba: Rgba,
    ) -> Texture:
        texture = Texture.create(
            size=(1, 1),
            colorfmt="rgba",
        )

        texture.blit_buffer(
            bytes(rgba),
            colorfmt="rgba",
            bufferfmt="ubyte",
        )

        texture.flip_vertical()
        return texture

    @staticmethod
    def from_source(
        path: str | Path,
        *,
        mipmap: bool = False,
        wrap: TextureWrap | None = None,
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter | None = None,
        flip_vertical: bool = False,
    ) -> Texture | None:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Texture source does not exist: {path}"
            )

        image = Image(
            str(path),
            mipmap=mipmap,
        )

        if image.texture is None:
            return None

        texture: Texture = image.texture

        if wrap is not None:
            texture.wrap = wrap

        if min_filter is not None:
            texture.min_filter = min_filter

        if mag_filter is not None:
            texture.mag_filter = mag_filter

        if flip_vertical:
            texture.flip_vertical()

        return texture


__all__ = [
    "Texture2D",
    "CubeTexture",
    "Rgba",
    "TextureWrap",
    "TextureMinFilter",
    "TextureMagFilter",
]
