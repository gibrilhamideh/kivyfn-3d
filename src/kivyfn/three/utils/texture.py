from kivy.graphics.texture import Texture

def create_texture(
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
