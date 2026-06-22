from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Self

from kivy.core.image import Image
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


Rgba = tuple[int, int, int, int]


@dataclass(frozen=True)
class CubeTexture:
    texture_id: int
    size: tuple[int, int]

    @classmethod
    def from_source(
        cls,
        *,
        right: str | Path,
        left: str | Path,
        top: str | Path,
        bottom: str | Path,
        front: str | Path,
        back: str | Path,
    ) -> Self:
        texture_id = _create_cube_texture_id()

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

        _configure_cube_texture()
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

        if expected_size is None:
            raise RuntimeError("Cubemap creation failed: no faces were uploaded")

        return cls(
            texture_id=texture_id,
            size=expected_size,
        )

    @classmethod
    def from_rgba(
        cls,
        *,
        right: Rgba,
        left: Rgba,
        top: Rgba,
        bottom: Rgba,
        front: Rgba,
        back: Rgba,
    ) -> Self:
        texture_id = _create_cube_texture_id()

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

        _configure_cube_texture()
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

        return cls(
            texture_id=texture_id,
            size=(1, 1),
        )


def _create_cube_texture_id() -> int:
    texture_id = glGenTextures(1)
    if isinstance(texture_id, (list, tuple)):
        texture_id = texture_id[0]

    texture_id = int(texture_id)

    glBindTexture(
        GL_TEXTURE_CUBE_MAP,
        texture_id,
    )

    return texture_id


def _configure_cube_texture() -> None:
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
