# kivyfn/three/graphics/gl/context.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from array import array
from kivy.graphics.opengl import (
    GL_FALSE,
    GL_CURRENT_PROGRAM,
    glGetUniformLocation,
    glUniformMatrix4fv,
)

from kivy.graphics import InstructionGroup, Callback
from kivy.graphics.context_instructions import ChangeState
from kivyfn.three.graphics.gl.core import GL
from kivyfn.three.math.matrix import Matrix3, Matrix4

if TYPE_CHECKING:
    from kivyfn.three.assets.deformation import Deformation
    from kivyfn.three.assets.material import Material
    from kivyfn.three.graphics.gl.texture import Texture2D, TextureCube


__all__ = (
    "BindUniform",
    "BindTransform",
    "BindGeometry",
    "BindDeformation",
    "BindMaterial",
    "BindObjectId",
    "BindTexture",
)


# =================================== #
# Bind Uniform
# =================================== #


class BindUniform(ChangeState):
    """
    Bind one uniform/state value to the active RenderContext.

    This is the basic per-object context instruction.
    It does not need RenderStage.
    """

    def __init__(
        self,
        name: str,
        value: Any,
        **kwargs: Any,
    ) -> None:
        self.name = name

        super().__init__(
            **{
                name: value,
            },
            **kwargs,
        )

    def sync(
        self,
        value: Any,
    ) -> None:
        self.changes = {
            self.name: value,
        }

        self.flag_data_update()


class BindMatrix4ArrayCallback(Callback):
    def __init__(
        self,
        *,
        uniform: str,
        data: array,
        count: int,
        **kwargs: Any,
    ) -> None:
        self.uniform = uniform
        self.data = data
        self.count = count

        super().__init__(
            self.apply,
            **kwargs,
        )

    def sync(
        self,
        *,
        data: array,
        count: int,
    ) -> None:
        self.data = data
        self.count = count
        self.ask_update()

    def apply(
        self,
        *_: Any,
    ) -> None:
        if self.count <= 0:
            return

        program = GL.get_int(
            GL_CURRENT_PROGRAM,
        )

        if program == 0:
            return

        location = glGetUniformLocation(
            program,
            self.uniform.encode("utf-8"),
        )

        if location < 0:
            return

        glUniformMatrix4fv(
            location,
            self.count,
            GL_FALSE,
            self.data.tobytes(),
        )


class BindMatrix4Array(InstructionGroup):
    def __init__(
        self,
        *,
        uniform: str,
        data: array,
        count: int,
    ) -> None:
        super().__init__()

        self.uniform = uniform

        self.bind_callback = BindMatrix4ArrayCallback(
            uniform=uniform,
            data=data,
            count=count,
        )

        self.add(
            self.bind_callback,
        )

    def sync(
        self,
        *,
        data: array,
        count: int,
    ) -> None:
        self.bind_callback.sync(
            data=data,
            count=count,
        )


# =================================== #
# Bind Deformation
# =================================== #

class BindDeformation(InstructionGroup):

    def __init__(
        self,
        *,
        deformation: Deformation,
    ) -> None:
        super().__init__()

        self.use_morphing = BindUniform(
            "use_morphing",
            self._encode_bool(deformation.has_morph_weights),
        )

        self.use_skinning = BindUniform(
            "use_skinning",
            self._encode_bool(deformation.has_skin),
        )

        self.morph_weights = BindUniform(
            "morph_weights",
            list(deformation.morph_weights),
        )

        self.joint_matrices = BindMatrix4Array(
            uniform="joint_matrices",
            data=deformation.joint_uniform_data,
            count=deformation.joint_count,
        )

        self.add(self.use_morphing)
        self.add(self.use_skinning)
        self.add(self.morph_weights)
        self.add(self.joint_matrices)

    @staticmethod
    def _encode_bool(
        value: bool,
    ) -> int:
        return 1 if value else 0

    def sync(
        self,
        *,
        deformation: Deformation,
    ) -> None:
        self.use_morphing.sync(
            self._encode_bool(deformation.has_morph_weights),
        )

        self.use_skinning.sync(
            self._encode_bool(deformation.has_skin),
        )

        self.morph_weights.sync(
            list(deformation.morph_weights),
        )

        self.joint_matrices.sync(
            data=deformation.joint_uniform_data,
            count=deformation.joint_count,
        )


# =================================== #
# Bind Transform
# =================================== #


class BindTransform(InstructionGroup):
    def __init__(
        self,
        *,
        model_mat: Matrix4 | None = None,
        normal_mat: Matrix3 | None = None,
    ) -> None:
        super().__init__()

        self.model_mat = BindUniform(
            "model_mat",
            (model_mat or Matrix4.identity()).to_uniform(),
        )

        self.normal_mat = BindUniform(
            "normal_mat",
            (normal_mat or Matrix3.identity()).to_uniform(),
        )

        self.add(self.model_mat)
        self.add(self.normal_mat)

    def sync(
        self,
        *,
        model_mat: Matrix4,
        normal_mat: Matrix3,
    ) -> None:
        self.model_mat.sync(
            model_mat.to_uniform(),
        )

        self.normal_mat.sync(
            normal_mat.to_uniform(),
        )




# =================================== #
# Bind Geometry
# =================================== #


class BindGeometry(InstructionGroup):
    def __init__(
        self,
        *,
        use_tangents: bool,
        use_skinning: bool,
        use_colors: bool,
    ) -> None:
        super().__init__()

        self.use_tangents = BindUniform(
            "use_tangents",
            self._encode_bool(use_tangents),
        )

        self.use_skinning = BindUniform(
            "use_skinning",
            self._encode_bool(use_skinning),
        )

        self.use_colors = BindUniform(
            "use_colors",
            self._encode_bool(use_colors),
        )

        self.add(self.use_tangents)
        self.add(self.use_skinning)
        self.add(self.use_colors)

    @staticmethod
    def _encode_bool(
        value: bool,
    ) -> int:
        return 1 if value else 0

    def sync(
        self,
        *,
        use_tangents: bool,
        use_skinning: bool,
        use_colors: bool,
    ) -> None:
        self.use_tangents.sync(
            self._encode_bool(use_tangents),
        )

        self.use_skinning.sync(
            self._encode_bool(use_skinning),
        )

        self.use_colors.sync(
            self._encode_bool(use_colors),
        )


# =================================== #
# Bind Material
# =================================== #


class BindMaterial(InstructionGroup):
    def __init__(
        self,
        *,
        material: Material,
    ) -> None:
        super().__init__()

        self.material = material
        self.uniforms: dict[str, BindUniform] = {}

        self.sync(
            material=material,
        )

    def sync(
        self,
        *,
        material: Material | None = None,
    ) -> None:
        if material is not None:
            self.material = material

        wanted = {
            name: value
            for name, value in self.material.uniforms.items()
            if value is not None
        }

        for name in list(self.uniforms):
            if name not in wanted:
                uniform = self.uniforms.pop(name)
                self.remove(uniform)

        for name, value in wanted.items():
            uniform = self.uniforms.get(name)

            if uniform is None:
                uniform = BindUniform(
                    name,
                    value,
                )

                self.uniforms[name] = uniform
                self.add(uniform)

                continue

            uniform.sync(value)

    def set_material(
        self,
        material: Material,
    ) -> None:
        self.sync(
            material=material,
        )


# =================================== #
# Bind Object ID
# =================================== #


class BindObjectId(InstructionGroup):
    def __init__(
        self,
        *,
        render_id: int,
        uniform: str,
    ) -> None:
        super().__init__()

        self.render_id = render_id
        self.uniform = uniform

        self.state = BindUniform(
            uniform,
            self.encode(render_id),
        )

        self.add(self.state)

    @staticmethod
    def encode(
        render_id: int,
    ) -> list[float]:
        r = (render_id >> 16) & 0xFF
        g = (render_id >> 8) & 0xFF
        b = render_id & 0xFF

        return [
            r / 255.0,
            g / 255.0,
            b / 255.0,
            1.0,
        ]

    def sync(
        self,
        *,
        render_id: int | None = None,
    ) -> None:
        if render_id is not None:
            self.render_id = render_id

        self.state.sync(
            self.encode(self.render_id),
        )


# =================================== #
# Bind Texture
# =================================== #

class BindTextureCallback(Callback):
    def __init__(
        self,
        *,
        texture: Texture2D | TextureCube,
        slot: int,
        **kwargs: Any,
    ) -> None:
        self.texture = texture
        self.slot = int(slot)

        super().__init__(
            self.apply,
            **kwargs,
        )

    def sync(
        self,
        *,
        texture: Texture2D | TextureCube | None = None,
        slot: int | None = None,
    ) -> None:
        if texture is not None:
            self.texture = texture

        if slot is not None:
            self.slot = int(slot)

        self.ask_update()

    def apply(
        self,
        *_: Any,
    ) -> None:
        self.texture.bind_to(
            self.slot,
        )

        GL.active_texture(
            0,
        )


class BindTexture(InstructionGroup):
    def __init__(
        self,
        *,
        uniform: str,
        texture: Texture2D | TextureCube,
        slot: int,
    ) -> None:
        super().__init__()

        self.uniform = uniform

        self.bind_callback = BindTextureCallback(
            texture=texture,
            slot=slot,
        )

        self.sampler = BindUniform(
            uniform,
            int(slot),
        )

        self.add(
            self.bind_callback,
        )

        self.add(
            self.sampler,
        )

    @property
    def texture(
        self,
    ) -> Texture2D | TextureCube:
        return self.bind_callback.texture

    @texture.setter
    def texture(
        self,
        texture: Texture2D | TextureCube,
    ) -> None:
        self.bind_callback.sync(
            texture=texture,
        )

    @property
    def slot(
        self,
    ) -> int:
        return self.bind_callback.slot

    @slot.setter
    def slot(
        self,
        slot: int,
    ) -> None:
        slot = int(slot)

        self.bind_callback.sync(
            slot=slot,
        )

        self.sampler.sync(
            slot,
        )

    def sync(
        self,
        *,
        texture: Texture2D | TextureCube | None = None,
        slot: int | None = None,
    ) -> None:
        if texture is not None:
            self.texture = texture

        if slot is not None:
            self.slot = slot



