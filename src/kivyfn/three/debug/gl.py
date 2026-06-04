
from kivy.graphics.opengl import (
        glGetIntegerv,
        GL_MAX_TEXTURE_IMAGE_UNITS,
        GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS,
)

def get_max_fragment_texture_units() -> int:
    value = glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS)
    return value[0]


def get_max_combined_texture_units() -> int:
    value = glGetIntegerv(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS)
    return value[0]
