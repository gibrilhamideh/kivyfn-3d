# kivyfn/three/utils/texture.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from kivy.core.image import Image
from kivy.graphics.texture import Texture

from kivy.graphics.opengl import (
    GL_CLAMP_TO_EDGE,
    GL_LINEAR,
    GL_RGBA,
    GL_TEXTURE_CUBE_MAP,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
    GL_TEXTURE_CUBE_MAP_POSITIVE_X,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glBindTexture,
    glGenTextures,
    glTexImage2D,
    glTexParameteri,
)

try:
    from kivy.graphics.opengl import GL_TEXTURE_WRAP_R
except ImportError:
    GL_TEXTURE_WRAP_R = 0x8072


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

@dataclass(frozen=True)
class CubeTexture:
    texture_id: int
    size: tuple[int, int]


def create_texture_from_rgba(
    rgba: tuple[int, int, int, int],
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


def create_texture_from_source(
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

def create_cube_texture_from_source(
    *,
    right: str | Path,
    left: str | Path,
    top: str | Path,
    bottom: str | Path,
    front: str | Path,
    back: str | Path,
) -> CubeTexture:
    texture_id = glGenTextures(1)
    if isinstance(texture_id, (list, tuple)):
        texture_id = texture_id[0]

    glBindTexture(
        GL_TEXTURE_CUBE_MAP,
        int(texture_id),
    )

    faces = [
        (GL_TEXTURE_CUBE_MAP_POSITIVE_X, right),
        (GL_TEXTURE_CUBE_MAP_NEGATIVE_X, left),
        (GL_TEXTURE_CUBE_MAP_POSITIVE_Y, top),
        (GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, bottom),
        (GL_TEXTURE_CUBE_MAP_POSITIVE_Z, front),
        (GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, back),
    ]

    expected_size: tuple[int, int] | None = None

    for target, path in faces:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Cubemap face source does not exist: {path}"
            )

        image = Image(
            str(path),
            nocache=True,
        )

        texture = image.texture
        if texture is None:
            raise RuntimeError(
                f"Failed to load cubemap face: {path}"
            )

        width, height = texture.size

        if width != height:
            raise ValueError(
                f"Cubemap face must be square: {path} has size {width}x{height}"
            )

        if expected_size is None:
            expected_size = texture.size
        elif texture.size != expected_size:
            raise ValueError(
                f"All cubemap faces must have the same size. "
                f"Expected {expected_size}, got {texture.size} for {path}"
            )

        glTexImage2D(
            target,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture.pixels,
        )

    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

    glBindTexture(
        GL_TEXTURE_CUBE_MAP,
        0,
    )

    if expected_size is None:
        raise RuntimeError("Cubemap creation failed: no faces were uploaded")

    return CubeTexture(
        texture_id=texture_id,
        size=expected_size,
    )

def create_cube_texture_from_rgba(
    *,
    right: tuple[int, int, int, int],
    left: tuple[int, int, int, int],
    top: tuple[int, int, int, int],
    bottom: tuple[int, int, int, int],
    front: tuple[int, int, int, int],
    back: tuple[int, int, int, int],
) -> CubeTexture:
    texture_id = glGenTextures(1)
    if isinstance(texture_id, (list, tuple)):
        texture_id = texture_id[0]

    glBindTexture(
        GL_TEXTURE_CUBE_MAP,
        int(texture_id),
    )

    faces = [
        (GL_TEXTURE_CUBE_MAP_POSITIVE_X, right),
        (GL_TEXTURE_CUBE_MAP_NEGATIVE_X, left),
        (GL_TEXTURE_CUBE_MAP_POSITIVE_Y, top),
        (GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, bottom),
        (GL_TEXTURE_CUBE_MAP_POSITIVE_Z, front),
        (GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, back),
    ]

    for target, rgba in faces:
        glTexImage2D(
            target,
            0,
            GL_RGBA,
            1,
            1,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            bytes(rgba),
        )

    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

    glBindTexture(
        GL_TEXTURE_CUBE_MAP,
        0,
    )

    return CubeTexture(
        texture_id=texture_id,
        size=(1, 1),
    )
