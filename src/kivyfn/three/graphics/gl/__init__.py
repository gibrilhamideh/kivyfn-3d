# kivyfn/three/graphics/gl/__init__.py

from kivyfn.three.graphics.gl.core import GL
from kivyfn.three.graphics.gl.texture import (
    Rgba,
    Texture2D,
    TextureCube,
)

from kivyfn.three.graphics.gl.context import (
    BindTexture,
    BindGeometry,
    BindMaterial,
    BindObjectId,
    BindTransform,
    BindUniform
)


from kivyfn.three.graphics.gl.targets import (
    ScreenTarget,
    Texture2DTarget,
    TextureCubeTarget,
)

from kivyfn.three.graphics.gl.utils import (
    normalize_size,
)

__all__ = (
    # Core
    "GL",

    # Utils
    "normalize_size",

    # Bind
    "BindTexture",
    "BindTransform",
    "BindObjectId",
    "BindObjectId",
    "BindMaterial",
    "BindGeometry",
    "BindUniform",

    # Textures
    "Rgba",
    "Texture2D",
    "TextureCube",

    # Targets
    "ScreenTarget",
    "Texture2DTarget",
    "TextureCubeTarget",
)
