# kivyfn/three/images/loader.py

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image as PillowImage
from PIL import ImageOps

from kivyfn.three.images.image import Image


class ImageLoader:
    @staticmethod
    def from_source(
        path: str | Path,
        *,
        flip_vertical: bool = False,
    ) -> Image:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Image source does not exist: {path}"
            )

        with PillowImage.open(path) as image:
            return ImageLoader.from_pillow(
                image,
                flip_vertical=flip_vertical,
            )

    @staticmethod
    def from_bytes(
        data: bytes,
        *,
        flip_vertical: bool = False,
    ) -> Image:
        with PillowImage.open(BytesIO(data)) as image:
            return ImageLoader.from_pillow(
                image,
                flip_vertical=flip_vertical,
            )

    @staticmethod
    def from_pillow(
        image: PillowImage.Image,
        *,
        flip_vertical: bool = False,
    ) -> Image:
        image = ImageOps.exif_transpose(
            image,
        )

        image = image.convert(
            "RGBA",
        )

        if flip_vertical:
            image = ImageOps.flip(
                image,
            )

        width, height = image.size

        return Image(
            width=width,
            height=height,
            pixels=image.tobytes(),
            channels=4,
        )
