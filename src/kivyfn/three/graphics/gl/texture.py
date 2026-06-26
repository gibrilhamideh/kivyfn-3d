# kivyfn/three/graphics/gl/texture.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Self

from kivy.core.image import Image

from kivyfn.three.graphics.gl.core import GL
from kivyfn.three.graphics.gl.utils import normalize_size


Rgba = tuple[int, int, int, int]


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


WRAP_MODES: dict[TextureWrap, int] = {
    "repeat": GL.REPEAT,
    "mirrored_repeat": GL.MIRRORED_REPEAT,
    "clamp_to_edge": GL.CLAMP_TO_EDGE,
}


FILTER_MODES: dict[TextureMinFilter | TextureMagFilter, int] = {
    "nearest": GL.NEAREST,
    "linear": GL.LINEAR,
    "nearest_mipmap_nearest": GL.NEAREST_MIPMAP_NEAREST,
    "linear_mipmap_nearest": GL.LINEAR_MIPMAP_NEAREST,
    "nearest_mipmap_linear": GL.NEAREST_MIPMAP_LINEAR,
    "linear_mipmap_linear": GL.LINEAR_MIPMAP_LINEAR,
}


MIPMAP_FILTERS: set[TextureMinFilter] = {
    "nearest_mipmap_nearest",
    "linear_mipmap_nearest",
    "nearest_mipmap_linear",
    "linear_mipmap_linear",
}


CUBE_FACE_TARGETS: tuple[int, ...] = (
    GL.CUBE_POSITIVE_X,
    GL.CUBE_NEGATIVE_X,
    GL.CUBE_POSITIVE_Y,
    GL.CUBE_NEGATIVE_Y,
    GL.CUBE_POSITIVE_Z,
    GL.CUBE_NEGATIVE_Z,
)


def _resolve_min_filter(
    *,
    mipmap: bool,
    min_filter: TextureMinFilter | None,
) -> TextureMinFilter:
    if min_filter is None:
        return (
            "linear_mipmap_linear"
            if mipmap
            else "linear"
        )

    if min_filter in MIPMAP_FILTERS and not mipmap:
        raise ValueError(
            f"min_filter={min_filter!r} requires mipmap=True."
        )

    return min_filter


def configure_texture_2d(
    *,
    wrap: TextureWrap = "clamp_to_edge",
    min_filter: TextureMinFilter = "linear",
    mag_filter: TextureMagFilter = "linear",
) -> None:
    wrap_value = WRAP_MODES[wrap]

    GL.tex_parameteri(
        GL.TEXTURE_2D,
        GL.TEXTURE_WRAP_S,
        wrap_value,
    )
    GL.tex_parameteri(
        GL.TEXTURE_2D,
        GL.TEXTURE_WRAP_T,
        wrap_value,
    )

    GL.tex_parameteri(
        GL.TEXTURE_2D,
        GL.TEXTURE_MIN_FILTER,
        FILTER_MODES[min_filter],
    )
    GL.tex_parameteri(
        GL.TEXTURE_2D,
        GL.TEXTURE_MAG_FILTER,
        FILTER_MODES[mag_filter],
    )


def configure_texture_cube(
    *,
    wrap: TextureWrap = "clamp_to_edge",
    min_filter: TextureMinFilter = "linear",
    mag_filter: TextureMagFilter = "linear",
) -> None:
    wrap_value = WRAP_MODES[wrap]

    GL.tex_parameteri(
        GL.TEXTURE_CUBE,
        GL.TEXTURE_WRAP_S,
        wrap_value,
    )
    GL.tex_parameteri(
        GL.TEXTURE_CUBE,
        GL.TEXTURE_WRAP_T,
        wrap_value,
    )
    GL.tex_parameteri(
        GL.TEXTURE_CUBE,
        GL.TEXTURE_WRAP_R,
        wrap_value,
    )

    GL.tex_parameteri(
        GL.TEXTURE_CUBE,
        GL.TEXTURE_MIN_FILTER,
        FILTER_MODES[min_filter],
    )
    GL.tex_parameteri(
        GL.TEXTURE_CUBE,
        GL.TEXTURE_MAG_FILTER,
        FILTER_MODES[mag_filter],
    )


def create_empty_pixels(
    *,
    width: int,
    height: int,
    format: int,
    type: int,
) -> bytes:
    if type != GL.UNSIGNED_BYTE:
        raise ValueError(
            "Only GL.UNSIGNED_BYTE empty texture pixels are supported."
        )

    if format == GL.RGBA:
        channels = 4
    elif format == GL.RGB:
        channels = 3
    else:
        raise ValueError(
            f"Unsupported empty texture format: {format}"
        )

    return bytes(width * height * channels)


@dataclass(slots=True)
class Texture2D:
    id: int
    size: tuple[int, int]
    target: int = GL.TEXTURE_2D
    resizable: bool = False
    format: int = GL.RGBA
    type: int = GL.UNSIGNED_BYTE
    mipmap: bool = False
    wrap: TextureWrap = "clamp_to_edge"
    min_filter: TextureMinFilter = "linear"
    mag_filter: TextureMagFilter = "linear"

    @classmethod
    def from_source(
        cls,
        path: str | Path,
        *,
        flip_vertical: bool = False,
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Texture source does not exist: {path}"
            )

        image = Image(
            str(path),
            nocache=True,
        )

        source = image.texture
        if source is None:
            raise RuntimeError(
                f"Failed to load texture source: {path}"
            )

        if flip_vertical:
            source.flip_vertical()

        width, height = source.size

        resolved_min_filter = _resolve_min_filter(
            mipmap=mipmap,
            min_filter=min_filter,
        )

        texture_id = GL.create_texture(GL.TEXTURE_2D)

        GL.tex_image_2d(
            target=GL.TEXTURE_2D,
            width=width,
            height=height,
            pixels=source.pixels,
            format=GL.RGBA,
            type=GL.UNSIGNED_BYTE,
        )

        configure_texture_2d(
            wrap=wrap,
            min_filter=resolved_min_filter,
            mag_filter=mag_filter,
        )

        if mipmap:
            GL.generate_mipmap(GL.TEXTURE_2D)

        GL.unbind_texture(GL.TEXTURE_2D)

        return cls(
            id=texture_id,
            size=(width, height),
            resizable=False,
            format=GL.RGBA,
            type=GL.UNSIGNED_BYTE,
            mipmap=mipmap,
            wrap=wrap,
            min_filter=resolved_min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def from_rgba(
        cls,
        rgba: Rgba,
        *,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        texture_id = GL.create_texture(GL.TEXTURE_2D)

        GL.tex_image_2d(
            target=GL.TEXTURE_2D,
            width=1,
            height=1,
            pixels=bytes(rgba),
            format=GL.RGBA,
            type=GL.UNSIGNED_BYTE,
        )

        configure_texture_2d(
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

        GL.unbind_texture(GL.TEXTURE_2D)

        return cls(
            id=texture_id,
            size=(1, 1),
            resizable=False,
            format=GL.RGBA,
            type=GL.UNSIGNED_BYTE,
            mipmap=False,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def empty(
        cls,
        size: int | tuple[int, int],
        *,
        resizable: bool = True,
        format: int = GL.RGBA,
        type: int = GL.UNSIGNED_BYTE,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        width, height = normalize_size(size)

        if min_filter in MIPMAP_FILTERS:
            raise ValueError(
                "Texture2D.empty() does not generate mipmaps. "
                f"Use a non-mipmap min_filter, got {min_filter!r}."
            )

        texture_id = GL.create_texture(GL.TEXTURE_2D)

        GL.tex_image_2d(
            target=GL.TEXTURE_2D,
            width=width,
            height=height,
            pixels=create_empty_pixels(
                width=width,
                height=height,
                format=format,
                type=type,
            ),
            format=format,
            type=type,
        )

        configure_texture_2d(
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

        GL.unbind_texture(GL.TEXTURE_2D)

        return cls(
            id=texture_id,
            size=(width, height),
            resizable=resizable,
            format=format,
            type=type,
            mipmap=False,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    def resize(
        self,
        size: int | tuple[int, int],
        *,
        format: int | None = None,
        type: int | None = None,
    ) -> None:
        if not self.resizable:
            raise RuntimeError(
                "Texture2D is not resizable."
            )

        width, height = normalize_size(size)

        if self.size == (width, height):
            return

        format = self.format if format is None else format
        type = self.type if type is None else type

        GL.bind_texture(
            self.target,
            self.id,
        )

        GL.tex_image_2d(
            target=self.target,
            width=width,
            height=height,
            pixels=create_empty_pixels(
                width=width,
                height=height,
                format=format,
                type=type,
            ),
            format=format,
            type=type,
        )

        configure_texture_2d(
            wrap=self.wrap,
            min_filter=self.min_filter,
            mag_filter=self.mag_filter,
        )

        GL.unbind_texture(self.target)

        self.size = (width, height)
        self.format = format
        self.type = type

    def delete(self) -> None:
        if self.id == 0:
            return

        GL.delete_texture(self.id)
        self.id = 0


@dataclass(slots=True)
class TextureCube:
    id: int
    size: tuple[int, int]
    target: int = GL.TEXTURE_CUBE
    resizable: bool = False
    format: int = GL.RGBA
    type: int = GL.UNSIGNED_BYTE
    mipmap: bool = False
    wrap: TextureWrap = "clamp_to_edge"
    min_filter: TextureMinFilter = "linear"
    mag_filter: TextureMagFilter = "linear"

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
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        resolved_min_filter = _resolve_min_filter(
            mipmap=mipmap,
            min_filter=min_filter,
        )

        texture_id = GL.create_texture(GL.TEXTURE_CUBE)

        faces = (
            (GL.CUBE_POSITIVE_X, right),
            (GL.CUBE_NEGATIVE_X, left),
            (GL.CUBE_POSITIVE_Y, top),
            (GL.CUBE_NEGATIVE_Y, bottom),
            (GL.CUBE_POSITIVE_Z, front),
            (GL.CUBE_NEGATIVE_Z, back),
        )

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

            source = image.texture
            if source is None:
                raise RuntimeError(
                    f"Failed to load cubemap face: {path}"
                )

            width, height = source.size

            if width != height:
                raise ValueError(
                    f"Cubemap face must be square: "
                    f"{path} has size {width}x{height}"
                )

            if expected_size is None:
                expected_size = source.size
            elif source.size != expected_size:
                raise ValueError(
                    "All cubemap faces must have the same size. "
                    f"Expected {expected_size}, "
                    f"got {source.size} for {path}"
                )

            GL.tex_image_2d(
                target=target,
                width=width,
                height=height,
                pixels=source.pixels,
                format=GL.RGBA,
                type=GL.UNSIGNED_BYTE,
            )

        configure_texture_cube(
            wrap=wrap,
            min_filter=resolved_min_filter,
            mag_filter=mag_filter,
        )

        if mipmap:
            GL.generate_mipmap(GL.TEXTURE_CUBE)

        GL.unbind_texture(GL.TEXTURE_CUBE)

        if expected_size is None:
            raise RuntimeError(
                "Cubemap creation failed: no faces were uploaded."
            )

        return cls(
            id=texture_id,
            size=expected_size,
            resizable=False,
            format=GL.RGBA,
            type=GL.UNSIGNED_BYTE,
            mipmap=mipmap,
            wrap=wrap,
            min_filter=resolved_min_filter,
            mag_filter=mag_filter,
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
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        if min_filter in MIPMAP_FILTERS:
            raise ValueError(
                "TextureCube.from_rgba() does not generate mipmaps. "
                f"Use a non-mipmap min_filter, got {min_filter!r}."
            )

        texture_id = GL.create_texture(GL.TEXTURE_CUBE)

        faces = (
            (GL.CUBE_POSITIVE_X, right),
            (GL.CUBE_NEGATIVE_X, left),
            (GL.CUBE_POSITIVE_Y, top),
            (GL.CUBE_NEGATIVE_Y, bottom),
            (GL.CUBE_POSITIVE_Z, front),
            (GL.CUBE_NEGATIVE_Z, back),
        )

        for target, rgba in faces:
            GL.tex_image_2d(
                target=target,
                width=1,
                height=1,
                pixels=bytes(rgba),
                format=GL.RGBA,
                type=GL.UNSIGNED_BYTE,
            )

        configure_texture_cube(
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

        GL.unbind_texture(GL.TEXTURE_CUBE)

        return cls(
            id=texture_id,
            size=(1, 1),
            resizable=False,
            format=GL.RGBA,
            type=GL.UNSIGNED_BYTE,
            mipmap=False,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def empty(
        cls,
        size: int | tuple[int, int],
        *,
        resizable: bool = True,
        format: int = GL.RGBA,
        type: int = GL.UNSIGNED_BYTE,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        width, height = normalize_size(size)

        if width != height:
            raise ValueError(
                f"TextureCube size must be square, got {width}x{height}."
            )

        if min_filter in MIPMAP_FILTERS:
            raise ValueError(
                "TextureCube.empty() does not generate mipmaps. "
                f"Use a non-mipmap min_filter, got {min_filter!r}."
            )

        texture_id = GL.create_texture(GL.TEXTURE_CUBE)

        pixels = create_empty_pixels(
            width=width,
            height=height,
            format=format,
            type=type,
        )

        for target in CUBE_FACE_TARGETS:
            GL.tex_image_2d(
                target=target,
                width=width,
                height=height,
                pixels=pixels,
                format=format,
                type=type,
            )

        configure_texture_cube(
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

        GL.unbind_texture(GL.TEXTURE_CUBE)

        return cls(
            id=texture_id,
            size=(width, height),
            resizable=resizable,
            format=format,
            type=type,
            mipmap=False,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    def resize(
        self,
        size: int | tuple[int, int],
        *,
        format: int | None = None,
        type: int | None = None,
    ) -> None:
        if not self.resizable:
            raise RuntimeError(
                "TextureCube is not resizable."
            )

        width, height = normalize_size(size)

        if width != height:
            raise ValueError(
                f"TextureCube size must be square, got {width}x{height}."
            )

        if self.size == (width, height):
            return

        format = self.format if format is None else format
        type = self.type if type is None else type

        GL.bind_texture(
            self.target,
            self.id,
        )

        pixels = create_empty_pixels(
            width=width,
            height=height,
            format=format,
            type=type,
        )

        for target in CUBE_FACE_TARGETS:
            GL.tex_image_2d(
                target=target,
                width=width,
                height=height,
                pixels=pixels,
                format=format,
                type=type,
            )

        configure_texture_cube(
            wrap=self.wrap,
            min_filter=self.min_filter,
            mag_filter=self.mag_filter,
        )

        GL.unbind_texture(self.target)

        self.size = (width, height)
        self.format = format
        self.type = type

    def delete(self) -> None:
        if self.id == 0:
            return

        GL.delete_texture(self.id)
        self.id = 0
